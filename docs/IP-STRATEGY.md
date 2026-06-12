# IP-Protection Strategy — Art Provenance Vault

> **This document describes a design strategy, not legal advice.** Nothing
> here constitutes legal counsel. Laws differ by jurisdiction, evolve rapidly
> in the AI-art space, and the specific facts of any work and any dispute are
> ultimately what a court or registrar weighs. Consult qualified IP counsel
> before relying on any of this for commercial or litigation purposes.

---

## The Problem This Strategy Solves

An AI-assisted artist today faces a compounding vulnerability: the visible
signature can be cropped off, the metadata can be stripped in one command, the
AI model has no memory of the creation event, and no authoritative external
record proves the human's involvement at the moment of creation. By the time a
dispute arises, the only evidence is the creator's word against an empty file.

This strategy — the spine of Art Provenance Vault — layers five interlocking
pillars so that stripping *any one* protection does not eliminate the claim.
Each pillar addresses a different failure mode; together they produce a
tamper-evident, multi-witness provenance record that is designed to survive
a hostile environment.

---

## The Five-Pillar Protection Stack

### Pillar 1 — Invisible / Robust Watermark (Fallback Layer)

The visible watermark (signature, frame, credit) is the first thing an
infringer removes. The invisible watermark is the fallback that survives that
removal — embedded in the signal itself, not in the wrapper.

APV's four-stage watermark pipeline operates in escalating depth:

| Stage | Technique | Robustness |
|-------|-----------|------------|
| 1 | XMP/EXIF/PNG-text metadata pointer | Cooperative platforms only; stripped by any re-encode |
| 2 | Spatial LSB embedding (key-seeded, ECC-coded) | Survives lossless copying; not JPEG or resizing |
| 3 | Frequency-domain (DCT/DWT) spread-spectrum | Survives moderate compression and mild resizing |
| 4 | Per-recipient multivariant tracing | Identifies the specific licensed copy that leaked |

Honest limits are documented in full in [ARCHITECTURE.md](ARCHITECTURE.md)
(Layer 5). No invisible watermark today reliably survives a determined,
technically skilled attacker. The pipeline's real value is: (a) catching the
careless majority who strip metadata but do not reprocess the signal, and (b)
generating *traceable copy records* that are contractually actionable even
when forensic evidence would be weak in court. The manifest ledger is the
strong claim; watermarks are the tracing aid.

### Pillar 2 — Blockchain / Public Ledger (Permanent, Undeletable Timestamp)

A creation claim with no independent witness is only as durable as the
platform hosting it. Pillar 2 is that independent witness: a public ledger
entry that permanently ties a work's hash to a timestamp, anchored outside
any single company or jurisdiction.

**Mechanism.** Periodically (daily by default), APV computes the Merkle root
of all manifest hashes committed since the last anchor and publishes that root
to a public chain or transparency log. The anchor is a single small
transaction; no artwork data, no personal data, and no per-work cost goes
on-chain. Yet the result is a third-party-verifiable timestamp that cannot be
silently deleted or altered after the fact.

**Chain options.** APV is chain-agnostic by design:

- *Established chains* — Ethereum, Polygon, and similar EVM chains provide
  mature tooling, global distribution, and legal recognition in several
  jurisdictions. OpenTimestamps attestations against Bitcoin are a
  zero-cost, well-audited alternative.
- *Purpose-built chain* — 0thernes's longer-term research track is an
  art-provenance-specific chain optimized for manifest anchoring, governance
  by creators, and permanence guarantees beyond the economics of a
  general-purpose chain. Nothing in layers 1–5 depends on it; the system is
  fully functional and independently verifiable with git + SHA-256 alone
  until that chain is ready.

The `ledger_anchor` object in the manifest schema (see
[schemas/manifest.schema.json](../schemas/manifest.schema.json)) records
the chain, transaction or Merkle reference, and anchor timestamp for each
published root.

**What this gives.** A Pillar-2 anchor means: even if the git repository is
taken down, the GitHub account is suspended, and the artist's hard drives are
destroyed, a blockchain record still exists proving that a specific manifest
hash existed at a specific moment in time. That record is permanent by the
design of the chain, not by any company's continued good will.

### Pillar 3 — Extensive Per-File Metadata (Context and History for Legal Contests)

