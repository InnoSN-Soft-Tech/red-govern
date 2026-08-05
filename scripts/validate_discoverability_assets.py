"""Validate Red-Govern's public discoverability and social metadata assets."""

from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any, NoReturn, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]
LLMS_PATH = ROOT / "docs" / "llms.txt"
SOCIAL_IMAGE_PATH = ROOT / "docs" / "assets" / "red-govern-social-card.png"
OVERRIDE_PATH = ROOT / "overrides" / "main.html"
MKDOCS_PATH = ROOT / "mkdocs.yml"
README_PATH = ROOT / "README.md"
DOCS_INDEX_PATH = ROOT / "docs" / "index.md"
MAP_PATH = ROOT / "docs" / "problems" / "problem-command-map.json"

EXPECTED_VERSION = "0.1.0a3"
EXPECTED_IMAGE_SHA256 = "2eaf486380e934d40bfdc5fc07022d22ea4ccb20a71fe2557d1deda2c96bf288"
EXPECTED_IMAGE_SIZE = (1200, 630)

REQUIRED_LLMS_URLS = {
    "https://innosn-soft-tech.github.io/red-govern/",
    "https://innosn-soft-tech.github.io/red-govern/installation/",
    "https://innosn-soft-tech.github.io/red-govern/quick-start/",
    "https://innosn-soft-tech.github.io/red-govern/configuration/",
    "https://innosn-soft-tech.github.io/red-govern/problems/",
    (
        "https://innosn-soft-tech.github.io/red-govern/problems/"
        "recommendation-boundaries/"
    ),
    (
        "https://innosn-soft-tech.github.io/red-govern/problems/"
        "agent-integration-contract/"
    ),
    (
        "https://innosn-soft-tech.github.io/red-govern/problems/"
        "problem-command-map.json"
    ),
    (
        "https://innosn-soft-tech.github.io/red-govern/problems/"
        "problem-command-map.schema.json"
    ),
    "https://pypi.org/project/red-govern/",
    "https://github.com/InnoSN-Soft-Tech/red-govern",
}

REQUIRED_META_MARKERS = {
    'name="robots"',
    'rel="alternate"',
    'type="text/markdown"',
    'property="og:type"',
    'property="og:site_name"',
    'property="og:title"',
    'property="og:description"',
    'property="og:url"',
    'property="og:image"',
    'property="og:image:width"',
    'property="og:image:height"',
    'property="og:image:alt"',
    'name="twitter:card"',
    'name="twitter:title"',
    'name="twitter:description"',
    'name="twitter:image"',
    'name="twitter:image:alt"',
    'type="application/ld+json"',
}

REQUIRED_JSON_LD_KEYS = {
    "@context",
    "@type",
    "name",
    "alternateName",
    "description",
    "applicationCategory",
    "applicationSubCategory",
    "operatingSystem",
    "softwareVersion",
    "softwareRequirements",
    "url",
    "downloadUrl",
    "installUrl",
    "image",
    "isAccessibleForFree",
    "license",
    "sameAs",
    "featureList",
    "publisher",
}


def fail(message: str) -> NoReturn:
    """Raise a discoverability validation error."""
    raise RuntimeError(message)


def normalize_text(value: str) -> str:
    """Collapse formatting whitespace for semantic text checks."""
    return " ".join(value.split())


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(parsed, dict):
        fail(f"Expected a JSON object: {path}")

    return cast(dict[str, Any], parsed)


def read_png_size(path: Path) -> tuple[int, int]:
    """Read PNG dimensions from the IHDR chunk."""
    data = path.read_bytes()

    if len(data) < 24:
        fail("Social image is too small to be a PNG.")

    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail("Social image does not have a PNG signature.")

    if data[12:16] != b"IHDR":
        fail("Social image does not begin with an IHDR chunk.")

    return struct.unpack(">II", data[16:24])


