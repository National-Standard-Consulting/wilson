"""
Wilson claims audit (16 Nov 26).

Every claim Wilson makes about itself gets an executable test here.
- PASS = claim verified against real pipeline code with recorded fixtures
         (network faked at the requests-module boundary; eyecite extraction,
         fuzzy matching, parsing, and report rendering are the real code).
- XFAIL(strict=True) = KNOWN DEFECT: the claim is currently false. The reason
  carries the defect id. When the defect is fixed the XPASS breaks CI,
  forcing the marker's removal -- defects cannot rot back silently.

Live claims needing a real CourtListener token (Mata 6/6, N-run verdict
stability, precision/recall on real filings) live in qa/CLAIMS_LEDGER.md.
"""
import copy
import json
import re
import pytest
from fastapi.testclient import TestClient

import api
import quote_verify
import coherence_check

client = TestClient(api.app)

ROE = "Roe v. Wade, 410 U.S. 113 (1973)"
BARE_COORDS = "410 U.S. 113"
MATA_FAKE = "Haller v. Blue Cross & Blue Shield Ins. Co., 1997 WL 683954 (S.D.N.Y. 1997)"
OPINION_HTML = ("<html><body><p>Held: The right of privacy, whether it be founded in the "
                "Fourteenth Amendment's concept of personal liberty, reaches a woman's "
                "decision to terminate a pregnancy.</p></body></html>")
REAL_QUOTE = ("The right of privacy, whether it be founded in the Fourteenth Amendment's "
              "concept of personal liberty")
PERTURBED_QUOTE = ("The right of privacy, whether founded in the Fourteenth Amendment concept "
                   "of personal liberty")
FAKE_QUOTE = "Every defendant shall receive a golden gavel upon conviction for state crimes."
TRUE_PROP = "The Constitution protects a woman's decision to terminate a pregnancy."


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = payload if isinstance(payload, str) else json.dumps(payload)

    def json(self):
        return copy.deepcopy(self._payload)


class FakeNetwork:
    """Requests-shaped fake. Routes = list of (method, url_substring, handler|payload|Exception).
    Handler: fn(url, kwargs) -> FakeResponse. Records every call."""
    import requests as _real
    exceptions = _real.exceptions  # code catches requests.exceptions.X

    def __init__(self, routes=None):
        self.routes = routes or []
        self.calls = []

    def _dispatch(self, method, url, **kw):
        self.calls.append({"method": method, "url": url, **kw})
        for m, sub, handler in self.routes:
            if m == method and sub in url:
                if isinstance(handler, Exception):
                    raise handler
                if callable(handler):
                    r = handler(url, kw)
                    return r if isinstance(r, FakeResponse) else FakeResponse(r)
                return FakeResponse(handler)
        raise AssertionError(f"unrouted {method} {url}")

    def get(self, url, **kw):
        return self._dispatch("GET", url, **kw)

    def post(self, url, **kw):
        return self._dispatch("POST", url, **kw)


def found(case_name="Roe v. Wade", cluster_id=111170):
    return [{"status": 200, "clusters": [{"id": cluster_id, "case_name": case_name}]}]


def standard_routes(lookup=None, opinion_status=200, blocked=False,
                    semantic_clusters=None, name_search=None,
                    ollama_down=False, generate=None):
    """Full world fixture: CourtListener + Ollama on one recorder."""
    def opinions(url, kw):
        if opinion_status != 200:
            return FakeResponse({"detail": "upstream error"}, status=opinion_status)
        return FakeResponse({"results": [{"id": 1, "html_with_citations": OPINION_HTML}]})

    def search(url, kw):
        params = kw.get("params") or {}
        if params.get("semantic"):
            if semantic_clusters is None:
                return FakeResponse({"results": []})
            return FakeResponse({"results": [{"cluster_id": c} for c in semantic_clusters]})
        if name_search is not None:
            return FakeResponse(name_search)
        return FakeResponse({"count": 0, "results": []})

    routes = [
        ("POST", "citation-lookup", lookup if lookup is not None else found()),
        ("GET", "/api/rest/v4/clusters/", lambda u, k: {"blocked": blocked}),
        ("GET", "/opinions/", opinions),
        ("GET", "/api/rest/v4/search/", search),
        ("GET", "api/rest/v4/", {}),  # health/token validation probe
        ("GET", "/api/tags", ConnectionError("refused") if ollama_down
         else {"models": [{"name": "test-model:latest"}]}),
        ("POST", "/api/generate", {"response": generate or json.dumps(
            {"verdict": "SUPPORTS", "confidence": "HIGH", "reasoning": "Holding on point."})}),
    ]
    return routes


