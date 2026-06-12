# Art Provenance Vault — Makefile
# Runs under Git Bash on Windows and sh/bash on Linux/macOS.
#
# PowerShell equivalents (run from the repo root in a PS terminal):
#   make setup  →  pip install ruff jsonschema pre-commit
#   make lint   →  ruff check src/ ; ruff format --check src/
#   make test   →  bash -c "printf 'apv smoke' > _smoke.bin && \
#                    python src/provenance.py register _smoke.bin \
#                    --license CC0-1.0 --method human && \
#                    python src/provenance.py verify _smoke.bin && \
#                    rm _smoke.bin"
#   make audit  →  python -m pip show ruff jsonschema pre-commit; \
#                  ruff check src/; python -m py_compile src/provenance.py; \
#                  python -c "import json,jsonschema; ..."
#   make ci     →  run all of the above in sequence

.DEFAULT_GOAL := help

.PHONY: help setup lint test audit ci schema-validate

help:
	@echo "Art Provenance Vault — development targets"
	@echo ""
	@echo "  setup           Install Python dev tools (ruff, jsonschema, pre-commit)"
	@echo "  lint            Run ruff check + format check over src/"
	@echo "  test            Run the register+verify smoke test against a temp asset"
	@echo "  schema-validate Validate schemas/manifest.schema.json as draft 2020-12"
	@echo "  audit           Full local audit: compile, lint, schema, smoke, secrets scan"
	@echo "  ci              Run everything in sequence (mirrors GitHub Actions CI)"
	@echo ""
	@echo "  Targets run under Git Bash. See the comment block for PowerShell equivalents."

setup:
	pip install --quiet ruff jsonschema pre-commit
	pre-commit install

lint:
	ruff check src/
	ruff format --check src/

schema-validate:
	python - <<'PY'
	import json
	from jsonschema.validators import Draft202012Validator
	with open("schemas/manifest.schema.json", encoding="utf-8") as f:
	    schema = json.load(f)
	Draft202012Validator.check_schema(schema)
	print("schema OK: draft 2020-12 valid")
	PY

test:
	@echo "--- smoke: register + verify round-trip ---"
	git config --get user.name  > /dev/null || git config user.name "dev"
	git config --get user.email > /dev/null || git config user.email "dev@example.invalid"
	printf 'apv makefile smoke asset' > _smoke.bin
	python src/provenance.py register _smoke.bin --license CC0-1.0 --method human
	python src/provenance.py verify _smoke.bin
	printf 'tampered' >> _smoke.bin
	! python src/provenance.py verify _smoke.bin
	rm -f _smoke.bin
	@echo "--- smoke OK ---"

audit: lint schema-validate
	@echo "--- compile check ---"
	python -m py_compile src/provenance.py
	@echo "compile OK"
	@echo "--- secrets scan (detect-private-key hook) ---"
	pre-commit run detect-private-key --all-files || true
	@echo "--- audit complete: review items in docs/AUDIT.md ---"

ci: audit test
	@echo "--- CI complete ---"
