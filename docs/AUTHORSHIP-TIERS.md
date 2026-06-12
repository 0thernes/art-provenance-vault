# Authorship Tiers — mapping human authorship onto manifests

Companion to [CASE-STUDY-ARTIST-ZERO.md](./CASE-STUDY-ARTIST-ZERO.md) and
[IP-STRATEGY.md](./IP-STRATEGY.md). Defines the disclosure tiers a creator declares per work, and
how each maps onto the manifest schema. The canonical public statement for artist-zero lives at the
sibling site repo's `AUTHORSHIP.md`; this file is the legal/provenance mapping.

> Not legal advice. U.S. copyright protects human-authored expression and turns on the **substance
> of human creative control**, judged case by case — not on a numeric percentage. The system's value
> is producing an **auditable, honest record** of that control, which is strongest when it does not
> overclaim.

## The tiers

| Tier | Meaning | Typical works | What is claimed |
|---|---|---|---|
| **A — Solo human authorship** | Prompt is 100% human-written (zero AI input/editing); output is human-curated; any accompanying writing is 100% human | AI-art prompts (the prompt as original text) + articles/statements | The human expression + creative control: prompt-as-writing, selection/curation, arrangement, prose |
| **B — Hybrid / AI-assisted** | AI generates a draft; human directs (selection, sequence, edit) and rewrites accuracy-critical text in their own words | Films, period/accuracy-critical pieces | The human contributions: direction, selection, edit, sequence, human-rewritten text — not raw machine output |
| **C — Reference only** | Third-party or tool-default material used as reference | mood/reference assets | Nothing claimed as original |

## Mapping to `schemas/manifest.schema.json`

- **`authorship_tier`** (recommended addition): `"A" | "B" | "C"` — the declared tier for the work.
- **`ai_generation`**: present for Tiers A and B. For Tier A the prompt is the human-authored input
  (link the prompt text / CC corpus reference); the model is recorded as the rendering tool. For
  Tier B, record each tool used (e.g. GPT, Seedance 2.0, Grok Imagine).
- **`human_attestations[]`**: the concrete human acts.
  - Tier A — Layer 1: *prompt authored by human* (original text); Layer 2: *output selected/curated by human*.
  - Tier B — Layer 1: *direction / shot + sequence selection*; Layer 2: *human rewrite/edit of text or cut*.
- **`license`**: e.g. CC-BY-4.0 for the published Tier A prompt corpus; per-work otherwise.
- **`ledger_anchor`**: timestamp anchor, tier-independent.

## Worked example pointer

The fully worked Tier A manifest (DALL·E 3 render of a 100%-human CC-licensed prompt, two human
attestation layers) is in [CASE-STUDY-ARTIST-ZERO.md](./CASE-STUDY-ARTIST-ZERO.md) §4. A Tier B
example (a hybrid film: multiple tools, direction + rewrite attestations) is a good next addition.

## Why disclosure beats inflation

A manifest that honestly marks a film **Tier B** is more defensible than one that claims everything
as wholly human. Courts and registrars weigh the *nature* of the human contribution; a precise,
contemporaneous, signed record of exactly what the human did is the asset. Overclaiming is the risk;
honest tiering is the moat.