@pytest.fixture
def world(monkeypatch):
    """Wire one shared fake network into api/quote_verify/coherence_check."""
    holder = {}

    def _world(routes):
        net = FakeNetwork(routes)
        monkeypatch.setattr(api, "http_requests", net)
        monkeypatch.setattr(quote_verify, "requests", net)
        monkeypatch.setattr(coherence_check, "requests", net)
        monkeypatch.setattr(coherence_check, "OLLAMA_MODEL", "test-model")
        # The embeddings fallback gates on a configured token; provide one so the
        # fallback path is actually exercised (on CI/dev boxes without .env it is None).
        monkeypatch.setattr(coherence_check, "CL_TOKEN", "test-token")
        holder["net"] = net
        return net

    yield _world
    holder.clear()


def verify(citation, quote=None, prop=None):
    body = {"citation": citation}
    if quote:
        body["quoted_text"] = quote
    if prop:
        body["proposition"] = prop
    r = client.post("/verify", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def cl_calls(net):
    return [c for c in net.calls if "courtlistener.com" in c["url"]]


# ================================================================ Phase 1

class TestPhase1Claims:
    def test_exists_verdict(self, world):
        world(standard_routes())
        assert verify(ROE)["phase1"]["verdict"] == "EXISTS"

    def test_fabricated_verdict_only_on_authoritative_miss(self, world):
        world(standard_routes(lookup=[{"status": 404, "error_message": "Not found"}]))
        assert verify(MATA_FAKE)["phase1"]["verdict"] == "FABRICATED"

    def test_misattributed_verdict_names_both_cases(self, world):
        world(standard_routes())
        out = verify("Smith v. Jones, 410 U.S. 113 (1973)")
        assert out["phase1"]["verdict"] == "MISATTRIBUTED"
        assert "Smith" in out["phase1"]["message"] and "Roe" in out["phase1"]["message"]

    def test_unreachable_database_is_error_never_fabricated(self, world):
        """The auditor's first duty: never accuse what it could not check."""
        world(standard_routes(lookup=ConnectionError("connection refused")))
        assert verify(ROE)["phase1"]["verdict"] == "ERROR"

    def test_timeout_is_error_never_fabricated(self, world):
        world(standard_routes(lookup=TimeoutError("read timeout")))
        assert verify(ROE)["phase1"]["verdict"] == "ERROR"

    @pytest.mark.xfail(strict=True, reason="DEFECT WIL-D2: bare coordinate citation with real "
                       "coordinates gets MISATTRIBUTED (false accusation) because case-name "
                       "matching runs against the raw coordinate string. Linear: file ticket.")
    def test_bare_coordinates_with_real_hit_verdict_exists(self, world):
        world(standard_routes())
        assert verify(BARE_COORDS)["phase1"]["verdict"] == "EXISTS"

    def test_low_confidence_name_match_produces_suggestion_not_verdict(self, world):
        world(standard_routes(name_search={"count": 1, "results": [{
            "cluster_id": 111170, "caseName": "Municipal Bond Review Act",
            "citation": ["1 F.2d 1 (3d Cir. 1923)"]}]}))
        out = verify("Roe versus Wade pregnancy privacy case")
        assert "phase1" not in out, "asserted a verdict on a low-similarity name match"


# ================================================================ Phase 2

class TestPhase2Claims:
    def test_exact_quote_is_100_match(self, world):
        world(standard_routes())
        assert verify(ROE, quote=REAL_QUOTE)["phase2"]["display_verdict"] == "100% MATCH"

    def test_perturbed_quote_is_fuzzy_not_100(self, world):
        world(standard_routes())
        dv = verify(ROE, quote=PERTURBED_QUOTE)["phase2"]["display_verdict"]
        assert dv.endswith("% MATCH") and dv != "100% MATCH"

    def test_fabricated_quote_is_not_found(self, world):
        world(standard_routes())
        assert verify(ROE, quote=FAKE_QUOTE)["phase2"]["display_verdict"] == "NOT FOUND"

    @pytest.mark.xfail(strict=True, reason="DEFECT WIL-D1: opinion-fetch failure (ERROR) maps to "
                       "display_verdict NOT FOUND -- an unchecked quote is reported as a fabricated "
                       "quote. Linear: file ticket.")
    def test_unfetchable_opinion_is_not_reported_as_not_found(self, world):
        world(standard_routes(opinion_status=500))
        out = verify(ROE, quote=REAL_QUOTE)
        assert out["phase2"].get("display_verdict") != "NOT FOUND"


# ================================================================ Phase 3

class TestPhase3Claims:
    def test_supports_via_local_ollama(self, world):
        world(standard_routes())
        out = verify(ROE, prop=TRUE_PROP)
        assert out["phase3"]["verdict"] == "SUPPORTS"
        assert out["phase3"]["backend_used"] == "ollama"

    def test_does_not_support_via_local_ollama(self, world):
        world(standard_routes(generate=json.dumps(
            {"verdict": "DOES_NOT_SUPPORT", "confidence": "HIGH",
             "reasoning": "Opinion concerns privacy, not speech."})))
        assert verify(ROE, prop=TRUE_PROP)["phase3"]["verdict"] == "DOES_NOT_SUPPORT"

    def test_both_backends_down_degrades_to_skipped(self, world):
        """Responsibility claim: with no coherence backend the verdict is SKIPPED,
        never a substantive answer invented from nothing."""
        world(standard_routes(ollama_down=True))  # semantic search returns no results
        out = verify(ROE, prop=TRUE_PROP)
        assert out["phase3"]["verdict"] == "SKIPPED"

    def test_semantic_rank_fallback_discloses_backend(self, world):
        world(standard_routes(ollama_down=True, semantic_clusters=[111170, 9, 8]))
        out = verify(ROE, prop=TRUE_PROP)
        assert out["phase3"]["backend_used"] == "embeddings"
        assert out["phase3"]["verdict"] == "SUPPORTS"  # rank #1 of 3
        assert "not full opinion analysis" in out["phase3"]["reasoning"]


# ============================================================ Data boundary

class TestDataBoundaryClaims:
    def test_with_ollama_up_only_citation_strings_reach_courtlistener(self, world):
        net = world(standard_routes())
        out = verify(ROE, quote=REAL_QUOTE, prop=TRUE_PROP)
        assert out["phase1"]["verdict"] == "EXISTS"
        for call in cl_calls(net):
            blob = json.dumps({k: v for k, v in call.items()
                               if k in ("params", "json", "data")}, default=str)
            assert TRUE_PROP not in blob, f"proposition leaked to CourtListener at {call['url']}"
            assert REAL_QUOTE not in blob, f"quote leaked to CourtListener at {call['url']}"

    @pytest.mark.xfail(strict=True, reason="DEFECT WIL-D3: embeddings fallback PUTS THE PROPOSITION "
                       "ITSELF into CourtListener semantic search (q param) while the report footer "
                       "and docs claim document content never left the machine. Fix: opt-in + honest "
                       "footer. Linear: file ticket.")
    def test_no_document_derived_text_leaves_machine_on_any_path(self, world):
        net = world(standard_routes(ollama_down=True, semantic_clusters=[111170]))
        verify(ROE, prop=TRUE_PROP)
        for call in cl_calls(net):
            blob = json.dumps(call, default=str)
            assert TRUE_PROP not in blob, "proposition text left the machine via semantic fallback"


# ========================================================== Report integrity

class TestReportClaims:
    def _req(self, citation_text=ROE):
        return {"filename": "brief.pdf", "sha256": "a" * 64, "page_count": 3,
                "citations": [{"citation_text": citation_text,
                               "phase1_verdict": "EXISTS", "phase2_verdict": "100% MATCH",
                               "phase3_verdict": "SUPPORTS", "page": 2}]}

    def test_report_binds_sha256_and_filename(self):
        html = client.post("/report/generate", json=self._req()).text
        assert "a" * 64 in html and "brief.pdf" in html

    def test_report_deterministic_modulo_timestamp(self):
        strip = lambda s: re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "T", s)
        a = strip(client.post("/report/generate", json=self._req()).text)
        b = strip(client.post("/report/generate", json=self._req()).text)
        assert a == b

    def test_report_escapes_untrusted_citation_text(self):
        evil = 'Roe v. Wade, 410 U.S. 113 <img src=x onerror="alert(1)">'
        html = client.post("/report/generate", json=self._req(evil)).text
        assert "<img src=x" not in html, "untrusted citation text renders unescaped"
        assert "&lt;img" in html

    @pytest.mark.xfail(strict=True, reason="DEFECT WIL-D4: report never shows which Phase 3 "
                       "backend produced a verdict; an embeddings-rank SUPPORTS and an "
                       "opinion-reading SUPPORTS are indistinguishable on paper. Linear: file ticket.")
    def test_report_discloses_phase3_backend_per_verdict(self):
        req = self._req()
        req["citations"][0]["phase3_backend"] = "embeddings"
        html = client.post("/report/generate", json=req).text
        assert "embeddings" in html.lower()


