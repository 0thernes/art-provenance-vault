# Security Policy

## Why security reports matter here

Art Provenance Vault is a trust system. A bug that lets an attacker forge a
manifest, produce a hash collision in practice, strip a watermark silently, or
rewrite ledger history without detection is not a normal bug — it defeats the
product. Such reports are treated at the highest priority.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x (PoC) | ✅ Current development line |

## Reporting a Vulnerability

Email **0_0@0thernes.art** with the subject line `[APV SECURITY]`.

Please include:

- A description of the issue and its impact on the trust model
  (forgery, tamper-evidence bypass, watermark removal, key exposure).
- Reproduction steps or a proof-of-concept manifest/asset pair.
- Your assessment of severity.

You can expect an acknowledgement within 72 hours and a remediation plan or
triage decision within 14 days. Please allow a 90-day coordinated-disclosure
window before publishing.

## Threat Model Notes (PoC stage)

Known, documented limitations of the current PoC — these are **not**
reportable vulnerabilities because they are stated design boundaries:

- Manifests are **not yet cryptographically signed**; the `signature` field
  is reserved. Until MVP signing lands, the ledger proves integrity and
  ordering, not authorship.
- A ledger holder with force-push rights can rewrite their own copy of
  history; tamper evidence depends on clones/witnesses holding earlier
  states. This is inherent to the design and mitigated by anchoring (v1).
- No watermarking is implemented yet; watermark records in manifests are
  declarative.

Anything outside those boundaries — especially manifest parsing flaws,
path-handling issues in the CLI, or schema-validation bypasses — please report.
