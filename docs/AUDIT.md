# Self-Audit Checklist

This checklist is the primary quality gate for Art Provenance Vault. Run it
before any release cut, any schema change, and any change to the trust-critical
paths (`sha256_file`, `canonical`, `cmd_register`, `cmd_verify`). Each item
must be verifiable — check it, don't assume it.

Items are organised by category. Add new items here as the codebase grows.

---

## Correctness

- [ ] `sha256_file` reads the asset in 1 MiB blocks; verified it does not skip
      the final partial block for assets whose size is not a multiple of
      `1 << 20`.
- [ ] `canonical()` produces byte-identical output across Python 3.10, 3.11,
      and 3.12 for the same manifest dict (key ordering, no insignificant
      whitespace, UTF-8 encoding confirmed).
- [ ] `chain_prev` scans all manifests for the creator's highest sequence
      number; confirmed it handles the empty-vault case (returns `(None, 1)`).
- [ ] `cmd_verify` exits non-zero for a tampered file AND prints both the
      expected and actual SHA-256 values to stderr. Verified in CI smoke test.
- [ ] `cmd_verify` exits non-zero for an unregistered asset (not just tampered).
- [ ] `cmd_register` is idempotent for the same asset: calling it twice does
      not create a second git commit or a second manifest file.
- [ ] Manifest written by `cmd_register` validates against
      `schemas/manifest.schema.json` (draft 2020-12) without errors.
- [ ] `chain.sequence` increments correctly across multiple registrations by
      the same creator in the same session and across sessions.
- [ ] `chain.prev` in the second manifest equals `sha256(canonical(first
      manifest))` — not the asset hash, the manifest hash.

---

## Security

- [ ] No secret, private key, or credential is present anywhere in the
      repository. Run `git log --all --full-history -- '*.pem' '*.key' '.env'`
      and confirm empty result.
- [ ] `.gitignore` blocks `*.pem`, `*.key`, `*.p12`, `.env`, `.env.*`, and
      `~/.apv/signing.key`-equivalent paths.
- [ ] `src/provenance.py` does not call `eval()`, `exec()`, `pickle.loads()`,
      or `subprocess.run(shell=True)`. Confirmed by grep.
- [ ] Path inputs from the command line are resolved via `Path.resolve()` before
      use. Symlink traversal is intentional and documented; symlink-to-outside-
      vault is noted as a risk in SECURITY-NOTES.md.
- [ ] The `git commit` subprocess is invoked with an explicit argument list, not
      a shell string. Manifest hash in the commit message cannot cause command
      injection (SHA-256 is hex-only).
- [ ] Manifest files are read with `encoding="utf-8"` and parsed via
      `json.loads()` only — no `yaml.load()` or custom deserialiser.
- [ ] `media_type` in the manifest is inferred via `mimetypes.guess_type`, not
      trusted from user input. A malicious filename extension cannot cause the
      system to execute or interpret the file differently.
- [ ] The `vault/manifests/` directory is created with default permissions;
      on Unix this is `0755`. Confirm that world-readable manifests is
      intentional (they are public provenance records).
- [ ] (MVP+) Ed25519 private key written with mode `0600`. Verified after
      `keygen` command.
- [ ] (MVP+) Signing does not log the private key or any key material at any
      log level.
- [ ] CodeQL scan shows no HIGH or CRITICAL findings in `src/`.

---

## Provenance Integrity

- [ ] Every registered manifest in `vault/manifests/` is present in exactly
      one git commit with a `ledger: register` message. Run
      `git log --oneline -- vault/manifests/` and cross-check file count.
- [ ] No manifest file in `vault/manifests/` appears in the working tree
      without a corresponding git commit (i.e., `git status` shows no
      untracked manifest files after a clean `register` run).
- [ ] `chain.prev` linkage is consistent: for creator C, the manifest with
      `chain.sequence = N` has `chain.prev` equal to the SHA-256 of the
      canonical form of the manifest with `chain.sequence = N-1`.
- [ ] `asset.sha256` in the manifest equals `sha256_file(asset)` computed
      fresh. Verify for at least the 3 most recently registered assets.
- [ ] Schema `$id` URI (`https://0thernes.art/schemas/apv/manifest.schema.json`)
      is stable and not redirected to an attacker-controlled endpoint
      (relevant for validators that dereference `$id`).
