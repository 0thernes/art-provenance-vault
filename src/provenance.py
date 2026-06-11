#!/usr/bin/env python3
"""Art Provenance Vault — PoC CLI.

Stdlib-only proof of the core loop:
  register <file>  hash the asset, write a manifest, commit it to the ledger
  verify   <file>  re-hash the asset and check it against the recorded manifest

Git stores manifests (the ledger), never the asset bytes themselves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "vault" / "manifests"
MANIFEST_VERSION = "0.1.0"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical(manifest: dict) -> bytes:
    """Canonical form (sorted keys, compact) — what MVP signatures will cover."""
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git(*args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def creator_identity() -> dict:
    """Creator claim from git config — a PoC stand-in for keypair identity (MVP)."""
    try:
        name = git("config", "user.name") or "unknown"
        email = git("config", "user.email") or "unknown@invalid"
    except subprocess.CalledProcessError:
        name, email = "unknown", "unknown@invalid"
    return {"id": email, "name": name}


def chain_prev(creator_id: str) -> tuple[str | None, int]:
    """Latest manifest hash + next sequence number for this creator."""
    head, seq = None, 0
    for mf in sorted(MANIFEST_DIR.glob("*.json")) if MANIFEST_DIR.is_dir() else []:
        m = json.loads(mf.read_text(encoding="utf-8"))
        if m.get("creator", {}).get("id") == creator_id and m["chain"].get("sequence", 0) > seq:
            seq = m["chain"]["sequence"]
            head = hashlib.sha256(canonical(m)).hexdigest()
    return head, seq + 1


def cmd_register(args: argparse.Namespace) -> int:
    asset = Path(args.file).resolve()
    if not asset.is_file():
        print(f"error: no such file: {asset}", file=sys.stderr)
        return 2
    digest = sha256_file(asset)
    manifest_path = MANIFEST_DIR / f"{digest}.json"
    if manifest_path.exists():
        print(f"already registered: {digest}")
        return 0
    creator = creator_identity()
    prev, seq = chain_prev(creator["id"])
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "asset": {
            "sha256": digest,
            "byte_size": asset.stat().st_size,
            "filename": asset.name,
            "media_type": mimetypes.guess_type(asset.name)[0] or "application/octet-stream",
        },
        "creator": creator,
        "creation": {"method": args.method},
        "license": {"spdx": args.license},
        "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chain": {"prev": prev, "sequence": seq},
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    rel = manifest_path.relative_to(REPO_ROOT).as_posix()
    git("add", "--", rel)
    git("commit", "-m", f"ledger: register {digest[:12]} ({asset.name})")
    print(f"registered: {digest}")
    print(f"manifest:   {rel}")
    print(f"chain:      seq {seq}, prev {prev or '(genesis)'}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    asset = Path(args.file).resolve()
    if not asset.is_file():
        print(f"error: no such file: {asset}", file=sys.stderr)
        return 2
    digest = sha256_file(asset)
    manifest_path = MANIFEST_DIR / f"{digest}.json"
    if manifest_path.is_file():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"VERIFIED  {asset.name}")
        print(f"  sha256:     {digest}")
        print(f"  creator:    {m['creator']['name']} <{m['creator']['id']}>")
        print(f"  license:    {m['license']['spdx']}")
        print(f"  registered: {m['registered_at']}  (chain seq {m['chain'].get('sequence')})")
        return 0
    # Not found by hash — check whether a same-named registration exists (tamper hint).
    for mf in sorted(MANIFEST_DIR.glob("*.json")) if MANIFEST_DIR.is_dir() else []:
        m = json.loads(mf.read_text(encoding="utf-8"))
        if m["asset"].get("filename") == asset.name:
            print(f"FAILED    {asset.name}: content does not match the ledger", file=sys.stderr)
            print(f"  expected sha256: {m['asset']['sha256']}", file=sys.stderr)
            print(f"  actual sha256:   {digest}", file=sys.stderr)
            return 1
    print(f"UNREGISTERED  {asset.name} (sha256 {digest})", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="provenance", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    reg = sub.add_parser("register", help="hash an asset, write its manifest, commit to the ledger")
    reg.add_argument("file")
    reg.add_argument("--license", default="CC-BY-4.0", help="SPDX license expression")
    reg.add_argument(
        "--method",
        default="ai_assisted",
        choices=["human", "ai_generated", "ai_assisted", "hybrid"],
        help="creation method recorded in the manifest",
    )
    reg.set_defaults(func=cmd_register)
    ver = sub.add_parser("verify", help="re-hash an asset and check it against the ledger")
    ver.add_argument("file")
    ver.set_defaults(func=cmd_verify)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
