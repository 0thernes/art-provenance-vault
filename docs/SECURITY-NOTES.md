# Security Notes — Defensive Posture

Art Provenance Vault is a trust system for AI-assisted artwork. Its security
posture must be honest: state what is protected, how, and where the limits are
— so that creators and relying parties make informed decisions, not wishful ones.

This document is constructive and protection-focused. It describes what we are
defending, the trust boundaries we maintain, the risks we have identified, and
the mitigations we have in place or planned. It is not an attack playbook.

---

## Assets to Protect

| Asset | Description | Sensitivity |
|-------|-------------|-------------|
| **Signed manifests** | The provenance record for each artwork — creator, hash, license, derivation, watermark records | High — falsifying a manifest is the primary attack vector |
| **Ed25519 signing key** | The creator's private key (reserved in PoC; active from MVP) | Critical — compromise enables manifest forgery under the creator's identity |
| **Watermark embedding key** | The key seeding LSB/DCT positions (MVP+) | High — disclosure allows an attacker to verify or remove watermarks |
| **Asset bytes in CAS** | The artwork files in `vault/assets/` (MVP+) | Variable — depends on the creator's distribution intent; the CAS contains originals |
| **Git ledger history** | The commit DAG and its tamper-evidence property | High — rewriting history without detection undermines all provenance claims |
| **Creator identity bindings** | Mapping of `creator.id` → verified person/entity | Medium — currently self-asserted; strengthened by signing in MVP |

