"""Build or validate Red-Govern's deterministic Skill archive."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0a3"
ARCHIVE_NAME = f"red-govern-{VERSION}.zip"
SHA_NAME = f"red-govern-{VERSION}.sha256"

DIST_ROOT = ROOT / "agent-skills" / "dist"
ARCHIVE_PATH = DIST_ROOT / ARCHIVE_NAME
SHA_PATH = DIST_ROOT / SHA_NAME
EXTERNAL_MANIFEST_PATH = DIST_ROOT / "manifest.json"

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = 0o100644

SOURCE_FILES = {
    "red-govern/SKILL.md": (
        ROOT / "agent-skills" / "red-govern" / "SKILL.md"
    ),
    "red-govern/references/agent-integration-contract.md": (
        ROOT
        / "agent-skills"
        / "red-govern"
        / "references"
        / "agent-integration-contract.md"
    ),
    "red-govern/references/problem-command-map.json": (
        ROOT
        / "agent-skills"
        / "red-govern"
        / "references"
        / "problem-command-map.json"
    ),
    "red-govern/references/problem-command-map.schema.json": (
        ROOT
        / "agent-skills"
        / "red-govern"
        / "references"
        / "problem-command-map.schema.json"
    ),
    "red-govern/references/recommendation-boundaries.md": (
        ROOT
        / "agent-skills"
        / "red-govern"
        / "references"
        / "recommendation-boundaries.md"
    ),
    "red-govern/README.md": (
        ROOT / "agent-skills" / "distribution" / "README.md"
    ),
    "red-govern/LICENSE.md": ROOT / "LICENSE.md",
    "red-govern/COMMERCIAL_LICENSE.md": ROOT / "COMMERCIAL_LICENSE.md",
    "red-govern/NOTICE": ROOT / "NOTICE",
    "red-govern/TRADEMARKS.md": ROOT / "TRADEMARKS.md",
}

LEGAL_ARCHIVE_PATHS = [
    "red-govern/LICENSE.md",
    "red-govern/COMMERCIAL_LICENSE.md",
    "red-govern/NOTICE",
    "red-govern/TRADEMARKS.md",
]


def fail(message: str) -> NoReturn:
    """Raise a stable distribution failure."""
    raise RuntimeError(message)


def digest_bytes(data: bytes) -> str:
    """Return a SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: Any) -> bytes:
    """Serialise stable UTF-8 JSON."""
    return (
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")


def source_entries() -> list[dict[str, Any]]:
    """Read and hash every archive source file."""
    entries: list[dict[str, Any]] = []

    for archive_path, source_path in sorted(SOURCE_FILES.items()):
        if not source_path.is_file():
            fail(f"Distribution source is missing: {source_path}")

        data = source_path.read_bytes()
        entries.append(
            {
                "path": archive_path,
                "source": source_path.relative_to(ROOT).as_posix(),
                "sha256": digest_bytes(data),
                "size": len(data),
                "data": data,
            }
        )

    return entries


def internal_manifest(entries: list[dict[str, Any]]) -> bytes:
    """Create the manifest stored inside the archive."""
    return canonical_json(
        {
            "schema_version": "1.0",
            "package_version": VERSION,
            "bundle_name": "red-govern",
            "archive_format": "zip",
            "deterministic": True,
            "files": [
                {
                    "path": entry["path"],
                    "sha256": entry["sha256"],
                    "size": entry["size"],
                }
                for entry in entries
            ],
            "legal_files": LEGAL_ARCHIVE_PATHS,
        }
    )


def zip_info(name: str) -> zipfile.ZipInfo:
    """Create one deterministic ZIP entry."""
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = ZIP_MODE << 16
    info.internal_attr = 0
    info.extra = b""
    info.comment = b""
    return info


def build_archive() -> tuple[bytes, dict[str, Any], str]:
    """Build archive bytes, manifest, and checksum line."""
    entries = source_entries()
    internal = internal_manifest(entries)
    archive_entries = [
        (str(entry["path"]), bytes(entry["data"]))
        for entry in entries
    ]
    archive_entries.append(("red-govern/MANIFEST.json", internal))
    archive_entries.sort(key=lambda item: item[0])

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
    ) as archive:
        archive.comment = b""

        for name, data in archive_entries:
            archive.writestr(zip_info(name), data)

    archive_bytes = buffer.getvalue()
    archive_sha = digest_bytes(archive_bytes)
    contents = [
        {
            "path": name,
            "sha256": digest_bytes(data),
            "size": len(data),
        }
        for name, data in archive_entries
    ]

    external_manifest = {
        "schema_version": "1.0",
        "package_version": VERSION,
        "artifact": ARCHIVE_NAME,
        "sha256": archive_sha,
        "size": len(archive_bytes),
        "format": "zip",
        "compression": "stored",
        "deterministic": True,
        "entry_timestamp": "1980-01-01T00:00:00Z",
        "entry_mode": "0644",
        "contents": contents,
        "legal_files": LEGAL_ARCHIVE_PATHS,
        "validation": (
            "python scripts/build_agent_skill_distribution.py --check"
        ),
    }
    checksum_line = f"{archive_sha}  {ARCHIVE_NAME}\n"
    return archive_bytes, external_manifest, checksum_line