File identity is not enough. Copyright disputes turn on *who contributed
what, and when*. Pillar 3 is the contemporaneous evidentiary record: every
work carries a structured manifest that answers those questions in a signed,
tamper-evident document at the moment of creation.

The APV manifest captures:

- **Content identity** — SHA-256 of the exact bytes; survives any rename or
  platform move.
- **Creation chain** — model name and version, prompt text or hash (for
  trade-secret prompts), parent works (img2img sources, composited elements,
  LoRA fine-tunes), and the sequence of tools used.
- **Human contribution declaration** — a contemporaneous, free-text statement
  by the creator describing their specific human authorship acts: the
  selection decisions, compositional choices, editing steps, and approvals.
  Signed with the manifest. A *contemporaneous* declaration made before any
  dispute arose is categorically stronger evidence than a *retroactive* one.
- **Human attestations** — structured records of each human approval layer
  (see Pillar 4), including actor identity, action taken, and timestamp.
- **Intra-creator chain** — `chain.prev` links each manifest to the creator's
  previous one by SHA-256, forming a chain that survives export from git.
- **AI generation record** — the specific model, a reference to the prompt
  record, and generation parameters (seed, sampler, steps), so the generation
  event is fully reproducible and attributable.

The manifest schema is in [schemas/manifest.schema.json](../schemas/manifest.schema.json).
The chain structure means each work carries not just its own provenance but
its position in the creator's documented body of work.

### Pillar 4 — Human-Authorship Layering (2-of-3 Human Majority Strategy)

This pillar addresses the hardest problem in AI art: proving that a human
being exercised *genuine creative control* and was not merely pushing a button.

**The design.** Every registered work passes through three stages:

```
Stage A  ─  Human creative direction (initial selection, framing, concept)
Stage B  ─  AI generation (model produces output under human-specified parameters)
Stage C  ─  Human editing and approval (curation, retouching, compositional changes)
```

Stages A and C are *human* stages. Stage B is the machine stage. The human
wraps the AI — two human layers, one AI layer.

APV calls this the **2-of-3 human-majority structure**: two of the three
production stages are demonstrably human acts, and both human stages
bookend the AI stage rather than merely rubber-stamping a completed output.

**What the attestation records.** Each human stage produces a signed
attestation entry in the manifest's `human_attestations` array:

- *Layer 1 (pre-generation):* Who directed the generation, what creative
  choices they made, which parameters or prompt they specified.
- *Layer 2 (post-generation):* Who reviewed the output, what edits or
  selections they made, and their explicit approval of the final work.

The attestations are timestamped and signed. Script-assisted tooling (batch
processing, automation) does not disqualify a human attestation as long as
*a human still acted* — reviewed, made a judgment, and approved. The
distinction is human judgment versus fully automated pipeline.

#### Legal reality check — what the "2-of-3" framing does and does not mean

The 2-of-3 majority is a *design heuristic*, not a legal threshold.

**The governing legal standard in the US** is human creative control, judged
on its qualitative substance — not on a ratio or a vote count. The Copyright
Office and courts ask: did a human being exercise creative control sufficient
to make the work the product of human authorship? The specific question is
whether the human's contributions — selection, arrangement, expression,
editing — are original and attributable to human creativity, not merely
instructing a machine to produce an output.

**The current US posture.** In *Thaler v. Perlmutter* (D.D.C. Aug. 2023,
affirmed D.C. Cir. March 2025), the courts held that works generated entirely
by an AI system with no human author cannot be registered for copyright: the
Copyright Act has always required a human author. The Copyright Office has
confirmed this position in its 2023 guidance on AI-generated works and in its
February 2023 Zarya of the Dawn decision: AI-generated elements are not
copyrightable, but human-authored elements in the same work *can* be, and
the human-authored portions may be registered while AI-generated portions
are excluded or disclosed.

The dispositive question is not a percentage of the process that was human,
but the *nature and substance of the human contribution*. A human who makes
a single genuinely creative selection or arrangement that is original
expression may have a protectable claim on that contribution. A human who
only types a prompt and accepts the output without further creative
intervention has a weaker claim — courts and the Copyright Office have
consistently emphasized that sufficient human creative control is determined
case-by-case on the facts of each work.

**What the 2-of-3 structure actually does.** It is not a magic formula that
guarantees copyright. What it does — and this is where its real legal value
lies — is:

