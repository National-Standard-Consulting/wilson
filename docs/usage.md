# Using Wilson (how-to)

Wilson runs as a local web app at `http://localhost:8000` once started (see [installation](install.md)).

## Verify one citation

1. Open the home page.
2. Paste the citation, optionally with a case name and the proposition it is cited for.
3. Watch the phases stream: existence, quote verification (if you supplied a quote), coherence (if you supplied a proposition).
4. Read the verdicts; what each means is in [phases and verdicts](phases.md).

Tip: providing the proposition is what unlocks Phase 3. Without it Wilson checks that the case exists and the quote is real, but not whether the case actually says what the brief claims.

## Verify a whole document (upload portal)

1. Open `/upload`.
2. Drop a PDF, DOCX, or TXT file. Wilson extracts every legal citation it finds.
3. Review the extracted citations and the proposed propositions; edit or add propositions before running.
4. Choose depth: existence only, or the full three-phase pipeline. (Batch verification checks existence only; per-citation quote verification requires a single citation input. See `qa/CLAIMS_LEDGER.md` WIL-D5.)
5. Run the batch and watch results stream in per citation.

Document content is parsed locally; only citation strings go to CourtListener, except on the Phase 3 semantic-fallback path (see [explanation](explanation.md)), which sends the proposition text to CourtListener search.

## Generate a report

After a batch run, generate the HTML verification report: a printable, self-contained document with per-citation verdicts, a summary block by verdict class, a data-boundary statement, and a SHA-256 of the source document so the report can be tied back to the exact file that was audited.

## Configure without touching .env

The gear icon on any page opens settings: theme (dark/light/high contrast/auto), font size, layout density, Ollama host/model, CourtListener token, and bulk-CSV status.

## Reproduce the Mata v. Avianca proof of concept

```bash
# .env must contain a valid COURTLISTENER_TOKEN
python test_mata_avianca.py
```

The script runs the Phase 1 pipeline against the six citations from the sanctioned Mata v. Avianca filing and prints per-citation verdicts. Expected: three `FABRICATED`, two `MISATTRIBUTED`, one `EXISTS`.
