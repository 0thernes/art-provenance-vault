"""Shared pytest fixtures for Art Provenance Vault tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure src/ is importable without installing the package.
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    """A temporary vault root with a git repo and manifests/ directory."""
    manifest_dir = tmp_path / "vault" / "manifests"
    manifest_dir.mkdir(parents=True)
    # Init a bare-enough git repo so provenance.py can commit.
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=str(tmp_path), check=True, capture_output=True,
    )
    return tmp_path
