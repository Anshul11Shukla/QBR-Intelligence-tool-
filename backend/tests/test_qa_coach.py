
from app.agents.qa_coach_agent import (
    generate_customer_questions,
)
from app.services.qa_coaching_service import (
    enhance_qa_questions,
)


def sample_context():
    return {
        "case_id": 1,
        "kpi_details": [
            {
                "metric": "SLA Compliance",
                "unit": "%",
                "previous_value": 98.0,
                "current_value": 92.0,
                "target": 95.0,
                "percentage_change": -6.12,
                "target_met": False,
                "sources": {
                    "previous": "previous.xlsx / Sheet1 / row 2",
                    "current": "current.xlsx / Sheet1 / row 2",
                },
            }
        ],
        "prioritized_risks": [
            {
                "metric": "SLA Compliance",
                "severity": "high",
                "reason": "KPI missed its target",
                "related_commitments": [],
            }
        ],
        "metric_document_evidence": [
            {
                "metric": "SLA Compliance",
                "document_hits": [],
            }
        ],
        "commitments": [
            {
                "id": 2,
                "title": "Update incident response playbook",
                "owner": "Operations Team",
                "due_date": "2026-09-30",
                "status": "in_progress",
                "effective_status": "overdue",
                "source_document_id": None,
            }
        ],
    }


def test_generates_kpi_and_commitment_questions():
    questions = generate_customer_questions(
        sample_context()
    )

    assert len(questions) == 2
    assert questions[0]["metric"] == "SLA Compliance"
    assert questions[0]["severity"] == "high"
    assert questions[1]["category"] == "historical_commitment"


def test_answer_contains_verified_kpi_values():
    questions = generate_customer_questions(
        sample_context()
    )

    answer = questions[0]["suggested_answer"]

    assert "98%" in answer
    assert "92%" in answer
    assert "95%" in answer
    assert "percentage points" in answer


def test_preserves_spreadsheet_sources():
    questions = generate_customer_questions(
        sample_context()
    )

    sources = questions[0]["source_references"]

    assert len(sources) == 2
    assert sources[0]["period"] == "previous"
    assert sources[1]["period"] == "current"


def test_commitment_answer_includes_owner_and_date():
    questions = generate_customer_questions(
        sample_context()
    )

    answer = questions[1]["suggested_answer"]

    assert "Operations Team" in answer
    assert "2026-09-30" in answer
    assert "in_progress" in answer


def test_coaching_enhancement():
    questions = generate_customer_questions(
        sample_context()
    )

    enhanced = enhance_qa_questions(questions)

    assert len(enhanced) == 2

    for question in enhanced:
        assert "answer_readiness" in question
        assert "executive_talking_points" in question
        assert "evidence_gaps" in question
        assert "preparation_actions" in question

    assert enhanced[0]["answer_readiness"] == "partially_ready"
    assert enhanced[1]["answer_readiness"] == "partially_ready"


def test_does_not_mutate_original_questions():
    questions = generate_customer_questions(
        sample_context()
    )

    enhanced = enhance_qa_questions(questions)

    assert "answer_readiness" not in questions[0]
    assert "answer_readiness" in enhanced[0]


def test_invalid_context():
    try:
        generate_customer_questions(None)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid context"
        )
