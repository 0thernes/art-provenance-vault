"""Tests for src/merkle.py — Merkle tree round-trip, inclusion proofs, tamper detection."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from merkle import build_merkle_root, merkle_proof, verify_proof  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_leaf(seed: str) -> str:
    """A deterministic 64-char hex digest to stand in for a manifest hash."""
    return hashlib.sha256(seed.encode()).hexdigest()


LEAVES_1 = [_fake_leaf("a")]
LEAVES_2 = [_fake_leaf("a"), _fake_leaf("b")]
LEAVES_3 = [_fake_leaf("a"), _fake_leaf("b"), _fake_leaf("c")]
LEAVES_4 = [_fake_leaf(c) for c in "abcd"]
LEAVES_7 = [_fake_leaf(c) for c in "abcdefg"]


# ---------------------------------------------------------------------------
# build_merkle_root
# ---------------------------------------------------------------------------

class TestBuildMerkleRoot:
    def test_single_leaf_is_domain_separated(self):
        leaf = _fake_leaf("x")
        root = build_merkle_root([leaf])
        # Must equal SHA-256(0x00 || leaf_bytes), not leaf itself.
        expected = hashlib.sha256(b"\x00" + bytes.fromhex(leaf)).hexdigest()
        assert root == expected

    def test_two_leaves_deterministic(self):
        r1 = build_merkle_root(LEAVES_2)
        r2 = build_merkle_root(LEAVES_2)
        assert r1 == r2
        assert len(r1) == 64

    def test_different_leaf_sets_give_different_roots(self):
        assert build_merkle_root(LEAVES_2) != build_merkle_root(LEAVES_3)

    def test_order_matters(self):
        leaves_reversed = list(reversed(LEAVES_4))
        assert build_merkle_root(LEAVES_4) != build_merkle_root(leaves_reversed)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="at least one leaf"):
            build_merkle_root([])

    def test_odd_number_of_leaves(self):
        # Must not raise; duplicate-last convention handles odd levels.
        root = build_merkle_root(LEAVES_3)
        assert len(root) == 64

    def test_seven_leaves(self):
        root = build_merkle_root(LEAVES_7)
        assert len(root) == 64

    def test_root_changes_when_leaf_changes(self):
        leaves_a = [_fake_leaf("a"), _fake_leaf("b"), _fake_leaf("c")]
        leaves_b = [_fake_leaf("a"), _fake_leaf("TAMPERED"), _fake_leaf("c")]
        assert build_merkle_root(leaves_a) != build_merkle_root(leaves_b)


# ---------------------------------------------------------------------------
# merkle_proof + verify_proof — round-trip
# ---------------------------------------------------------------------------

class TestInclusionProof:
    @pytest.mark.parametrize("leaves,index", [
        (LEAVES_1, 0),
        (LEAVES_2, 0),
        (LEAVES_2, 1),
        (LEAVES_3, 0),
        (LEAVES_3, 1),
        (LEAVES_3, 2),
        (LEAVES_4, 0),
        (LEAVES_4, 3),
        (LEAVES_7, 0),
        (LEAVES_7, 3),
        (LEAVES_7, 6),
    ])
    def test_valid_proof_verifies(self, leaves, index):
        root = build_merkle_root(leaves)
        proof = merkle_proof(leaves, index)
        assert verify_proof(leaves[index], proof, root) is True

    @pytest.mark.parametrize("leaves,index", [
        (LEAVES_2, 0),
        (LEAVES_4, 1),
        (LEAVES_7, 4),
    ])
    def test_tampered_leaf_fails(self, leaves, index):
        root = build_merkle_root(leaves)
        proof = merkle_proof(leaves, index)
        tampered = _fake_leaf("this-is-NOT-the-real-leaf")
        assert verify_proof(tampered, proof, root) is False

    def test_proof_wrong_root_fails(self):
        root = build_merkle_root(LEAVES_4)
        wrong_root = build_merkle_root(LEAVES_3)
        proof = merkle_proof(LEAVES_4, 0)
        assert verify_proof(LEAVES_4[0], proof, wrong_root) is False

    def test_out_of_range_index_raises(self):
        with pytest.raises(IndexError):
            merkle_proof(LEAVES_3, 3)

    def test_negative_index_raises(self):
        with pytest.raises(IndexError):
            merkle_proof(LEAVES_3, -1)

    def test_proof_path_length(self):
        """Proof length should be ceil(log2(n)) for a power-of-two tree."""
        import math
        for leaves in [LEAVES_2, LEAVES_4]:
            n = len(leaves)
            proof = merkle_proof(leaves, 0)
            assert len(proof) == math.ceil(math.log2(n))

    def test_sibling_swap_fails(self):
        """Swapping a sibling hash in the proof must cause verify to fail."""
        root = build_merkle_root(LEAVES_4)
        proof = merkle_proof(LEAVES_4, 0)
        bad_proof = [{"sibling": _fake_leaf("wrong"), "direction": proof[0]["direction"]}] + proof[1:]
        assert verify_proof(LEAVES_4[0], bad_proof, root) is False

    def test_direction_flip_fails(self):
        """Flipping a direction in the proof must cause verify to fail (non-trivially)."""
        root = build_merkle_root(LEAVES_4)
        proof = merkle_proof(LEAVES_4, 1)
        # Flip the first direction
        orig = proof[0]["direction"]
        flipped = "left" if orig == "right" else "right"
        bad_proof = [{"sibling": proof[0]["sibling"], "direction": flipped}] + proof[1:]
        # This should either give the wrong hash or fail
        assert verify_proof(LEAVES_4[1], bad_proof, root) is False

    def test_invalid_direction_raises(self):
        root = build_merkle_root(LEAVES_2)
        bad_proof = [{"sibling": LEAVES_2[1], "direction": "up"}]
        with pytest.raises(ValueError, match="invalid direction"):
            verify_proof(LEAVES_2[0], bad_proof, root)
