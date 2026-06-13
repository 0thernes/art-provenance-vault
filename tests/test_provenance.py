"""Tests for src/provenance.py — register/verify happy path, verify-chain tamper localization."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import provenance  # noqa: E402
from provenance import canonical, cmd_anchor, cmd_verify_chain  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_manifest(manifest_dir: Path, m: dict) -> Path:
    """Write a manifest dict into manifest_dir/<asset.sha256>.json.

    Matches the naming convention of cmd_register: the filename is the
    asset's sha256, not the canonical-manifest hash.  The canonical-manifest
    hash is used separately for chain.prev linkage.
    """
    asset_sha = m["asset"]["sha256"]
    path = manifest_dir / f"{asset_sha}.json"
    path.write_text(json.dumps(m, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _make_manifest(
    asset_sha: str,
    creator_id: str,
    prev: str | None,
    seq: int,
) -> dict:
    return {
        "manifest_version": "0.1.0",
        "asset": {"sha256": asset_sha, "byte_size": 1, "filename": "x.bin",
                  "media_type": "application/octet-stream"},
        "creator": {"id": creator_id, "name": "Test"},
        "creation": {"method": "human"},
        "license": {"spdx": "CC0-1.0"},
        "registered_at": "2026-06-12T00:00:00+00:00",
        "chain": {"prev": prev, "sequence": seq},
    }


def _fake_sha(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _args(**kwargs):
    """Build a minimal Namespace-like object."""
    import argparse
    return argparse.Namespace(**kwargs)


# ---------------------------------------------------------------------------
# register -> verify happy path
# ---------------------------------------------------------------------------

class TestRegisterVerify:
    def test_register_creates_manifest(self, tmp_vault: Path):
        """register writes a manifest and verify confirms it."""
        # Create a small asset file.
        asset = tmp_vault / "artwork.bin"
        asset.write_bytes(b"hello provenance")

        # Patch REPO_ROOT and MANIFEST_DIR to point at the tmp vault.
        manifest_dir = tmp_vault / "vault" / "manifests"
        with (
            mock.patch.object(provenance, "REPO_ROOT", tmp_vault),
            mock.patch.object(provenance, "MANIFEST_DIR", manifest_dir),
        ):
            # register
            rc = provenance.main(["register", str(asset), "--license", "CC0-1.0", "--method", "human"])
            assert rc == 0

            # manifest file should exist, named by the asset sha256
            digest = provenance.sha256_file(asset)
            mf = manifest_dir / f"{digest}.json"
            assert mf.is_file()

            m = json.loads(mf.read_text(encoding="utf-8"))
            assert m["asset"]["sha256"] == digest
            assert m["license"]["spdx"] == "CC0-1.0"
            assert m["chain"]["prev"] is None  # genesis

            # verify
            rc = provenance.main(["verify", str(asset)])
            assert rc == 0

    def test_verify_tampered_file_fails(self, tmp_vault: Path):
        asset = tmp_vault / "art2.bin"
        asset.write_bytes(b"original content")

        manifest_dir = tmp_vault / "vault" / "manifests"
        with (
            mock.patch.object(provenance, "REPO_ROOT", tmp_vault),
            mock.patch.object(provenance, "MANIFEST_DIR", manifest_dir),
        ):
            provenance.main(["register", str(asset)])
            # Tamper with the asset.
            asset.write_bytes(b"tampered content")
            rc = provenance.main(["verify", str(asset)])
            assert rc != 0

    def test_double_register_is_idempotent(self, tmp_vault: Path):
        asset = tmp_vault / "art3.bin"
        asset.write_bytes(b"idempotent")

        manifest_dir = tmp_vault / "vault" / "manifests"
        with (
            mock.patch.object(provenance, "REPO_ROOT", tmp_vault),
            mock.patch.object(provenance, "MANIFEST_DIR", manifest_dir),
        ):
            rc1 = provenance.main(["register", str(asset)])
            rc2 = provenance.main(["register", str(asset)])
            assert rc1 == 0
            assert rc2 == 0  # already registered — not an error

    def test_verify_unregistered_returns_nonzero(self, tmp_vault: Path):
        asset = tmp_vault / "art4.bin"
        asset.write_bytes(b"never registered")

        manifest_dir = tmp_vault / "vault" / "manifests"
        with (
            mock.patch.object(provenance, "REPO_ROOT", tmp_vault),
            mock.patch.object(provenance, "MANIFEST_DIR", manifest_dir),
        ):
            rc = provenance.main(["verify", str(asset)])
            assert rc != 0

    def test_chain_sequence_increments(self, tmp_vault: Path):
        """Registering two assets for the same creator produces seq 1 then seq 2."""
        asset1 = tmp_vault / "a1.bin"
        asset2 = tmp_vault / "a2.bin"
        asset1.write_bytes(b"first asset")
        asset2.write_bytes(b"second asset")

        manifest_dir = tmp_vault / "vault" / "manifests"
        with (
            mock.patch.object(provenance, "REPO_ROOT", tmp_vault),
            mock.patch.object(provenance, "MANIFEST_DIR", manifest_dir),
            mock.patch.object(provenance, "creator_identity",
                              return_value={"id": "artist@example.test", "name": "Artist"}),
        ):
            provenance.main(["register", str(asset1)])
            provenance.main(["register", str(asset2)])

            manifests = sorted(manifest_dir.glob("*.json"))
            data = [json.loads(mf.read_text(encoding="utf-8")) for mf in manifests]
            seqs = sorted(m["chain"]["sequence"] for m in data)
            assert seqs == [1, 2]

            # seq 2 must have a non-null prev pointing at seq 1's hash
            m2 = next(m for m in data if m["chain"]["sequence"] == 2)
            m1 = next(m for m in data if m["chain"]["sequence"] == 1)
            expected_prev = hashlib.sha256(canonical(m1)).hexdigest()
            assert m2["chain"]["prev"] == expected_prev


# ---------------------------------------------------------------------------
# anchor command
# ---------------------------------------------------------------------------

class TestAnchor:
    def test_anchor_prints_root(self, tmp_path: Path, capsys):
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        m1 = _make_manifest(_fake_sha("asset1"), "creator@test", None, 1)
        _write_manifest(manifest_dir, m1)

        rc = cmd_anchor(_args(manifest_dir=str(manifest_dir)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "merkle_root:" in out
        # Root must be a 64-char hex string
        root_line = next(l for l in out.splitlines() if "merkle_root:" in l)
        root_val = root_line.split("merkle_root:")[1].strip()
        assert len(root_val) == 64
        assert all(c in "0123456789abcdef" for c in root_val)

    def test_anchor_two_manifests(self, tmp_path: Path, capsys):
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        m1 = _make_manifest(_fake_sha("a1"), "c@t", None, 1)
        p1 = _write_manifest(manifest_dir, m1)
        prev1 = hashlib.sha256(canonical(m1)).hexdigest()
        m2 = _make_manifest(_fake_sha("a2"), "c@t", prev1, 2)
        _write_manifest(manifest_dir, m2)

        rc = cmd_anchor(_args(manifest_dir=str(manifest_dir)))
        assert rc == 0
        out = capsys.readouterr().out
        assert "2" in out  # manifests count

    def test_anchor_empty_dir_returns_error(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        rc = cmd_anchor(_args(manifest_dir=str(empty)))
        assert rc != 0


# ---------------------------------------------------------------------------
# verify-chain — valid chain
# ---------------------------------------------------------------------------

class TestVerifyChainValid:
    def test_single_genesis_manifest(self, tmp_path: Path, capsys):
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()
        m = _make_manifest(_fake_sha("asset"), "creator@test", None, 1)
        _write_manifest(manifest_dir, m)

        rc = cmd_verify_chain(_args(manifest_dir=str(manifest_dir)))
        assert rc == 0
        assert "OK" in capsys.readouterr().out

    def test_three_link_chain(self, tmp_path: Path, capsys):
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        m1 = _make_manifest(_fake_sha("a1"), "c@t", None, 1)
        _write_manifest(manifest_dir, m1)
        prev1 = hashlib.sha256(canonical(m1)).hexdigest()

        m2 = _make_manifest(_fake_sha("a2"), "c@t", prev1, 2)
        _write_manifest(manifest_dir, m2)
        prev2 = hashlib.sha256(canonical(m2)).hexdigest()

        m3 = _make_manifest(_fake_sha("a3"), "c@t", prev2, 3)
        _write_manifest(manifest_dir, m3)

        rc = cmd_verify_chain(_args(manifest_dir=str(manifest_dir)))
        assert rc == 0

    def test_two_creators_independent_chains(self, tmp_path: Path, capsys):
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        # Creator A: 2 manifests
        a1 = _make_manifest(_fake_sha("aa1"), "a@t", None, 1)
        _write_manifest(manifest_dir, a1)
        prev_a1 = hashlib.sha256(canonical(a1)).hexdigest()
        a2 = _make_manifest(_fake_sha("aa2"), "a@t", prev_a1, 2)
        _write_manifest(manifest_dir, a2)

        # Creator B: 1 manifest (genesis)
        b1 = _make_manifest(_fake_sha("bb1"), "b@t", None, 1)
        _write_manifest(manifest_dir, b1)

        rc = cmd_verify_chain(_args(manifest_dir=str(manifest_dir)))
        assert rc == 0


# ---------------------------------------------------------------------------
# verify-chain — tamper localization (THE key test)
# ---------------------------------------------------------------------------

class TestVerifyChainTamperLocalization:
    def test_tampered_middle_manifest_is_identified(self, tmp_path: Path, capsys):
        """Mutate the middle manifest of a 3-link chain; verify-chain must identify it.

        Tamper strategy: overwrite m2's content keeping its filename (asset sha).
        This causes:
          1. The filename-vs-asset.sha256 check to fire (asset.sha256 in content
             now differs from the filename which holds the original asset sha).
          2. The chain.prev of m3 to no longer match the canonical hash of the
             tampered m2 (chain link breakage — tamper localization).
        Both errors identify p2 by name.
        """
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        # Build a valid 3-link chain.
        m1 = _make_manifest(_fake_sha("t1"), "c@t", None, 1)
        _write_manifest(manifest_dir, m1)
        prev1 = hashlib.sha256(canonical(m1)).hexdigest()

        m2 = _make_manifest(_fake_sha("t2"), "c@t", prev1, 2)
        p2 = _write_manifest(manifest_dir, m2)   # named <_fake_sha("t2")>.json
        prev2 = hashlib.sha256(canonical(m2)).hexdigest()

        m3 = _make_manifest(_fake_sha("t3"), "c@t", prev2, 3)
        _write_manifest(manifest_dir, m3)

        # Sanity: chain should be valid before tampering.
        assert cmd_verify_chain(_args(manifest_dir=str(manifest_dir))) == 0
        capsys.readouterr()  # discard OK output

        # --- Tamper: overwrite p2 with altered content (different asset sha, same filename).
        m2_tampered = dict(m2)
        m2_tampered["asset"] = dict(m2["asset"])
        m2_tampered["asset"]["sha256"] = _fake_sha("TAMPERED-ASSET")
        # Keep filename as the ORIGINAL asset sha — now mismatches the content.
        p2.write_text(
            json.dumps(m2_tampered, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )

        # Chain must now be invalid.
        rc = cmd_verify_chain(_args(manifest_dir=str(manifest_dir)))
        assert rc != 0

        # The error output must mention p2's name (tamper localization).
        err = capsys.readouterr().err
        assert p2.name in err, (
            f"Expected tampered manifest filename '{p2.name}' in stderr, got:\n{err}"
        )

    def test_tampered_first_manifest_detected(self, tmp_path: Path, capsys):
        """Mutating the genesis manifest's asset.sha256 triggers the filename check."""
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        m1 = _make_manifest(_fake_sha("f1"), "c@t", None, 1)
        p1 = _write_manifest(manifest_dir, m1)  # named <_fake_sha("f1")>.json
        prev1 = hashlib.sha256(canonical(m1)).hexdigest()

        m2 = _make_manifest(_fake_sha("f2"), "c@t", prev1, 2)
        _write_manifest(manifest_dir, m2)

        # Sanity check
        assert cmd_verify_chain(_args(manifest_dir=str(manifest_dir))) == 0
        capsys.readouterr()

        # Tamper m1: change asset.sha256 in content but keep filename the same.
        m1_tampered = dict(m1)
        m1_tampered["asset"] = dict(m1["asset"])
        m1_tampered["asset"]["sha256"] = _fake_sha("TAMPERED-F1")
        p1.write_text(
            json.dumps(m1_tampered, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )

        rc = cmd_verify_chain(_args(manifest_dir=str(manifest_dir)))
        assert rc != 0
        err = capsys.readouterr().err
        # Filename-vs-asset.sha256 mismatch fires on p1; chain link on m2 fires too.
        assert "TAMPER" in err

    def test_wrong_prev_pointer_is_reported(self, tmp_path: Path, capsys):
        """A manifest whose chain.prev doesn't match the predecessor hash is reported."""
        manifest_dir = tmp_path / "manifests"
        manifest_dir.mkdir()

        m1 = _make_manifest(_fake_sha("w1"), "c@t", None, 1)
        _write_manifest(manifest_dir, m1)

        # m2 has a deliberately wrong prev pointer.
        m2 = _make_manifest(_fake_sha("w2"), "c@t", _fake_sha("wrong-prev"), 2)
        p2 = _write_manifest(manifest_dir, m2)

        rc = cmd_verify_chain(_args(manifest_dir=str(manifest_dir)))
        assert rc != 0
        err = capsys.readouterr().err
        assert p2.name in err

    def test_empty_dir_returns_error(self, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        rc = cmd_verify_chain(_args(manifest_dir=str(empty)))
        assert rc != 0
