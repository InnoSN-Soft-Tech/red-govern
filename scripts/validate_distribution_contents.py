"""Validate Red-Govern wheel and source-distribution contents."""

from __future__ import annotations

import argparse
import sys
import tarfile
import zipfile
from email.message import Message
from email.parser import Parser
from pathlib import Path
from typing import NoReturn

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]


EXPECTED_LICENSE_EXPRESSION = "LicenseRef-PolyForm-Perimeter-1.0.1"
EXPECTED_METADATA_VERSION = "2.4"


def fail(message: str) -> NoReturn:
    """Raise a validation error with a stable message."""
    raise RuntimeError(message)


def read_project_metadata(project_root: Path) -> tuple[str, str, list[str]]:
    """Read package name, version, and declared legal files."""
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.is_file():
        fail(f"pyproject.toml is missing: {pyproject_path}")

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project")

    if not isinstance(project, dict):
        fail("[project] metadata is missing.")

    name = project.get("name")
    version = project.get("version")
    license_files = project.get("license-files")

    if not isinstance(name, str) or not name:
        fail("Project name is missing.")

    if not isinstance(version, str) or not version:
        fail("Project version is missing.")

    if not isinstance(license_files, list) or not all(
        isinstance(item, str) and item
        for item in license_files
    ):
        fail("project.license-files is invalid.")

    if len(license_files) != len(set(license_files)):
        fail("project.license-files contains duplicates.")

    return name, version, license_files


def select_distributions(dist_dir: Path) -> tuple[Path, Path]:
    """Select exactly one wheel and one source distribution."""
    if not dist_dir.is_dir():
        fail(f"Distribution directory is missing: {dist_dir}")

    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    files = sorted(path for path in dist_dir.iterdir() if path.is_file())

    if len(files) != 2:
        fail(
            "Expected exactly two distribution files, "
            f"found {len(files)}: {[path.name for path in files]}"
        )

    if len(wheels) != 1:
        fail(f"Expected exactly one wheel, found {len(wheels)}.")

    if len(sdists) != 1:
        fail(f"Expected exactly one source distribution, found {len(sdists)}.")

    return wheels[0], sdists[0]


def parse_metadata(text: str, source: str) -> Message:
    """Parse and validate core metadata fields."""
    metadata = Parser().parsestr(text)

    if metadata.get("Metadata-Version") != EXPECTED_METADATA_VERSION:
        fail(
            f"{source}: expected Metadata-Version "
            f"{EXPECTED_METADATA_VERSION}, got "
            f"{metadata.get('Metadata-Version')!r}."
        )

    if metadata.get("License-Expression") != EXPECTED_LICENSE_EXPRESSION:
        fail(
            f"{source}: expected License-Expression "
            f"{EXPECTED_LICENSE_EXPRESSION!r}, got "
            f"{metadata.get('License-Expression')!r}."
        )

    return metadata


def validate_license_metadata(
    metadata: Message,
    expected_files: list[str],
    source: str,
) -> list[str]:
    """Validate the exact License-File set without assuming declaration order."""
    actual = metadata.get_all("License-File") or []

    if len(actual) != len(set(actual)):
        fail(f"{source}: License-File metadata contains duplicates: {actual}")

    if set(actual) != set(expected_files):
        fail(
            f"{source}: License-File metadata differs. "
            f"Expected {sorted(expected_files)}, got {sorted(actual)}."
        )

    return actual


def validate_sdist(
    sdist_path: Path,
    normalized_name: str,
    version: str,
    expected_files: list[str],
) -> list[str]:
    """Validate legal files and PKG-INFO in the source distribution."""
    root = f"{normalized_name}-{version}/"

    with tarfile.open(sdist_path, mode="r:gz") as archive:
        members = {
            member.name
            for member in archive.getmembers()
            if member.isfile()
        }

        missing = [
            name
            for name in expected_files
            if root + name not in members
        ]

        if missing:
            fail(f"sdist: missing declared legal files: {missing}")

        pkg_info_name = root + "PKG-INFO"

        if pkg_info_name not in members:
            fail(f"sdist: PKG-INFO is missing: {pkg_info_name}")

        extracted = archive.extractfile(pkg_info_name)

        if extracted is None:
            fail("sdist: PKG-INFO could not be read.")

        metadata_text = extracted.read().decode("utf-8")

    metadata = parse_metadata(metadata_text, "sdist PKG-INFO")
    return validate_license_metadata(
        metadata,
        expected_files,
        "sdist PKG-INFO",
    )


def validate_wheel(
    wheel_path: Path,
    expected_files: list[str],
) -> list[str]:
    """Validate legal files and METADATA in the wheel."""
    with zipfile.ZipFile(wheel_path) as archive:
        members = set(archive.namelist())
        metadata_names = sorted(
            name
            for name in members
            if name.endswith(".dist-info/METADATA")
        )

        if len(metadata_names) != 1:
            fail(
                "wheel: expected exactly one METADATA file, "
                f"found {len(metadata_names)}."
            )

        missing = [
            name
            for name in expected_files
            if not any(
                member.endswith(f".dist-info/licenses/{name}")
                for member in members
            )
        ]

        if missing:
            fail(f"wheel: missing declared legal files: {missing}")

        metadata_text = archive.read(metadata_names[0]).decode("utf-8")

    metadata = parse_metadata(metadata_text, "wheel METADATA")
    return validate_license_metadata(
        metadata,
        expected_files,
        "wheel METADATA",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate Red-Govern wheel and source-distribution "
            "licensing contents and metadata."
        )
    )
    parser.add_argument(
        "dist_dir",
        type=Path,
        help="Directory containing exactly one wheel and one .tar.gz sdist.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing pyproject.toml. Defaults to cwd.",
    )
    return parser.parse_args()


def main() -> int:
    """Run distribution-content validation."""
    args = parse_args()
    project_root = args.project_root.resolve()
    dist_dir = args.dist_dir.resolve()

    name, version, expected_files = read_project_metadata(project_root)
    normalized_name = name.replace("-", "_")

    wheel_path, sdist_path = select_distributions(dist_dir)

    expected_wheel_prefix = f"{normalized_name}-{version}-"
    expected_sdist_name = f"{normalized_name}-{version}.tar.gz"

    if not wheel_path.name.startswith(expected_wheel_prefix):
        fail(
            "Wheel filename does not match project name/version: "
            f"{wheel_path.name}"
        )

    if sdist_path.name != expected_sdist_name:
        fail(
            "Source-distribution filename does not match project "
            f"name/version: {sdist_path.name}"
        )

    sdist_license_order = validate_sdist(
        sdist_path,
        normalized_name,
        version,
        expected_files,
    )
    wheel_license_order = validate_wheel(
        wheel_path,
        expected_files,
    )

    if sdist_license_order != wheel_license_order:
        fail(
            "sdist and wheel License-File ordering differs: "
            f"{sdist_license_order!r} != {wheel_license_order!r}"
        )

    print(f"Validated wheel: {wheel_path.name}")
    print(f"Validated sdist: {sdist_path.name}")
    print(f"Metadata-Version: {EXPECTED_METADATA_VERSION}")
    print(f"License-Expression: {EXPECTED_LICENSE_EXPRESSION}")
    print(f"License-File entries: {sdist_license_order}")
    print("Distribution-content validation passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