def main() -> int:
    """Validate source discoverability assets."""
    for path in (
        LLMS_PATH,
        SOCIAL_IMAGE_PATH,
        OVERRIDE_PATH,
        MKDOCS_PATH,
        README_PATH,
        DOCS_INDEX_PATH,
        MAP_PATH,
    ):
        if not path.is_file():
            fail(f"Required discoverability file is missing: {path}")

    mkdocs_raw = yaml.safe_load(MKDOCS_PATH.read_text(encoding="utf-8"))

    if not isinstance(mkdocs_raw, dict):
        fail("mkdocs.yml must contain a mapping.")

    theme = mkdocs_raw.get("theme")

    if not isinstance(theme, dict):
        fail("mkdocs.yml theme must be a mapping.")

    if theme.get("custom_dir") != "overrides":
        fail("MkDocs custom_dir must be overrides.")

    if mkdocs_raw.get("site_url") not in {
        "https://InnoSN-Soft-Tech.github.io/red-govern",
        "https://innosn-soft-tech.github.io/red-govern",
    }:
        fail("MkDocs site_url is unexpected.")

    mapping = load_json_object(MAP_PATH)

    if mapping.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Problem map version is unexpected.")

    llms = LLMS_PATH.read_text(encoding="utf-8")
    normalized_llms = normalize_text(llms)

    if not llms.startswith("# Red-Govern\n\n> "):
        fail("llms.txt must begin with the required H1 and blockquote.")

    for heading in (
        "## Start here",
        "## Problem and capability guidance",
        "## Redshift operation and trust",
        "## Package and source",
        "## Optional",
    ):
        if heading not in llms:
            fail(f"llms.txt omits heading: {heading}")

    missing_urls = {
        url for url in REQUIRED_LLMS_URLS if url not in llms
    }

    if missing_urls:
        fail(f"llms.txt omits URLs: {sorted(missing_urls)}")

    for required_text in (
        EXPECTED_VERSION,
        "does not perform destructive remediation",
        "does not prove that an object is safe to delete",
        "must not be used to collect passwords",
    ):
        if normalize_text(required_text) not in normalized_llms:
            fail(f"llms.txt omits boundary: {required_text}")

    override = OVERRIDE_PATH.read_text(encoding="utf-8")

    missing_markers = {
        marker
        for marker in REQUIRED_META_MARKERS
        if marker not in override
    }

    if missing_markers:
        fail(
            "Social/template metadata markers are missing: "
            f"{sorted(missing_markers)}"
        )

    script_match = re.search(
        (
            r'<script\s+type="application/ld\+json">\s*'
            r"(?P<body>\{.*?\})\s*</script>"
        ),
        override,
        flags=re.DOTALL,
    )

    if script_match is None:
        fail("JSON-LD SoftwareApplication block was not found.")

    structured = json.loads(script_match.group("body"))
    missing_keys = REQUIRED_JSON_LD_KEYS - set(structured)

    if missing_keys:
        fail(f"JSON-LD omits keys: {sorted(missing_keys)}")

    if structured.get("@context") != "https://schema.org":
        fail("JSON-LD context is unexpected.")

    if structured.get("@type") != "SoftwareApplication":
        fail("JSON-LD type is unexpected.")

    if structured.get("name") != "Red-Govern":
        fail("JSON-LD name is unexpected.")

    if structured.get("softwareVersion") != EXPECTED_VERSION:
        fail("JSON-LD software version is unexpected.")

    if structured.get("applicationCategory") != "DeveloperApplication":
        fail("JSON-LD application category is unexpected.")

    if structured.get("isAccessibleForFree") is not True:
        fail("JSON-LD accessibility flag is unexpected.")

    publisher = structured.get("publisher")

    if not isinstance(publisher, dict):
        fail("JSON-LD publisher must be an object.")

    if publisher.get("name") != "InnoSN Soft Tech":
        fail("JSON-LD publisher is unexpected.")

    if read_png_size(SOCIAL_IMAGE_PATH) != EXPECTED_IMAGE_SIZE:
        fail("Social image dimensions are unexpected.")

    image_digest = hashlib.sha256(
        SOCIAL_IMAGE_PATH.read_bytes()
    ).hexdigest()

    if image_digest != EXPECTED_IMAGE_SHA256:
        fail("Social image SHA-256 is unexpected.")

    readme = README_PATH.read_text(encoding="utf-8")

    if (
        "https://innosn-soft-tech.github.io/red-govern/llms.txt"
        not in readme
    ):
        fail("README does not link the public llms.txt file.")

    docs_index = DOCS_INDEX_PATH.read_text(encoding="utf-8")

    if f"The current release is `{EXPECTED_VERSION}`." not in docs_index:
        fail("Documentation homepage release version is stale.")

    for required in (
        "[AI-readable documentation index](llms.txt)",
        "[Problem taxonomy](problems/index.md)",
        (
            "[Agent integration contract]"
            "(problems/agent-integration-contract.md)"
        ),
    ):
        if required not in docs_index:
            fail(f"Documentation homepage omits link: {required}")

    print(f"Validated llms.txt: {LLMS_PATH}")
    print("llms.txt format and links: passed")
    print("JSON-LD SoftwareApplication: passed")
    print("Open Graph metadata: passed")
    print("Twitter card metadata: passed")
    print(
        "Social image:",
        f"{EXPECTED_IMAGE_SIZE[0]}x{EXPECTED_IMAGE_SIZE[1]}",
    )
    print("Social image SHA-256:", image_digest)
    print("Documentation release version:", EXPECTED_VERSION)
    print("Discoverability-asset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
