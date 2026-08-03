"""Secure local-file preparation for Red-Govern."""

from __future__ import annotations

import os
from pathlib import Path

PRIVATE_FILE_MODE = 0o600


def prepare_private_file(path: Path) -> Path:
    """Create or tighten a local file using owner-only permissions."""
    private_path = path.expanduser().resolve()

    private_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        descriptor = os.open(
            private_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            PRIVATE_FILE_MODE,
        )
    except FileExistsError:
        if not private_path.is_file():
            raise OSError(f"Private-file destination is not a file: {private_path}") from None

        private_path.chmod(PRIVATE_FILE_MODE)
    else:
        os.close(descriptor)

    return private_path