# ============================================================ Upload portal

class TestUploadClaims:
    def test_oversize_upload_rejected_cleanly(self, monkeypatch):
        monkeypatch.setattr(api, "MAX_UPLOAD_SIZE", 100)
        r = client.post("/upload/parse", files={"file": ("x.txt", b"z" * 101, "text/plain")})
        assert r.status_code >= 400 and r.status_code < 500

    def test_empty_upload_does_not_crash(self):
        r = client.post("/upload/parse", files={"file": ("x.txt", b"", "text/plain")})
        assert r.status_code < 500

    def test_extension_mismatch_does_not_crash(self):
        r = client.post("/upload/parse",
                        files={"file": ("x.pdf", b"definitely not a pdf", "application/pdf")})
        assert r.status_code == 422, f"corrupt document must be 422 (client input), got {r.status_code}"
        assert "corrupted" in r.json()["detail"].lower() or "could not read" in r.json()["detail"].lower()


# ============================================================== Health

class TestHealthClaims:
    def test_health_names_each_backend_state(self, world):
        world(standard_routes(ollama_down=True))
        h = client.get("/health").json()
        assert "available" in h["phases"]["phase1_api"]
        assert h["phases"]["phase3"]["available"] is False


# ================================================ Input boundary (audit sweep)

class TestInputBoundaries:
    """Hostile-sweep follow-ups: unbounded or unvalidated client input on the
    report/batch surface, and a no-auth localhost tool's exposure defaults."""

    def test_batch_rejects_absurd_citation_count(self):
        r = client.post("/batch/stream",
                        json={"citations": [{"citation_text": f"x {i}"} for i in range(501)],
                              "depth": "full"})
        assert r.status_code == 422

    def test_report_requires_real_sha256_shape(self):
        req = {"filename": "brief.pdf", "sha256": "trust-me", "page_count": 1,
               "citations": [{"citation_text": ROE}]}
        r = client.post("/report/generate", json=req)
        assert r.status_code == 422, "forged hash shape accepted into forensic report"

    def test_report_rejects_header_injection_in_filename(self):
        req = {"filename": 'x.txt\r\nX-Evil: 1', "sha256": "a" * 64, "page_count": 1,
               "citations": [{"citation_text": ROE}]}
        r = client.post("/report/generate", json=req)
        assert r.status_code == 422
        assert "x-evil" not in str(r.headers).lower()
