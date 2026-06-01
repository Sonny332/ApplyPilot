from __future__ import annotations

import sqlite3

import pytest

import applypilot.scoring.scorer as scorer


def _sample_profile() -> dict:
    return {
        "experience": {
            "target_role": "Senior Software Engineer",
            "years_of_experience_total": "8",
        },
        "work": [
            {
                "position": "Senior Software Engineer",
                "technologies": ["Python", "React", "AWS", "Kubernetes"],
            }
        ],
        "skills": [
            {"name": "Languages", "keywords": ["Python", "Java", "TypeScript"]},
            {"name": "Frameworks", "keywords": ["React", "FastAPI", "Angular"]},
            {"name": "Cloud", "keywords": ["AWS", "Docker", "Kubernetes"]},
        ],
    }


def _sonny_energy_profile() -> dict:
    return {
        "experience": {
            "target_role": "Energy Analyst / Energy Engineer / Building Performance Analyst",
            "years_of_experience_total": "5",
        },
        "work": [
            {
                "position": "Energy Analyst & Business Analyst",
                "technologies": [
                    "HVAC",
                    "building systems",
                    "energy efficiency",
                    "energy modeling",
                    "utility tariff analysis",
                    "financial modeling",
                    "facilities operations",
                ],
            },
            {
                "position": "Renewable Energy Engineer",
                "technologies": [
                    "ANSYS Fluent",
                    "MATLAB",
                    "AutoCAD",
                    "thermodynamics",
                    "heat transfer",
                    "fluid mechanics",
                ],
            },
        ],
        "skills": [
            {
                "name": "Energy and Building Systems",
                "keywords": [
                    "HVAC",
                    "building systems",
                    "energy efficiency",
                    "energy modeling",
                    "utility tariff analysis",
                    "financial modeling",
                    "facilities operations",
                ],
            },
            {
                "name": "Engineering Tools",
                "keywords": [
                    "ANSYS Fluent",
                    "MATLAB",
                    "AutoCAD",
                    "thermodynamics",
                    "heat transfer",
                    "fluid mechanics",
                ],
            },
        ],
    }


def _calibrated_score_for_energy_job(title: str, description: str, llm_score: int = 3) -> int:
    scoring_profile = scorer._build_scoring_profile(_sonny_energy_profile())
    job = {"title": title, "full_description": description}
    baseline = scorer._compute_deterministic_baseline(scoring_profile, job)
    final_score, _ = scorer._apply_score_calibration(
        baseline=baseline,
        llm_score=llm_score,
        confidence=0.95,
        matched_skills=baseline["matched_skills"],
        missing_requirements=baseline["missing_requirements"],
        job_context=f"{title}\n{description}",
    )
    return final_score


