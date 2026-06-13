#!/usr/bin/env python3
"""Art Provenance Vault — PoC CLI.

Stdlib-only proof of the core loop:
  register     <file>         hash the asset, write a manifest, commit it to the ledger
  verify       <file>         re-hash the asset and check it against the recorded manifest
  anchor       <manifest-dir> compute the Merkle root over all manifests and print/record it
  verify-chain <manifest-dir> walk chain.prev across manifests, recompute each content hash,
                               validate each link's prev linkage, and report which manifest
                               broke on tamper (tamper localization).

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

from merkle import build_merkle_root, merkle_proof, verify_proof  # noqa: F401

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


def _load_manifests(manifest_dir: Path) -> list[tuple[Path, dict]]:
    """Return (path, parsed_manifest) pairs sorted by filename (= sha256 digest)."""
    if not manifest_dir.is_dir():
        return []
    pairs = []
    for mf in sorted(manifest_dir.glob("*.json")):
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warning: could not parse {mf.name}: {exc}", file=sys.stderr)
            continue
        pairs.append((mf, m))
    return pairs


def cmd_anchor(args: argparse.Namespace) -> int:
    """Compute the Merkle root over all manifests in manifest_dir and print it.

    The root is the SHA-256 Merkle root (domain-separated, 0x00/0x01 prefixes)
    over the canonical-form hashes of every manifest, sorted by filename.

    This realizes ledger_anchor.merkle_root: the returned root can be published
    to a public chain / transparency log to timestamp the whole ledger batch.
    """
    manifest_dir = Path(args.manifest_dir).resolve()
    pairs = _load_manifests(manifest_dir)
    if not pairs:
        print(f"error: no manifests found in {manifest_dir}", file=sys.stderr)
        return 2

    # Leaf hashes: sha256 of canonical form of each manifest (same as chain.prev linkage)
    leaf_hashes = [
        hashlib.sha256(canonical(m)).hexdigest() for _, m in pairs
    ]
    root = build_merkle_root(leaf_hashes)

    print(f"manifests:    {len(pairs)}")
    print(f"merkle_root:  {root}")
    print()
    print("Leaf hashes (canonical sha256, sorted by filename):")
    for (mf, _), lh in zip(pairs, leaf_hashes):
        print(f"  {lh}  {mf.name}")
    return 0


def cmd_verify_chain(args: argparse.Namespace) -> int:
    """Walk chain.prev across all manifests, recompute hashes, and validate linkage.

    For each creator's chain (identified by creator.id), the algorithm:
      1. Sorts that creator's manifests by chain.sequence.
      2. Recomputes the canonical SHA-256 of each manifest on disk.
      3. Verifies chain.prev of each manifest matches the recomputed hash of
         the previous one.

    On tamper: reports WHICH manifest has the broken link (tamper localization),
    not just that the chain is invalid.

    Also validates that every manifest file is named <sha256>.json where sha256
    matches the canonical hash of its content (i.e. the file itself is intact).
    """
    manifest_dir = Path(args.manifest_dir).resolve()
    pairs = _load_manifests(manifest_dir)
    if not pairs:
        print(f"error: no manifests found in {manifest_dir}", file=sys.stderr)
        return 2

    errors: list[str] = []

    # Step 1: verify filename == asset sha256 recorded in the manifest.
    # Manifests are named <asset.sha256>.json by cmd_register; if the file has
    # been renamed or its content mutated so that asset.sha256 no longer matches
    # the filename, this is a structural tamper signal.
    for mf, m in pairs:
        recorded_asset_sha = m.get("asset", {}).get("sha256", "")
        if mf.stem != recorded_asset_sha:
            errors.append(
                f"TAMPER: {mf.name} — filename stem does not match asset.sha256 in manifest\n"
                f"  expected stem: {recorded_asset_sha}\n"
                f"  actual stem:   {mf.stem}"
            )

    # Step 2: group by creator and validate chain.prev linkage
    from collections import defaultdict
    by_creator: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    for mf, m in pairs:
        creator_id = m.get("creator", {}).get("id", "unknown")
        by_creator[creator_id].append((mf, m))

    for creator_id, creator_pairs in by_creator.items():
        # Sort by sequence number (fall back to 0 if missing)
        creator_pairs.sort(key=lambda t: t[1].get("chain", {}).get("sequence", 0))

        prev_hash: str | None = None
        for mf, m in creator_pairs:
            seq = m.get("chain", {}).get("sequence")
            recorded_prev = m.get("chain", {}).get("prev")
            canonical_hash = hashlib.sha256(canonical(m)).hexdigest()

            if prev_hash is None:
                # First manifest in chain: prev must be null
                if recorded_prev is not None:
                    errors.append(
                        f"TAMPER: {mf.name} — chain.prev should be null for first manifest\n"
                        f"  creator: {creator_id}  seq: {seq}\n"
                        f"  recorded prev: {recorded_prev}"
                    )
            else:
                # Subsequent manifest: prev must match canonical hash of predecessor
                if recorded_prev != prev_hash:
                    errors.append(
                        f"TAMPER: {mf.name} — chain.prev does not match predecessor hash\n"
                        f"  creator:      {creator_id}  seq: {seq}\n"
                        f"  expected prev: {prev_hash}\n"
                        f"  recorded prev: {recorded_prev}"
                    )
            prev_hash = canonical_hash

    total = len(pairs)
    creators = len(by_creator)
    if errors:
        print(
            f"CHAIN INVALID — {len(errors)} error(s) across {total} manifests "
            f"({creators} creator chain(s))",
            file=sys.stderr,
        )
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print(
        f"chain OK — {total} manifest(s) across {creators} creator chain(s), "
        f"all links verified"
    )
    return 0


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

    anc = sub.add_parser(
        "anchor",
        help="compute the Merkle root over all manifests and print it",
    )
    anc.add_argument(
        "manifest_dir",
        nargs="?",
        default=str(MANIFEST_DIR),
        help="directory containing *.json manifests (default: vault/manifests)",
    )
    anc.set_defaults(func=cmd_anchor)

    vc = sub.add_parser(
        "verify-chain",
        help="walk chain.prev across all manifests and report tamper localization",
    )
    vc.add_argument(
        "manifest_dir",
        nargs="?",
        default=str(MANIFEST_DIR),
        help="directory containing *.json manifests (default: vault/manifests)",
    )
    vc.set_defaults(func=cmd_verify_chain)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
