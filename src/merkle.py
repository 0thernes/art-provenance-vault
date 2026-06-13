"""Art Provenance Vault — Merkle tree over the manifest ledger (stdlib-only).

Implements:
  build_merkle_root(leaf_hashes)  -> root hex digest
  merkle_proof(leaf_hashes, index) -> list[dict]  (sibling hashes + directions)
  verify_proof(leaf_hash, proof, root) -> bool

Security properties
-------------------
* SHA-256 throughout (hashlib).
* Domain-separated hashing: leaf nodes are prefixed 0x00, internal nodes 0x01
  before hashing, preventing second-preimage attacks where an internal node
  hash could be mistaken for a leaf (see RFC 6962 §2.1).
* Odd-level duplicate: when a level has an odd number of nodes the last node is
  duplicated, matching the Bitcoin/many-ledger convention. This is safe here
  because the duplicate is on the right and the tree position is part of the
  proof (not just the hash).

Usage
-----
    from merkle import build_merkle_root, merkle_proof, verify_proof

    hashes = [sha256(m) for m in manifests]
    root = build_merkle_root(hashes)
    proof = merkle_proof(hashes, index=2)
    assert verify_proof(hashes[2], proof, root)
"""
from __future__ import annotations

import hashlib

# Domain-separation prefixes (RFC 6962 style).
_LEAF_PREFIX = b"\x00"
_NODE_PREFIX = b"\x01"


def _leaf_hash(data: str | bytes) -> str:
    """SHA-256( 0x00 || data ).  data may be a hex digest string or raw bytes."""
    raw = bytes.fromhex(data) if isinstance(data, str) else data
    return hashlib.sha256(_LEAF_PREFIX + raw).hexdigest()


def _node_hash(left: str, right: str) -> str:
    """SHA-256( 0x01 || left_bytes || right_bytes )."""
    return hashlib.sha256(
        _NODE_PREFIX + bytes.fromhex(left) + bytes.fromhex(right)
    ).hexdigest()


def _build_tree_levels(leaf_hashes: list[str]) -> list[list[str]]:
    """Return all levels of the tree, bottom-up.

    levels[0] = leaf-hashed nodes (domain-separated)
    levels[-1] = [root]
    """
    if not leaf_hashes:
        raise ValueError("build_merkle_root requires at least one leaf")

    current = [_leaf_hash(h) for h in leaf_hashes]
    levels: list[list[str]] = [current]

    while len(current) > 1:
        if len(current) % 2 == 1:
            current = current + [current[-1]]  # duplicate last on odd level
        next_level = [
            _node_hash(current[i], current[i + 1]) for i in range(0, len(current), 2)
        ]
        levels.append(next_level)
        current = next_level

    return levels


def build_merkle_root(leaf_hashes: list[str]) -> str:
    """Return the Merkle root (hex SHA-256) for the given leaf hashes.

    Each element of *leaf_hashes* must be a 64-character lowercase hex string
    (e.g. the sha256 of a manifest file in canonical form).

    A single-leaf tree returns SHA-256(0x00 || leaf_bytes).
    """
    return _build_tree_levels(leaf_hashes)[-1][0]


def merkle_proof(leaf_hashes: list[str], index: int) -> list[dict]:
    """Return the inclusion-proof path for *leaf_hashes[index]*.

    Each step in the proof is a dict::

        {"sibling": "<hex>", "direction": "left" | "right"}

    "direction" is the direction of the *sibling* relative to the current node.
    During verification, combine current + sibling in the order:
      - sibling is "left"  -> hash = node_hash(sibling, current)
      - sibling is "right" -> hash = node_hash(current, sibling)

    Raises IndexError if *index* is out of range.
    """
    n = len(leaf_hashes)
    if not 0 <= index < n:
        raise IndexError(f"index {index} out of range for {n} leaves")

    levels = _build_tree_levels(leaf_hashes)
    proof: list[dict] = []
    pos = index

    for level in levels[:-1]:  # all levels except the root level
        # If this level was padded to even length, duplicate the last node.
        padded = level + [level[-1]] if len(level) % 2 == 1 else level
        if pos % 2 == 0:
            # Current is left child; sibling is to the right.
            sibling_pos = pos + 1
            direction = "right"
        else:
            # Current is right child; sibling is to the left.
            sibling_pos = pos - 1
            direction = "left"
        proof.append({"sibling": padded[sibling_pos], "direction": direction})
        pos //= 2

    return proof


def verify_proof(leaf_hash: str, proof: list[dict], root: str) -> bool:
    """Return True iff the proof demonstrates *leaf_hash* is in the tree at *root*.

    *leaf_hash* is the raw manifest hash (hex, 64 chars) — the same value that
    was passed as an element of *leaf_hashes* to :func:`build_merkle_root`.
    The function applies the leaf domain-separation prefix internally.
    """
    current = _leaf_hash(leaf_hash)
    for step in proof:
        sibling = step["sibling"]
        direction = step["direction"]
        if direction == "left":
            current = _node_hash(sibling, current)
        elif direction == "right":
            current = _node_hash(current, sibling)
        else:
            raise ValueError(f"invalid direction in proof step: {direction!r}")
    return current == root