---

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────┐
│  Creator's machine                                      │
│   - provenance.py runs here                             │
│   - ~/.apv/signing.key lives here (MVP+)                │
│   - vault/ is a git clone here                          │
│  TRUSTED: creator controls this environment             │
├─────────────────────────────────────────────────────────┤
│  Git hosting (GitHub or self-hosted)                    │
│   - Holds the manifest ledger (not asset bytes)         │
│   - Provides clone replicas → tamper evidence           │
│  SEMI-TRUSTED: platform can delete; platform sees       │
│  all manifests (they are public provenance records)     │
│  Platform cannot forge a valid signature (MVP+)         │
├─────────────────────────────────────────────────────────┤
│  Content-addressed storage backend (MVP+)               │
│   - Holds asset bytes by hash                           │
│   - Local CAS: same trust as creator's machine          │
│   - S3/IPFS: external; treated as untrusted transport   │
│  Assets are authenticated by their SHA-256 hash         │
├─────────────────────────────────────────────────────────┤
│  Recipients / licensees                                 │
│   - Receive watermarked variants (MVP+)                 │
│   - Can verify against the public ledger                │
│  UNTRUSTED: assume a recipient may attempt to leak      │
│  or strip watermarks                                    │
├─────────────────────────────────────────────────────────┤
│  Public / verifiers                                     │
│   - Can clone the ledger and verify any manifest        │
│   - No write access; no key material                    │
│  UNTRUSTED INPUT: any file submitted for verify may     │
│  be malicious (oversized, path-traversal filename, etc) │
└─────────────────────────────────────────────────────────┘
```

---

## Risk Categories and Mitigations

### 1. Manifest Forgery

**Risk:** An attacker creates a manifest claiming authorship of someone else's
work and commits it to a vault they control.

**Mitigations in place (PoC):**
- SHA-256 content identity — the asset hash in the manifest must match the
  actual bytes. An attacker cannot claim a different SHA-256 without also
  controlling the content.
- Git commit timestamps and parent hashes — a forged manifest committed after
  a legitimate one is detectable by anyone holding an earlier clone.
- `chain.prev` linkage — the creator's chain forms a hash-linked sequence.
  Inserting a forged manifest into the chain requires forging all subsequent
  `chain.prev` hashes.

**Planned mitigations (MVP):**
- Ed25519 signatures over canonicalized manifests. A signature created with
  the creator's private key cannot be reproduced without that key. Forgery
  becomes a key-compromise problem, not a data-editing problem.
- `creator.public_key_fingerprint` binds the signature to a stable creator
  identity. Changing the `creator` field invalidates the signature.

**Honest limit:** In the PoC, anyone with push access to the vault can alter
manifest fields. This is a documented PoC limitation, not a reportable
vulnerability. See SECURITY.md.

---

### 2. Private Key Compromise (MVP+)

**Risk:** The creator's Ed25519 signing key is stolen, allowing an attacker to
sign manifests as the creator.

**Mitigations planned (MVP):**
- Private key stored at `~/.apv/signing.key` with mode `0600` (owner read
  only). Written atomically on first use.
- The private key is never logged, never included in any manifest field, and
  never transmitted. `provenance.py` reads it once per invocation and does not
  cache it in memory beyond the signing operation.
- The manifest records only `creator.public_key_fingerprint` — enough to
  identify the key in use without revealing any key material.
- Key rotation: when a key is rotated, the old fingerprint remains valid for
  manifests signed before rotation. A `keychain` entry (v1) will map
  fingerprint → validity period.
- **Users should back up their signing key offline.** Loss means future
  manifests will start a new chain that cannot be linked to the old one by
  signature; the git history still proves temporal ordering.

**Recommended practice:** store the private key on an encrypted volume or
hardware security token. APV does not enforce this but documents it here.

---

### 3. Ledger History Rewrite (Git Force-Push)

**Risk:** A creator, or an attacker who compromises the creator's git
credentials, rewrites the vault history, altering or deleting past manifests.

**Mitigations in place:**
- Every `git clone` is a full replica. Any holder of a clone from before the
  rewrite can detect the discrepancy by comparing commit hashes.
- `chain.prev` in manifests provides an independent hash chain inside the
  data, not just in git. Even if git history is rewritten, manifests that were
  previously exported (via C2PA, IPFS, or a court filing) carry the chain
  linkage and can be cross-checked.
- GitHub's branch protection can require signed commits and disallow
  force-push to `main`. Enabling this is strongly recommended for production
  vaults.

**Planned mitigations (v1):**
- Merkle-root anchoring via OpenTimestamps publishes a periodic proof of the
  ledger state to a public transparency log. A rewrite that omits manifests
  present before the anchor is detectable by anyone using the anchor proof.

**Honest limit:** The PoC has no witness infrastructure. A solo creator with
no independent clone has no tamper evidence except the manifest's `chain.prev`
chain. The architecture document is explicit about this. It is a design
boundary, not a vulnerability.

---

### 4. Untrusted File Input to the CLI

**Risk:** A malicious user passes a specially crafted file path or filename to
`register` or `verify` in an attempt to read files outside the vault, trigger
path traversal, or cause unexpected subprocess behaviour.

**Mitigations in place:**
- All user-supplied file paths are resolved via `Path.resolve()` before use.
  This collapses `../` sequences and resolves symlinks.
- The git commit message includes only the first 12 hex characters of the
  SHA-256 digest and the asset's filename. The SHA-256 digest is hex-only
  (no shell metacharacters possible). The filename is passed as a separate
  argument to `git commit -m`, not concatenated into a shell string.
- `subprocess.run` is called with an explicit argument list; `shell=True` is
  never used. No user input is interpolated into a shell string.
- JSON manifests are parsed with `json.loads()`. No `yaml.load()`, `eval()`,
  `exec()`, or `pickle.loads()` is used anywhere in the codebase.
- `media_type` is inferred from the filename extension via
  `mimetypes.guess_type()`, not from user-supplied input or file content
  sniffing. A file named `evil.php` does not execute; it just gets
  `media_type: "application/x-php"` in the manifest.

**Residual risk (noted):** Symlink traversal. If the user passes a path that
is a symlink pointing outside the vault, `Path.resolve()` will follow it to
the real path. The file will be hashed and registered. This is consistent with
the operating system's behaviour and is not a security vulnerability for a CLI
tool running with the creator's own permissions. It is noted here for
completeness.

---

### 5. Schema Validation Bypass

**Risk:** A crafted manifest JSON file that passes `json.loads()` but fails
the JSON Schema contract is committed to the ledger, producing a corrupt
provenance record.

**Mitigations in place:**
- `register` produces manifests programmatically from a controlled dict
  structure. It does not accept a manifest as user input in the PoC.
- CI runs `Draft202012Validator.check_schema(schema)` to validate that the
  schema itself is well-formed as draft 2020-12.
- The smoke test round-trip confirms that a registered manifest validates
  against the schema.
- Any future `import` command that accepts external manifests must validate
  against the schema as the first step before writing or acting on any field.

---

### 6. Watermark Integrity and Removal (MVP+)

**Risk:** A recipient strips or launders the invisible watermark from a
licensed copy, breaking the leak-tracing chain.

**Mitigations and honest limits:**
- Stage 1 (XMP/PNG-text): no adversarial robustness. A platform that strips
  metadata defeats Stage 1 trivially. Stage 1's value is cooperative discovery,
  not adversarial tracing.
- Stage 2 (LSB): surviving lossless copying only. The embedding key seed is
  not in the manifest (only `key_id` is). An attacker without the key cannot
  know which pixels carry payload bits and cannot remove them without
  destroying arbitrary pixels — which is detectable as quality degradation.
- Stage 3 (DCT/DWT, v1): survives moderate JPEG and mild resize. A determined
  attacker with access to the watermarked file and knowledge of the algorithm
  can attempt statistical attacks. The key seed is not public.
- Stage 4 (multivariant, v1): collusion-resistant codes (Tardos-style) make
  it computationally expensive to average away watermarks without perceptible
  quality loss, even for colluding recipients.

**Watermark robustness is a tracing aid, not a rights enforcement mechanism.**
The legal and business value of APV rests on the signed manifest ledger. The
watermark pipeline raises the cost of undetected infringement and catches
careless leakers; it does not prevent a determined attacker with modern tools.
This framing is stated in all partner-facing materials.

---

### 7. Supply-Chain Integrity of CI / Dependencies

**Risk:** A compromised GitHub Action or Python package injects malicious code
into the CI pipeline or the published tool.

**Mitigations in place:**
- All GitHub Actions in `.github/workflows/` are pinned to specific version
  tags (e.g., `actions/checkout@v4`), not floating `@main` or `@latest`.
- `dependabot.yml` monitors both the `github-actions` and `pip` ecosystems
  weekly and opens PRs for dependency updates, making upgrades visible and
  reviewed.
- The PoC has **zero runtime dependencies** beyond Python 3.10+ stdlib. There
  is no supply-chain exposure for the deployed tool in PoC state.
- When MVP dependencies (`cryptography`, `Pillow`, `NumPy`) are added, they
  will be pinned with hashes in `requirements.txt` (`pip install --require-hashes`).

---

## Summary: What APV Guarantees (PoC Stage)

| Property | Status |
|----------|--------|
| Content integrity — SHA-256 of asset bytes | Guaranteed |
| Ordering — manifest A committed before manifest B is detectable | Guaranteed (git DAG) |
| Authorship — creator field is a verified identity | Not yet (PoC limitation — MVP Ed25519 signing) |
| Non-repudiation — creator cannot deny the manifest | Not yet (requires signature) |
| Tamper evidence — manifest alteration is detectable | Guaranteed IF witnesses (clones) exist |
| Leak tracing — which recipient leaked a copy | Not yet (watermarking is MVP+) |
| Long-term timestamp — independent of APV infrastructure | Not yet (anchoring is v1) |

This table is reproduced in `docs/FAQ.md` and should be updated with each
phase as properties move from "not yet" to "guaranteed."
