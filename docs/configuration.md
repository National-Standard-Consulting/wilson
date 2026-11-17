# Configuration reference

All configuration lives in `.env` (copy `.env.example` to start), except display and runtime settings available in the in-app settings panel. Never commit `.env`.

## Environment variables

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `COURTLISTENER_TOKEN` | Yes | none | Free token from [courtlistener.com/sign-in](https://www.courtlistener.com/sign-in/). Used for citation lookup, opinion text, and semantic search. |
| `CITATIONS_CSV` | No | unset | Full path to a CourtListener bulk citations CSV. When set, Phase 1 existence checks run against the local ~18M-record file first. ~1.9 GB compressed download; see [install guide](install.md#optional-local-bulk-citation-data). |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama endpoint for Phase 3. |
| `OLLAMA_MODEL` | No | see `.env.example` | Model used for coherence checking. Pull it first: `ollama pull <model>`. |
| `OLLAMA_CONTEXT_SIZE` | No | model-dependent | Context window Wilson assumes for the configured model. |
| `PACER_USERNAME` / `PACER_PASSWORD` | No | unset | Reserved for the planned original-filing retrieval feature (see roadmap); currently unused. |

## Settings panel (in-app)

Theme (dark/light/high contrast/auto), font size, layout density, Ollama host and model, CourtListener token management, bulk-CSV status and update notification. Settings made here persist and override `.env` equivalents where they overlap.

## API endpoints (for programmatic use)

| Endpoint | Method | Purpose |
|---|---|---|
| `/verify` | POST | Single citation, all phases, single JSON response |
| `/verify/stream` | POST | Same, streamed per phase |
| `/batch/stream` | POST | Batch verification of extracted citations with propositions |
| `/batch/propositions` | POST | Proposition extraction for a parsed document |
| `/report/generate` | POST | Printable HTML report for a finished batch |
| `/upload/parse` | POST | Parse an uploaded PDF/DOCX/TXT and extract citations |
| `/health` | GET | Status check |

## Data sources

| Source | Purpose | License |
|---|---|---|
| [CourtListener](https://www.courtlistener.com) | Case lookup, full opinion text, semantic search | CC BY-ND |
| [Free Law Project Bulk Data](https://www.courtlistener.com/help/api/bulk-data/) | Local citation database (~18M records) | CC BY-ND |
| [eyecite](https://github.com/freelawproject/eyecite) | Citation extraction | BSD |
| [Charlotin AI Hallucination Cases Database](https://www.damiencharlotin.com/hallucinations/) | Reference dataset for verification scenarios | CC BY 4.0 (research use) |

Wilson does not republish case content; it performs local forensic analysis and returns verdicts.
