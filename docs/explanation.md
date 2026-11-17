# Explanation

Why Wilson is built this way. For task instructions see the [how-to guides](install.md); for verdict meanings see the [reference](phases.md).

## Why open source

A verification tool that judges citations is itself a judgment surface. If its logic, thresholds, and failure modes are not inspectable, it substitutes one black box for another. Auditability requires transparency, and a proprietary accountability tool carries a conflict of interest: the vendor decides what "verified" means and profits from the answer. Wilson's verdicts are meant to be argueable, and arguing requires seeing the machinery.

## Why the three-phase split

Existence, quotation, and coherence are three distinct failure modes with three distinct evidentiary standards:

- A citation can resolve to a real case that never says what the brief claims (real coordinates, dead weight).
- A quote can come from the right case with altered wording.
- A case can exist, be quoted accurately, and still not support the proposition.

A tool that collapses these into one "confidence score" cannot tell a court which kind of failure occurred. Wilson keeps the verdicts separate and named so each can be challenged on its own terms.

## Why the data boundary is this shape

Only citation strings are transmitted to CourtListener. If the local model is unavailable, Phase 3 is skipped by default. The semantic-search fallback that sends proposition text to CourtListener exists but is **opt-in and off by default** (Settings panel or `WILSON_EMBEDDINGS_FALLBACK=1`); turning it on is a deliberate crossing of the boundary, disclosed in every affected verdict. Document content is parsed locally, quotes are compared against retrieved opinion text, and Phase 3 runs against a local model by default. This is a deliberate legal-profession constraint: verification must be usable on material a firm cannot upload to a third party. The boundary is stated in every generated report so the audit trail itself records what left the machine (citation strings, plus proposition text only if you explicitly enable the semantic fallback).

## Why CourtListener and eyecite

Free Law Project's CourtListener is the only comprehensive, licensed-for-use corpus of US federal opinions with an open API, and eyecite is the same extraction library the corpus maintainers use. Building on them means Wilson inherits a maintained upstream rather than a private scrape, and its extraction behavior is inspectable and reproducible.

## Why Ollama for Phase 3

Coherence checking needs a language model, and any design that sends full opinion text plus a firm's propositions to a hosted API breaks the data boundary above. Local inference via Ollama keeps Phase 3 inside that boundary; the semantic-search fallback exists so the tool degrades honestly (`SKIPPED`) rather than secretly phoning home.

## Why the Mata v. Avianca proof is documented, not asserted

*Mata v. Avianca* is the canonical US sanctions case for filed AI fabrications; its fabricated citations are permanently described in Judge Castel's June 2023 order. Running Wilson against exactly those citations tests the tool on known-bad ground with a public answer key. The run is reproducible (`python test_mata_avianca.py`) and honestly labeled a proof-of-concept script, not part of the automated suite. Capability claims that cannot be re-run by a skeptic are not claims; they are marketing.

## Why "Wilson"

The volleyball in *Cast Away*: something real built under duress because survival required it. A thinking partner that keeps you sane when the system breaks down around you.
