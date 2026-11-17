# Wilson Claims Ledger (16 Nov 26)

Every claim Wilson makes about itself, and how it is evidenced. `tests/test_claims_audit.py` is the executable half; this file is the map. Fixture tests fake only the requests-module boundary: extraction (eyecite), fuzzy matching, parsing, SSE aggregation, and report rendering are the real shipped code.

## Verified (fixture-proven, in CI)

| # | Claim | Evidence |
|---|---|---|
| V1 | Phase 1 returns EXISTS / FABRICATED / MISATTRIBUTED, and MISATTRIBUTED names both cases | test_claims_audit TestPhase1Claims |
| V2 | **An unreachable or timing-out database produces ERROR, never an accusation of fabrication** | test_unreachable_database_is_error_never_fabricated, test_timeout_is_error_never_fabricated |
| V3 | Name-based fallback with low similarity yields a suggestion, never a verdict | test_low_confidence_name_match_produces_suggestion_not_verdict |
| V4 | Phase 2 exact quote = 100% MATCH; perturbed = fuzzy < 100; fabricated = NOT FOUND | TestPhase2Claims |
| V5 | Phase 3 returns the local model's verdict, backend-labeled `ollama` | TestPhase3Claims |
| V6 | With no coherence backend at all, Phase 3 = SKIPPED; nothing is invented | test_both_backends_down_degrades_to_skipped |
| V7 | Semantic-rank fallback discloses "not full opinion analysis" in the trace | test_semantic_rank_fallback_discloses_backend |
| V8 | With Ollama up, only citation strings reach CourtListener (proposition and quote payloads proven absent) | TestDataBoundaryClaims |
| V9 | Report binds SHA-256 + filename, is deterministic modulo timestamp, and HTML-escapes untrusted citation text (injection test) | TestReportClaims |
| V10 | Upload portal rejects oversize cleanly; empty and corrupted documents return 4xx with user-actionable messages, never 500 | TestUploadClaims (corrupt-PDF-500 defect found and fixed 16 Nov) |
| V11 | /health reports per-backend availability, not a blanket green | TestHealthClaims |

## Known defects (strict-xfail in the suite; each has a Linear ticket)

| ID | Claim affected | Defect |
|---|---|---|
| ~~WIL-D1~~ | **FIXED 17 Nov** (defect-wil-d1-d2): unchecked quote now displays UNVERIFIED; test promoted from xfail to strict pass. |  |
| ~~WIL-D2~~ | **FIXED 17 Nov** (defect-wil-d1-d2): bare coordinates are now EXISTS with a disclosed "no case name supplied" note; name comparison runs only when a name claim exists. |  |
| WIL-D3 | "Document content never left this machine" | The Phase 3 embeddings fallback sends the proposition itself to CourtListener semantic search. The report footer and privacy docs are false on that path. Fix = opt-in fallback + honest footer (product decision pending). |
| ~~WIL-D4~~ | **FIXED 17 Nov** (defect-d4-d6-minors): report rows and the batch UI disclose the Phase 3 backend (embeddings and prose-fallback carry explicit weaker-evidence wording); xfail promoted. |  |
| WIL-D5 | Batch depth "quotes" | `/batch/stream` always passes `quoted_text=None`: batch quote verification is a no-op label. Docs corrected 16 Nov; code needs the feature or the option removed. |
| ~~WIL-D6~~ | **FIXED 17 Nov** (defect-d4-d6-minors): Phase 3 options now temperature 0.0 + seed 1234; test asserts the sampling config. |  |

## Live-only claims (need a CourtListener token; harness ready, execution blocked)

| # | Claim | Test to run when token is available |
|---|---|---|
| L1 | Mata v. Avianca 6/6 | `python test_mata_avianca.py` against live API; expect 3 FABRICATED / 2 MISATTRIBUTED / 1 EXISTS |
| L2 | Verdict stability: same citation N=10 runs, identical verdicts | Script: loop /verify over the golden set, diff verdicts; run twice (morning/evening) |
| L3 | Precision/recall on real filings | Golden set from the Charlotin DB (CC BY 4.0): ~50 known-bad citations + matched controls; report per-phase precision/recall, not a headline number |
| L4 | Blocked-opinion privacy skip on a real flagged cluster | fixture-tested (V-adjacent); live confirmation pending |

## What "reliably, repeatably, responsibly" means in this ledger

- Reliably = the failure-mode tests (V2, V6, V10): the tool must degrade to explicit ERROR/SKIPPED/4xx, never to a confident wrong verdict.
- Repeatably = V9 determinism + WIL-D6 fixed (temperature 0, seed 1234); L2 empirical stability still runs at token time.
- Responsibly = V8/data boundary (WIL-D3 is the open violation), V7 disclosure, and the privacy-flag behavior.

A claim with no test in this file and no row above does not get published in README, docs, reports, or posts.

## Hostile code sweep (16 Nov 26, GLM-4.6 + DeepSeek-V3, per-file chunks)

Adjudicated against live code; noise rejected (SSRF-on-hardcoded-URL, CSV path traversal via DataFrame equality, health-mask and None-name crash claims were false). Confirmed findings fixed same day on `release-prep`:

| Fix | Finding |
|---|---|
| Commit "input bounds and exposure defaults" | Batch endpoint accepted unbounded citation lists; report endpoint accepted any string as the forensic SHA-256 and any string as filename (header-injection crash). Now: max 500 batch entries, `^[0-9a-fA-F]{64}$` hash, sanitized filename. Tests in TestInputBoundaries. |
| Same commit | Install docs instructed `--host 0.0.0.0`: this tool has no auth; anyone reaching the port can read your token. Docs now default to 127.0.0.1 with an explicit exposure warning. |
| Same commit | Setup scripts echoed the CourtListener token to the console; now masked (`read -rs`, SecureString). |
| Same commit | Windows uninstaller killed every `python` process on the machine; now scoped to Wilson's own interpreter path. |

Re-checked and found already-correct (sweep claims rejected): fail-closed ERROR verdicts on API/auth failure (proven by V2), case-name default guards, CSV lookup is in-memory equality.

Deferred minors (NAT-695) resolved 17 Nov on defect-d4-d6-minors: `.env` read-modify-write now file-locked (fcntl/msvcrt); opinion truncation disclosed in Phase 3 reasoning + `opinion_truncated` flag; prose-fallback labeled `ollama(prose-fallback)`, LOW cap, weaker-evidence wording; proposition-suggestion fallback labeled LOW with edit-before-use note. **Still deferred:** bulk CSV checksum -- CourtListener publishes no stable checksum for the daily files and S3 ETags are multipart (not MD5); revisit if they publish one.
