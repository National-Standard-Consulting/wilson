# Wilson

> Wilson removes the advantage afforded to those who will lie.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://github.com/National-Standard-Consulting/wilson/actions/workflows/ci.yml/badge.svg)](https://github.com/National-Standard-Consulting/wilson/actions/workflows/ci.yml)

Wilson is an open-source AI reasoning auditor for legal citations. It verifies a citation against primary sources and then audits whether the cited case actually supports the proposition it was cited for, returning a documented evidence chain rather than a score.

An auditor you cannot audit is just another black box. Wilson is open because auditability requires transparency.

## Why this exists

Courts worldwide have recorded [2,306 decisions](https://www.damiencharlotin.com/hallucinations/) (database count as of 16 Nov 2026, covering Q2 2023 onward) in which a court found or implied that a party relied on AI-hallucinated content. Roughly two-thirds are US decisions. Every commercial response to this problem is proprietary and opaque. Wilson is the accountability layer that can be inspected, run with document content kept local, and argued with.

## Quickstart

**Windows (no developer tools needed):** download `Wilson-Setup-0.1.1.exe` from [Releases](https://github.com/National-Standard-Consulting/wilson/releases), run it, follow the first-launch wizard. It installs into your user folder, bundles its own Python runtime, and opens the web interface in your browser. You need a free [CourtListener API token](https://www.courtlistener.com/sign-in/).

**Linux / macOS:**

```bash
git clone https://github.com/National-Standard-Consulting/wilson.git
cd wilson
./setup.sh
```

Then open `http://localhost:8000`. Full requirements and troubleshooting: [installation guide](docs/install.md).

## Documentation

| If you want to... | Go to |
|---|---|
| Get Wilson running on your machine | [Installation guide](docs/install.md) (how-to) |
| Verify a citation, a quote, or a whole document | [Using Wilson](docs/usage.md) (how-to) |
| Look up a configuration option or environment variable | [Configuration reference](docs/configuration.md) (reference) |
| Understand what each verdict means | [Phases and verdicts](docs/phases.md) (reference) |
| Understand why it is built this way | [Explanation](docs/explanation.md) (explanation) |

## What it does, in one screen

Three phases, each with explicit verdicts:

1. **Existence.** Extracts citations with [eyecite](https://github.com/freelawproject/eyecite), checks them against CourtListener (optionally a local 18M-record bulk CSV). Verdicts: `FABRICATED` / `MISATTRIBUTED` / `EXISTS`.
2. **Quote verification.** Fetches the opinion and checks whether the quoted language actually appears, verbatim or approximately. Verdicts: `100% MATCH` / `XX% MATCH` / `NOT FOUND` / `UNVERIFIED` (could not check -- not a finding about the quote).
3. **Coherence.** Asks a local LLM via Ollama whether the cited case actually supports the proposition, with CourtListener semantic search as fallback. Verdicts: `SUPPORTS` / `DOES_NOT_SUPPORT` / `UNCERTAIN` / `SKIPPED`.

Privacy: only citation strings are sent to CourtListener (exception: if the local model is down, the Phase 3 semantic fallback sends the proposition text to CourtListener search). Document content stays on your machine. Wilson respects CourtListener's privacy-removal flags and skips phases for blocked opinions.

## Proof of capability

Wilson was run against the fabricated citations from *Mata v. Avianca* (1:22-cv-01461, S.D.N.Y.), the most sanctioned AI hallucination case in US legal history: all six citations in the offending filing were correctly classified (three fabricated, two misattributed to valid coordinates belonging to different cases, one legitimate). This is a documented proof-of-concept run, not part of the automated suite: `python test_mata_avianca.py` reproduces it and requires a CourtListener token. Sources: Judge Castel's sanctions order of 22 Jun 2023 and the [Charlotin database](https://www.damiencharlotin.com/hallucinations/) entry for the case.

## Current release

**v0.1.1:** three-phase pipeline, streaming web interface, document upload portal (PDF/DOCX/TXT batch verification with proposition review queue), settings panel, HTML verification reports, privacy-flag compliance. Tests run on every push in [CI](https://github.com/National-Standard-Consulting/wilson/actions).

Contributions welcome. Read [SECURITY.md](SECURITY.md) before reporting vulnerabilities, and open an issue before submitting a pull request.

## Who builds this

Wilson is developed by [National Standard Consulting LLC](https://github.com/National-Standard-Consulting), a Service-Disabled Veteran-Owned Small Business.

Named for the volleyball in *Cast Away*: something real built under duress because survival required it.

## License

Apache 2.0. See [LICENSE](LICENSE). Data sources and their licenses are listed in the [configuration reference](docs/configuration.md#data-sources).

*Wilson does not make decisions. It makes decisions auditable.*