1. **Produce auditable evidence.** Each human stage leaves a signed,
   timestamped attestation in the manifest before any dispute arises.
   That contemporaneous record is far harder to challenge than retroactive
   testimony.
2. **Demonstrate genuine bookending.** Two wrapped human stages are stronger
   evidence of creative control than a single post-hoc approval, because
   they show the human shaped both the direction (pre-generation) and the
   final form (post-generation).
3. **Support a qualitative claim.** When a registrar or court assesses the
   human contribution, the attestation chain gives them concrete, documented
   acts to evaluate — not a vague assertion.

The honest summary: **this system's real legal value is the tamper-evident
provenance record it creates, not the ratio of human to AI stages.** Treating
"2-of-3" as a threshold that automatically confers copyright would be a
misreading of current law. Treating it as a disciplined way to generate
auditable human-authorship evidence is what it is actually designed to do.

### Pillar 5 — Public Repo as Durable, Decentralized Storage

A provenance record in a private database is only as durable as the company
running it. Pillar 5 makes the ledger itself distributed and permanent: the
vault is a public git repository (e.g., on GitHub) where the provenance
record lives openly, is cloneable by anyone, and survives any single
platform's failure.

**Why this matters.** Every `git clone` is a complete replica of the ledger.
A vault with forks held by collaborators, archivists, or CI services cannot
be silently altered — any rewrite of history produces a divergent hash chain
that independent clones expose. For AI artists whose work is contested, this
means the provenance record is not in anyone's control but the community's.

**Web3 spirit, git mechanics.** The vault is not a blockchain, but it shares
the key property that makes blockchain ledgers valuable: the record does not
depend on any one authority's continued goodwill. GitHub's Terms of Service
allow content removal; the manifest is small, widely cloned, and survives
platform loss. (Assets — the large image files — live in content-addressed
storage separate from git, per the architecture; the manifest is the durable
record, not the file itself.)

**Combined with Pillar 2**, public git replication and blockchain anchoring
create a two-layer durability guarantee: distributed clones protect against
ledger alteration, and the chain anchor protects against total ledger
disappearance.

---

## How the Pillars Interlock

Each pillar is independently useful and independently replaceable. Their
combination is what makes the system robust:

| Threat | Primary defense | Fallback |
|--------|-----------------|---------|
| Visible signature stripped | Pillar 1 invisible watermark | Pillar 3 manifest (out-of-band) |
| Metadata stripped from file | Pillar 3 manifest in vault | Pillar 2 blockchain timestamp |
| Disputed creation date | Pillar 2 anchor timestamp | Pillar 3 git commit timestamp |
| Disputed human authorship | Pillar 4 attestation chain | Pillar 3 human_contribution declaration |
| Vault hosted repo taken down | Pillar 5 clone distribution | Pillar 2 anchor (hash survives) |
| "You just pushed a button" claim | Pillar 4 structured attestations | Pillar 3 prompt + tool records |

---

## What APV Does and Does Not Do

**What APV does:**
- Generates contemporaneous, signed, tamper-evident provenance records.
- Creates auditable evidence of human creative involvement at each stage.
- Anchors records to a public ledger for third-party timestamp verification.
- Enables leak tracing via per-recipient watermark variants.
- Provides the evidentiary infrastructure to support an authorship claim.

**What APV does not do:**
- Certify that any work is copyrighted. Copyright eligibility is determined
  by law and adjudicated by courts and registration bodies, not by this
  system.
- Adjudicate the *degree* of human contribution. APV records claims; it does
  not score them.
- Transfer rights. The manifest records a license offer; it does not itself
  transfer intellectual property.
- Guarantee any specific legal outcome in any jurisdiction.

---

## Cross-References

- Architecture (six-layer technical stack): [ARCHITECTURE.md](ARCHITECTURE.md)
- Manifest schema (human_attestations, ai_generation, ledger_anchor): [schemas/manifest.schema.json](../schemas/manifest.schema.json)
- Legal landscape and design implications: [LEGAL-NOTES.md](LEGAL-NOTES.md)
- Watermark robustness details: [ARCHITECTURE.md](ARCHITECTURE.md) Layer 5
- Roadmap for phased implementation: [ROADMAP.md](ROADMAP.md)
