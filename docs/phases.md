# Phases and verdicts (reference)

## Pipeline

```
Input (citation text, case name, or uploaded document)
              |
    Citation Extraction (eyecite -- Free Law Project)
              |
+------------------------------------------+
|  PHASE 1: Existence Verification         |
|  - CourtListener API citation lookup     |
|  - Local bulk CSV (~18M records)         |
|  - Case name fuzzy match (75% min)       |
|  - Privacy flag check (blocked field)    |
|  -> FABRICATED / MISATTRIBUTED / EXISTS  |
+------------------------------------------+
              | (if EXISTS and not blocked)
+------------------------------------------+
|  PHASE 2: Quote Verification             |
|  - Fetch full opinion text               |
|  - Exact + fuzzy string match            |
|  -> 100% MATCH / XX% MATCH / NOT FOUND   |
+------------------------------------------+
              | (if proposition provided)
+------------------------------------------+
|  PHASE 3: Coherence Checking             |
|  Primary: Ollama local LLM               |
|  Fallback: CourtListener semantic search |
|  -> SUPPORTS / DOES_NOT_SUPPORT /        |
|     UNCERTAIN / SKIPPED                  |
+------------------------------------------+
              |
  Full Reasoning Trace
```

## Phase 1 -- Existence

Checks that a case exists at the cited coordinates and that the coordinates belong to the cited case.

| Verdict | Meaning |
|---|---|
| `FABRICATED` | No case exists at the cited reporter/volume/page coordinates. |
| `MISATTRIBUTED` | Real coordinates, but they belong to a different case than the one named. |
| `EXISTS` | Citation resolves to the named case. |

Mechanics: extraction via eyecite; lookup against the local bulk CSV when configured, otherwise the CourtListener API; name-based fuzzy fallback when only a case name is given, with confidence thresholding and "did you mean?" suggestions.

## Phase 2 -- Quote verification

Checks whether quoted language actually appears in the opinion.

| Verdict | Meaning |
|---|---|
| `100% MATCH` | Quotation appears verbatim. |
| `XX% MATCH` | Approximate match; paraphrase presented as quotation, or minor alteration. The percentage is the fuzzy similarity score. |
| `NOT FOUND` | Quoted language does not appear in the opinion. |

## Phase 3 -- Coherence

Checks whether the cited case actually supports the proposition it is cited for.

| Verdict | Meaning |
|---|---|
| `SUPPORTS` | The opinion holds or states something that supports the proposition. |
| `DOES_NOT_SUPPORT` | The opinion does not support the proposition (includes right case, wrong proposition). |
| `UNCERTAIN` | The checking model could not reach a reliable verdict. |
| `SKIPPED` | No proposition supplied, coherence infrastructure unavailable, or the opinion is privacy-blocked. |

Primary backend is a local Ollama model (opinion text never leaves the machine). Fallback is CourtListener semantic search.

## Cross-phase states

| State | Meaning |
|---|---|
| `blocked` (Phases 2-3 skipped) | The opinion carries a CourtListener privacy-removal flag. Wilson honors it by design and notes it in results. |
