# Contributing to Art Provenance Vault

Thank you for your interest. APV is in proof-of-concept stage and maintained by
a solo founder; contributions are welcome but the bar for scope is deliberately
tight.

## Ground Rules

- **Stdlib-only in the PoC.** `src/provenance.py` must run on a clean
  Python 3.10+ install with no `pip install`. Dependencies (cryptography,
  Pillow, NumPy) arrive in the MVP phase behind explicit ADRs.
- **The schema is a contract.** Any change to
  `schemas/manifest.schema.json` requires: a version bump in the
  `manifest_version` const, a CHANGELOG entry, and a note on migration of
  existing manifests. Breaking the verifiability of already-committed
  manifests is not acceptable.
- **Architecture decisions go through ADRs.** Anything that changes a layer
  boundary in `docs/ARCHITECTURE.md` needs a new file in `docs/adr/`
  (sequential numbering, the format established by ADR-0001).
- **Never commit secrets or private keys.** The `.gitignore` blocks common
  key formats; treat that as a backstop, not a guarantee.

## Workflow

1. Open an issue describing the problem before sending a change.
2. Branch from `main`; keep commits focused and messages in
   [Conventional Commits](https://www.conventionalcommits.org/) form
   (`feat:`, `fix:`, `docs:`, `chore:`).
3. Make sure CI passes: `python -m py_compile src/provenance.py` and the
   schema must validate as JSON Schema draft 2020-12.
4. Update CHANGELOG.md under `[Unreleased]`.

## Code Style

- Follow `.editorconfig` (4-space indent, LF endings, UTF-8).
- Keep functions small; the PoC CLI should remain readable top to bottom in
  one sitting.
- Prefer explicit error messages that name the file and the expected hash —
  this is a trust tool, vague errors erode it.

## Reporting Security Issues

Do **not** open a public issue for vulnerabilities. See [SECURITY.md](SECURITY.md).
