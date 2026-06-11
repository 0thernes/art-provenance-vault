# Legal Landscape — Research Notes

> **Status: research notes, not legal advice.** This document is a working
> map of the licensing and copyright terrain APV operates in, compiled to
> guide product design. Nothing here has been reviewed by counsel. Before any
> commercial launch, these notes must be replaced by an actual legal opinion
> in each target jurisdiction.

## 1. Why licensing is a first-class manifest field

A provenance record that says *who made this* but not *what you may do with
it* solves half the problem. The `license` field in the manifest is therefore
mandatory, machine-readable, and signed along with everything else — making
the license offer itself non-repudiable and timestamped.

## 2. SPDX as the spine

- [SPDX license expressions](https://spdx.org/licenses/) are the
  machine-readable standard for naming licenses (`CC-BY-4.0`,
  `CC-BY-NC-SA-4.0 OR LicenseRef-APV-Commercial-1.0`, etc.).
- The manifest schema requires an SPDX expression string. Custom commercial
  terms use the SPDX `LicenseRef-` mechanism with the full terms stored as a
  hashed, referenced document — so even bespoke contracts are
  content-addressed and tamper-evident.
- Open question: SPDX expressions were designed for software; some art-market
  concepts (editions, exhibition rights, resale royalty) have no SPDX
  vocabulary. Likely answer: SPDX expression for the rights *family* +
  structured `terms` extension for art-specific clauses.

## 3. Creative Commons in an AI-art context

- CC licenses are the de facto standard for shareable art, well understood by
  platforms, and legally battle-tested.
- Friction points to track:
  - **NC ambiguity** — "non-commercial" is notoriously fuzzy; for AI training
    use it is essentially unlitigated territory.
  - **CC and training data**: CC licenses predate generative AI; whether
    training is "use" governed by the license, fair use, or a TDM
    (text-and-data-mining) exception varies by jurisdiction (EU DSM Art. 4
    opt-out vs. US fair-use litigation in progress).
  - CC's own "preference signals" work acknowledges the gap; APV manifests
    can carry an explicit training-permission flag (`ai_training: allowed |
    disallowed | conditional`) rather than overloading the license string —
    aligned with the C2PA `training-and-data-mining` assertion.

## 4. Commercial licensing terms

For paid licenses, the manifest references (by sha256) a terms document
covering, at minimum: scope (media, territory, duration, exclusivity),
sublicensing, derivative rights, credit requirements, and — relevant to
Layer 5 — the recipient's acknowledgment that their copy is individually
watermarked. Recording that acknowledgment in the signed license record is
what makes Stage 4 leak-tracing results *actionable* contractually
(termination for breach) even where they would be weak in court as forensic
evidence.

## 5. The AI-art copyright question (open, jurisdiction-dependent)

The hard, unresolved questions APV must remain agnostic about:

- **US:** The Copyright Office's position (Compendium + 2023–2025 guidance
  and the *Thaler* line of cases) is that purely machine-generated output is
  not copyrightable; works with sufficient human authorship are, with the
  AI-generated portions potentially excluded. Registration practice asks
  applicants to disclose AI use.
- **EU/UK:** EU law requires the author's "own intellectual creation"; the
  UK's s.9(3) CDPA computer-generated-works provision points the other way
  but its scope is debated.
- **Practical consequence for APV:** we cannot and do not certify that a
  registered work *is* copyrighted. What we can do — and what the design
  leans into — is create **contemporaneous, signed, tamper-evident evidence
  of the human contribution** (`creation.human_contribution`, prompt
  records, parent-work chains, editing actions). Whatever line each
  jurisdiction ultimately draws, the creator who can *prove* their process
  is in a categorically better position than one who cannot.

## 6. Adjacent regimes to track

- **EU AI Act** transparency obligations for AI-generated content labeling —
  APV manifests + C2PA export are a natural compliance vehicle.
- **Moral rights** (attribution/integrity) in droit-d'auteur jurisdictions —
  cannot be waived in some markets; manifest attribution helps honor them.
- **Right of publicity / likeness** issues in AI art are orthogonal to
  copyright but a major platform-liability driver; out of APV scope, worth a
  manifest flag eventually.
- **NFT precedent**: courts and markets learned the difference between a
  token and the rights to a work the hard way. APV's docs must always state
  plainly: *the manifest records claims and license offers; it does not
  itself transfer rights.*

## 7. Design implications adopted

1. `license` = SPDX expression, required, signed (schema-enforced).
2. AI-training permission is a separate explicit field, not inferred from
   the license.
3. Human-contribution declaration is free text + structured creation chain,
   never an APV-computed score.
4. Commercial terms documents are content-addressed (sha256) like assets.
5. All public-facing materials must carry the "records claims, not
   adjudications" disclaimer.