def _make_jobs_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE jobs (
            url TEXT PRIMARY KEY,
            title TEXT,
            site TEXT,
            location TEXT,
            full_description TEXT,
            fit_score INTEGER,
            score_reasoning TEXT,
            scored_at TEXT,
            exclusion_reason_code TEXT,
            exclusion_rule_id TEXT,
            excluded_at TEXT,
            score_error TEXT,
            score_retry_count INTEGER DEFAULT 0,
            score_next_retry_at TEXT
        )
        """
    )
    conn.commit()
    return conn


def _insert_job(conn: sqlite3.Connection, url: str = "https://example.com/job/1") -> None:
    conn.execute(
        """
        INSERT INTO jobs (
            url, title, site, location, full_description, fit_score, score_reasoning,
            scored_at, exclusion_reason_code, exclusion_rule_id, excluded_at,
            score_error, score_retry_count, score_next_retry_at
        ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL)
        """,
        (url, "Backend Engineer", "ExampleCo", "Remote", "Python and APIs"),
    )
    conn.commit()


def test_parse_score_response_requires_valid_json_object() -> None:
    with pytest.raises(scorer.ScoreResponseParseError) as exc:
        scorer._parse_score_response("Score maybe 6 based on requirements")
    assert exc.value.category in {"missing_json_object", "invalid_json"}


def test_parse_score_response_accepts_strict_json_schema() -> None:
    parsed = scorer._parse_score_response(
        """
        {
          "score": 8,
          "confidence": 0.84,
          "why_short": "Strong backend skill overlap",
          "matched_skills": ["python", "react"],
          "missing_requirements": ["graphql"],
          "reasoning": "Strong overlap with backend stack."
        }
        """
    )
    assert parsed["score"] == 8
    assert parsed["confidence"] == pytest.approx(0.84)
    assert parsed["why_short"] == "Strong backend skill overlap"
    assert parsed["matched_skills"] == ["python", "react"]
    assert parsed["missing_requirements"] == ["graphql"]


def test_score_job_retries_inline_until_it_gets_valid_json(monkeypatch) -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.calls = 0
            self.responses = [
                "this is not json",
                '{"score": 8, "confidence": 0.9, "matched_skills": ["python"], "missing_requirements": [], "reasoning": "Strong fit"}',
            ]

        def chat(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.calls += 1
            return self.responses.pop(0)

    fake_client = _FakeClient()
    monkeypatch.setattr(scorer, "get_client", lambda: fake_client)
    monkeypatch.setattr(scorer, "SCORE_ATTEMPT_BACKOFF_SECONDS", 0.0)

    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    result = scorer.score_job(
        resume_text="Senior software engineer with Python and React.",
        job={
            "title": "Senior Backend Engineer",
            "site": "ExampleCo",
            "location": "Remote",
            "full_description": "Requirements: Python, REST APIs, AWS.",
        },
        scoring_profile=scoring_profile,
    )

    assert fake_client.calls == 2
    assert result["score"] > 0
    assert "parse_error_category" not in result
    assert result["llm_why_short"] == "Strong fit with clear overlap"
    assert result["llm_reasoning_full"] == "Strong fit"


def test_score_job_uses_normal_output_budget_for_gemini_thinking(monkeypatch) -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.kwargs = None

        def chat(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.kwargs = kwargs
            return (
                '{"score": 8, "confidence": 0.9, "why_short": "Strong backend overlap", '
                '"matched_skills": ["python"], "missing_requirements": [], "reasoning": "Strong fit"}'
            )

    fake_client = _FakeClient()
    monkeypatch.setattr(scorer, "get_client", lambda: fake_client)

    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    scorer.score_job(
        resume_text="Senior software engineer with Python and React.",
        job={
            "title": "Senior Backend Engineer",
            "site": "ExampleCo",
            "location": "Remote",
            "full_description": "Requirements: Python, REST APIs, AWS.",
        },
        scoring_profile=scoring_profile,
    )

    assert fake_client.kwargs["max_output_tokens"] == 3072


def test_parse_scoring_llm_models_adds_gemini_prefix(monkeypatch) -> None:
    monkeypatch.setenv(
        "SCORING_LLM_MODELS",
        "gemini-3.1-flash-lite, gemini/gemini-3.5-flash, ,gemini-3-flash",
    )

    assert scorer._scoring_llm_models() == [
        "gemini/gemini-3.1-flash-lite",
        "gemini/gemini-3.5-flash",
        "gemini/gemini-3-flash",
    ]


def test_score_job_falls_back_to_next_scoring_model_on_429(monkeypatch) -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.models = []

        def chat(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.models.append(kwargs.get("model"))
            if len(self.models) == 1:
                raise RuntimeError("LLM request failed: 429 rate limit")
            return (
                '{"score": 8, "confidence": 0.9, "why_short": "Strong backend overlap", '
                '"matched_skills": ["python"], "missing_requirements": [], "reasoning": "Strong fit"}'
            )

    fake_client = _FakeClient()
    monkeypatch.setenv("SCORING_LLM_MODELS", "gemini-3.1-flash-lite,gemini-3.5-flash")
    monkeypatch.setattr(scorer, "get_client", lambda: fake_client)
    monkeypatch.setattr(scorer, "SCORE_ATTEMPT_BACKOFF_SECONDS", 0.0)

    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    result = scorer.score_job(
        resume_text="Senior software engineer with Python and React.",
        job={
            "title": "Senior Backend Engineer",
            "site": "ExampleCo",
            "location": "Remote",
            "full_description": "Requirements: Python, REST APIs, AWS.",
        },
        scoring_profile=scoring_profile,
    )

    assert fake_client.models == ["gemini/gemini-3.1-flash-lite", "gemini/gemini-3.5-flash"]
    assert result["score"] > 0


def test_score_job_does_not_fallback_models_on_malformed_json(monkeypatch) -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.models = []

        def chat(self, *args, **kwargs):  # noqa: ANN002, ANN003
            self.models.append(kwargs.get("model"))
            return "this is not json"

    fake_client = _FakeClient()
    monkeypatch.setenv("SCORING_LLM_MODELS", "gemini-3.1-flash-lite,gemini-3.5-flash")
    monkeypatch.setattr(scorer, "get_client", lambda: fake_client)
    monkeypatch.setattr(scorer, "SCORE_ATTEMPT_BACKOFF_SECONDS", 0.0)

    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    result = scorer.score_job(
        resume_text="Senior software engineer with Python and React.",
        job={
            "title": "Senior Backend Engineer",
            "site": "ExampleCo",
            "location": "Remote",
            "full_description": "Requirements: Python, REST APIs, AWS.",
        },
        scoring_profile=scoring_profile,
    )

    assert fake_client.models == ["gemini/gemini-3.1-flash-lite"] * scorer.MAX_SCORE_ATTEMPTS_PER_JOB
    assert result["parse_error_category"] == "missing_json_object"


def test_engineering_fit_guardrail_blocks_bottom_bucket_without_hard_mismatch() -> None:
    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    job = {
        "title": "Senior Full-Stack Engineer (Java + React/Angular)",
        "full_description": (
            "Requirements: 5+ years software engineering experience. "
            "Strong Java, Python, React, AWS, and Kubernetes."
        ),
    }

    baseline = scorer._compute_deterministic_baseline(scoring_profile, job)
    final_score, _ = scorer._apply_score_calibration(
        baseline=baseline,
        llm_score=1,
        confidence=0.95,
        matched_skills=baseline["matched_skills"],
        missing_requirements=[],
        job_context=job["full_description"],
    )

    assert baseline["score"] >= 4
    assert final_score >= 3


def test_hard_mismatch_evidence_can_allow_bottom_bucket() -> None:
    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    job = {
        "title": "Senior Full-Stack Engineer",
        "full_description": (
            "Requirements: Active TS/SCI clearance and U.S. citizenship required. "
            "5+ years Java and React."
        ),
    }

    baseline = scorer._compute_deterministic_baseline(scoring_profile, job)
    final_score, _ = scorer._apply_score_calibration(
        baseline=baseline,
        llm_score=1,
        confidence=0.95,
        matched_skills=baseline["matched_skills"],
        missing_requirements=["Active TS/SCI clearance required"],
        job_context=job["full_description"],
    )

    assert final_score <= 2


def test_non_fit_role_baseline_and_calibrated_score_stay_low() -> None:
    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    job = {
        "title": "Director of Marketing + Audience Development",
        "full_description": (
            "Lead demand generation, audience growth, SEO strategy, and content operations."
        ),
    }

    baseline = scorer._compute_deterministic_baseline(scoring_profile, job)
    final_score, _ = scorer._apply_score_calibration(
        baseline=baseline,
        llm_score=3,
        confidence=0.6,
        matched_skills=[],
        missing_requirements=["SEO", "demand generation"],
        job_context=job["full_description"],
    )

    assert baseline["score"] <= 3
    assert final_score <= 4


def test_data_center_thermal_role_gets_market_elasticity_for_adjacent_evidence() -> None:
    score = _calibrated_score_for_energy_job(
        "Data Center Thermal Solutions Engineer",
        (
            "Design emerging AI data center thermal solutions using HVAC, building systems, "
            "heat transfer, thermodynamics, ANSYS Fluent, energy modeling, chilled water, "
            "liquid cooling, and PUE analysis."
        ),
    )

    assert 5 <= score <= 7


def test_data_center_cooling_expert_moves_to_manual_review_range() -> None:
    score = _calibrated_score_for_energy_job(
        "Data Center Cooling Expert",
        (
            "Support data center cooling infrastructure, HVAC optimization, energy efficiency, "
            "facilities operations, financial modeling, thermal management, liquid cooling, "
            "and chilled water retrofit planning."
        ),
    )

    assert 5 <= score <= 6


def test_principal_thermal_engineer_elasticity_cap_stays_low() -> None:
    score = _calibrated_score_for_energy_job(
        "Principal Thermal Engineer",
        (
            "Principal thermal engineer for data center liquid cooling platforms. "
            "Requires 12+ years of thermal design leadership and management experience."
        ),
        llm_score=5,
    )

    assert score <= 4


def test_noc_technician_data_center_not_boosted() -> None:
    score = _calibrated_score_for_energy_job(
        "NOC Technician",
        "Monitor data center network operations, rack cabling, alerts, incidents, and night shift handoffs.",
        llm_score=5,
    )

    assert score <= 3


def test_sales_engineer_or_commission_role_not_boosted() -> None:
    score = _calibrated_score_for_energy_job(
        "Data Center Cooling Sales Engineer",
        "Commission sales role for data center cooling products, account development, and business development.",
        llm_score=5,
    )

    assert score <= 3


def test_no_sponsorship_data_center_role_not_boosted() -> None:
    score = _calibrated_score_for_energy_job(
        "Data Center Cooling Engineer",
        (
            "Work on HVAC and thermal management for data center cooling. "
            "Unable to sponsor now or in the future; candidates must not require sponsorship."
        ),
        llm_score=5,
    )

    assert score <= 2


def test_near_identical_titles_have_bounded_baseline_and_calibrated_variance() -> None:
    scoring_profile = scorer._build_scoring_profile(_sample_profile())
    job_a = {
        "title": "Senior Full-Stack Engineer (Java + React/Angular)",
        "full_description": "Build APIs in Java/Python with React and AWS.",
    }
    job_b = {
        "title": "Senior Full Stack Engineer - Java React Angular",
        "full_description": "Build APIs in Java and Python with React on AWS.",
    }

    baseline_a = scorer._compute_deterministic_baseline(scoring_profile, job_a)
    baseline_b = scorer._compute_deterministic_baseline(scoring_profile, job_b)
    assert abs(baseline_a["score"] - baseline_b["score"]) <= 1

    low_score, _ = scorer._apply_score_calibration(
        baseline=baseline_a,
        llm_score=1,
        confidence=0.4,
        matched_skills=baseline_a["matched_skills"],
        missing_requirements=[],
        job_context=job_a["full_description"],
    )
    high_score, _ = scorer._apply_score_calibration(
        baseline=baseline_a,
        llm_score=10,
        confidence=0.4,
        matched_skills=baseline_a["matched_skills"],
        missing_requirements=[],
        job_context=job_a["full_description"],
    )
    assert abs(high_score - low_score) <= 4


def test_llm_failure_writes_retry_metadata_and_keeps_fit_score_null(monkeypatch) -> None:
    conn = _make_jobs_conn()
    _insert_job(conn)

    monkeypatch.setattr(scorer, "get_connection", lambda: conn)
    monkeypatch.setattr(scorer, "_load_scoring_resume_text", lambda: "resume")
    monkeypatch.setattr(scorer, "_load_scoring_profile", lambda: scorer._build_scoring_profile(_sample_profile()))
    monkeypatch.setattr(
        scorer,
        "get_jobs_by_stage",
        lambda **_: [
            {
                "url": "https://example.com/job/1",
                "title": "Backend Engineer",
                "site": "ExampleCo",
                "location": "Remote",
                "full_description": "Python and APIs",
                "score_retry_count": 0,
            }
        ],
    )
    monkeypatch.setattr(scorer, "evaluate_exclusion", lambda _: None)
    monkeypatch.setattr(
        scorer,
        "score_job",
        lambda *_: {
            "score": 0,
            "keywords": "",
            "reasoning": "LLM parse error [invalid_json]: malformed payload",
            "parse_error_category": "invalid_json",
        },
    )

    result = scorer.run_scoring()

    row = conn.execute(
        "SELECT fit_score, score_error, score_retry_count, score_next_retry_at FROM jobs WHERE url = ?",
        ("https://example.com/job/1",),
    ).fetchone()
    assert result["errors"] == 1
    assert row["fit_score"] is None
    assert "invalid_json" in row["score_error"]
    assert row["score_retry_count"] == 1
    assert row["score_next_retry_at"] is not None


def test_success_clears_retry_and_error_fields(monkeypatch) -> None:
    conn = _make_jobs_conn()
    _insert_job(conn)
    conn.execute(
        "UPDATE jobs SET score_error = ?, score_retry_count = 3, score_next_retry_at = ? WHERE url = ?",
        ("LLM error: old failure", "2099-01-01T00:00:00+00:00", "https://example.com/job/1"),
    )
    conn.commit()

    monkeypatch.setattr(scorer, "get_connection", lambda: conn)
    monkeypatch.setattr(scorer, "_load_scoring_resume_text", lambda: "resume")
    monkeypatch.setattr(scorer, "_load_scoring_profile", lambda: scorer._build_scoring_profile(_sample_profile()))
    monkeypatch.setattr(
        scorer,
        "get_jobs_by_stage",
        lambda **_: [
            {
                "url": "https://example.com/job/1",
                "title": "Backend Engineer",
                "site": "ExampleCo",
                "location": "Remote",
                "full_description": "Python and APIs",
                "score_retry_count": 3,
            }
        ],
    )
    monkeypatch.setattr(scorer, "evaluate_exclusion", lambda _: None)
    monkeypatch.setattr(
        scorer,
        "score_job",
        lambda *_: {"score": 8, "keywords": "python,apis", "reasoning": "Strong fit."},
    )

    scorer.run_scoring()
    row = conn.execute(
        "SELECT fit_score, score_error, score_retry_count, score_next_retry_at, exclusion_reason_code FROM jobs WHERE url = ?",
        ("https://example.com/job/1",),
    ).fetchone()

    assert row["fit_score"] == 8
    assert row["score_error"] is None
    assert row["score_retry_count"] == 0
    assert row["score_next_retry_at"] is None
    assert row["exclusion_reason_code"] is None


def test_exclusions_remain_score_zero_and_clear_retry_fields(monkeypatch) -> None:
    conn = _make_jobs_conn()
    _insert_job(conn)
    conn.execute(
        "UPDATE jobs SET score_error = ?, score_retry_count = 2, score_next_retry_at = ? WHERE url = ?",
        ("LLM error: stale", "2099-01-01T00:00:00+00:00", "https://example.com/job/1"),
    )
    conn.commit()

    monkeypatch.setattr(scorer, "get_connection", lambda: conn)
    monkeypatch.setattr(scorer, "_load_scoring_resume_text", lambda: "resume")
    monkeypatch.setattr(scorer, "_load_scoring_profile", lambda: scorer._build_scoring_profile(_sample_profile()))
    monkeypatch.setattr(
        scorer,
        "get_jobs_by_stage",
        lambda **_: [
            {
                "url": "https://example.com/job/1",
                "title": "Backend Engineer Intern",
                "site": "ExampleCo",
                "location": "Remote",
                "full_description": "Intern role",
                "score_retry_count": 2,
            }
        ],
    )
    monkeypatch.setattr(
        scorer,
        "evaluate_exclusion",
        lambda _: {
            "score": 0,
            "keywords": "",
            "reasoning": "EXCLUDED: excluded_keyword - matched 'intern' (rule r-001)",
            "exclusion_reason_code": "excluded_keyword",
            "exclusion_rule_id": "r-001",
        },
    )
    monkeypatch.setattr(scorer, "score_job", lambda *_: (_ for _ in ()).throw(AssertionError("score_job must not run")))

    scorer.run_scoring()
    row = conn.execute(
        """
        SELECT fit_score, exclusion_reason_code, exclusion_rule_id,
               score_error, score_retry_count, score_next_retry_at
        FROM jobs WHERE url = ?
        """,
        ("https://example.com/job/1",),
    ).fetchone()

    assert row["fit_score"] == 0
    assert row["exclusion_reason_code"] == "excluded_keyword"
    assert row["exclusion_rule_id"] == "r-001"
    assert row["score_error"] is None
    assert row["score_retry_count"] == 0
    assert row["score_next_retry_at"] is None


def test_autoheal_repairs_only_legacy_llm_error_rows() -> None:
    conn = _make_jobs_conn()
    conn.execute(
        """
        INSERT INTO jobs (
            url, title, site, location, full_description, fit_score, score_reasoning,
            exclusion_reason_code, exclusion_rule_id, score_retry_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "https://example.com/poisoned",
            "Engineer",
            "ExampleCo",
            "Remote",
            "Desc",
            0,
            "\nLLM error: legacy failure",
            None,
            None,
            0,
        ),
    )
    conn.execute(
        """
        INSERT INTO jobs (
            url, title, site, location, full_description, fit_score, score_reasoning,
            exclusion_reason_code, exclusion_rule_id, score_retry_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "https://example.com/excluded",
            "Intern Engineer",
            "ExampleCo",
            "Remote",
            "Desc",
            0,
            "EXCLUDED: excluded_keyword",
            "excluded_keyword",
            "r-001",
            0,
        ),
    )
    conn.commit()

    healed = scorer._autoheal_legacy_llm_failures(conn)

    poisoned = conn.execute(
        "SELECT fit_score, score_error, score_retry_count, score_next_retry_at FROM jobs WHERE url = ?",
        ("https://example.com/poisoned",),
    ).fetchone()
    excluded = conn.execute(
        "SELECT fit_score, exclusion_reason_code, exclusion_rule_id FROM jobs WHERE url = ?",
        ("https://example.com/excluded",),
    ).fetchone()

    assert healed == 1
    assert poisoned["fit_score"] is None
    assert poisoned["score_error"].startswith("LLM error:")
    assert poisoned["score_retry_count"] == 1
    assert poisoned["score_next_retry_at"] is None
    assert excluded["fit_score"] == 0
    assert excluded["exclusion_reason_code"] == "excluded_keyword"
    assert excluded["exclusion_rule_id"] == "r-001"