def validate_archive_structure(
    archive_bytes: bytes,
    manifest: dict[str, Any],
) -> None:
    """Validate ZIP entries, timestamps, modes, digests, and paths."""
    expected = {
        str(item["path"]): item
        for item in manifest["contents"]
    }

    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]

        if names != sorted(expected):
            fail("Archive entries are not sorted or complete.")

        if len(names) != len(set(names)):
            fail("Archive contains duplicate entries.")

        for info in infos:
            if info.is_dir():
                fail(f"Archive contains a directory entry: {info.filename}")

            path = Path(info.filename)

            if path.is_absolute() or ".." in path.parts:
                fail(f"Archive contains an unsafe path: {info.filename}")

            if info.date_time != ZIP_TIMESTAMP:
                fail(f"Archive timestamp drift: {info.filename}")

            if info.compress_type != zipfile.ZIP_STORED:
                fail(f"Archive compression drift: {info.filename}")

            mode = (info.external_attr >> 16) & 0o777777

            if mode != ZIP_MODE:
                fail(
                    f"Archive mode drift: {info.filename} "
                    f"{oct(mode)}"
                )

            data = archive.read(info.filename)
            expected_item = expected[info.filename]

            if digest_bytes(data) != expected_item["sha256"]:
                fail(f"Archive digest mismatch: {info.filename}")

            if len(data) != expected_item["size"]:
                fail(f"Archive size mismatch: {info.filename}")


def write_outputs() -> dict[str, Any]:
    """Write the deterministic archive and metadata."""
    archive_bytes, manifest, checksum_line = build_archive()
    validate_archive_structure(archive_bytes, manifest)

    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PATH.write_bytes(archive_bytes)
    SHA_PATH.write_text(checksum_line, encoding="utf-8")
    EXTERNAL_MANIFEST_PATH.write_bytes(canonical_json(manifest))
    return manifest


def check_outputs() -> dict[str, Any]:
    """Rebuild and compare every tracked output byte-for-byte."""
    for path in (ARCHIVE_PATH, SHA_PATH, EXTERNAL_MANIFEST_PATH):
        if not path.is_file():
            fail(f"Tracked distribution output is missing: {path}")

    archive_bytes, manifest, checksum_line = build_archive()
    expected_manifest = canonical_json(manifest)

    if ARCHIVE_PATH.read_bytes() != archive_bytes:
        fail("Tracked Skill archive is not reproducible.")

    if SHA_PATH.read_text(encoding="utf-8") != checksum_line:
        fail("Tracked Skill checksum file differs.")

    if EXTERNAL_MANIFEST_PATH.read_bytes() != expected_manifest:
        fail("Tracked Skill manifest differs.")

    validate_archive_structure(archive_bytes, manifest)

    if digest_bytes(archive_bytes) != manifest["sha256"]:
        fail("Archive digest differs from the external manifest.")

    return manifest


def main() -> int:
    """Build or check the deterministic Skill archive."""
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()

    manifest = write_outputs() if arguments.write else check_outputs()

    print("Skill archive:", manifest["artifact"])
    print("Package version:", manifest["package_version"])
    print("Archive SHA-256:", manifest["sha256"])
    print("Archive size:", manifest["size"])
    print("Archive entries:", len(manifest["contents"]))
    print("Legal files:", len(manifest["legal_files"]))
    print("Compression:", manifest["compression"])
    print("Deterministic Skill distribution validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