- [ ] (MVP+) All manifests in the ledger that carry a `signature` field pass
      `verify` with their recorded `creator.public_key_fingerprint`.

---

## Performance

- [ ] `sha256_file` on a 50 MB file completes in < 1 second on the CI runner.
      If not, confirm block size is 1 MiB (not smaller).
- [ ] `chain_prev` scan over 500 manifest files completes in < 2 seconds
      without the SQLite index. If not, the index (T-007) is overdue.
- [ ] `git commit` for a single manifest file completes in < 5 seconds on
      CI. If git is slow, check that `vault/assets/` is not accidentally
      staged (it is gitignored but a misconfigured repo can override).
- [ ] (MVP+) SQLite index rebuild over 500 manifests completes in < 10 seconds.

---

## Reproducibility

- [ ] `canonical()` is deterministic: the same manifest dict always produces
      the same bytes regardless of insertion order of the dict keys.
- [ ] Running `register` on the same asset at different times produces
      different `registered_at` timestamps but the same `asset.sha256` and the
      system detects "already registered" and does not create a second manifest.
- [ ] `schemas/manifest.schema.json` is valid according to the JSON Schema
      meta-schema for draft 2020-12. Checked by `make schema-validate`.
- [ ] All CI jobs are pinned to specific action versions (e.g.
      `actions/checkout@v4`) to prevent supply-chain drift.

---

## Documentation

- [ ] `docs/ARCHITECTURE.md` accurately describes the current PoC behaviour,
      including what is NOT yet implemented (signing, watermarking).
- [ ] Every ROADMAP acceptance criterion has a corresponding test (or a
      documented gap with a Kanban card referencing it).
- [ ] CHANGELOG has an entry for every user-visible change since the last
      version tag.
- [ ] CONTRIBUTING.md reflects the current development workflow (branch names,
      commit format, CI requirements).
- [ ] The `--help` output of `python src/provenance.py` accurately describes
      the `--license` and `--method` defaults.
- [ ] `docs/SECURITY-NOTES.md` is current: stated PoC limitations match the
      actual code (e.g., "unsigned manifests" is accurate until T-001 ships).

---

## Tests

- [ ] CI smoke test (register + verify + tamper) passes on every push to
      `main`. No bypasses (`--no-verify` or `skip: true` in the workflow)
      are present.
- [ ] For every happy-path test, a corresponding failure-path test exists that
      asserts a non-zero exit code and a specific error message.
- [ ] No test creates files in the real `vault/manifests/` directory; all
      tests use temporary directories.
- [ ] (MVP+) The "Stage 2 watermark destroyed by JPEG re-encode" failure-mode
      test is present and asserts extraction fails (not silently passes).

---

## Developer Experience

- [ ] `python src/provenance.py register --help` and `verify --help` print
      useful usage without errors on Python 3.10, 3.11, and 3.12.
- [ ] `make help` lists all targets with one-line descriptions.
- [ ] Pre-commit hooks install cleanly on a fresh clone with `make setup`.
- [ ] The repo clones and runs the smoke test end to end on Windows (Git Bash)
      and Ubuntu without any manual configuration steps beyond `git config
      user.name` and `user.email`.
- [ ] Error messages in `cmd_verify` and `cmd_register` name the file path
      and the expected vs. actual hash. Vague "verification failed" messages
      are not acceptable in a trust tool.

---

## Licensing and Provenance

- [ ] `LICENSE` (MIT) is present and unmodified at the repo root.
- [ ] `src/provenance.py` contains no third-party code that would require a
      different license. It is entirely original and stdlib-only in the PoC.
- [ ] `schemas/manifest.schema.json` is original work; no copyrighted schema
      template has been incorporated verbatim.
- [ ] All ADRs in `docs/adr/` cite sources for any external decision influence
      (C2PA spec version, JSON Schema draft, Tardos code parameters).
- [ ] `dependabot.yml` is configured to alert on dependency security advisories
      for pip and github-actions ecosystems.
- [ ] No dependency in the planned MVP stack (`cryptography`, `Pillow`,
      `NumPy`) has a license incompatible with MIT distribution. Confirmed:
      all three use Apache 2.0 or BSD-style licenses.
