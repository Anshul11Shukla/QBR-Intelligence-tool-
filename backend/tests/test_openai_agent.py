
import json
from unittest.mock import Mock

from app.agents.openai_agent import generate_ai_qbr_insights


def sample_analysis():
    return {
        "case_id": 1,
        "metrics": [
            {
                "metric": "SLA Compliance",
                "unit": "%",
                "direction": "higher",
                "previous_value": 98.0,
                "current_value": 92.0,
                "percentage_change": -6.12,
                "target": 95.0,
                "target_met": False,
                "alerts": ["Target breach"],
                "sources": {
                    "previous": "Sheet1 row 2",
                    "current": "Sheet1 row 2",
                },
            }
        ],
        "summary": {"total_metrics": 1},
        "warnings": [],
    }


def test_ai_success():
    client = Mock()

    client.responses.create.return_value.output_text = (
        json.dumps({
            "executive_summary": "SLA declined below target.",
            "key_findings": [
                "SLA declined from 98% to 92%."
            ],
            "risks": [
                "SLA missed the 95% target."
            ],
            "recommendations": [
                "Investigate incidents behind the breach."
            ],
        })
    )

    result = generate_ai_qbr_insights(
        sample_analysis(),
        client=client,
    )

    assert result["generation_mode"] == "openai"
    assert result["ai_status"] == "success"
    assert result["evidence"][0]["metric"] == "SLA Compliance"
    client.responses.create.assert_called_once()


def test_ai_failure_fallback():
    client = Mock()
    client.responses.create.side_effect = RuntimeError(
        "Simulated API failure"
    )

    result = generate_ai_qbr_insights(
        sample_analysis(),
        client=client,
    )

    assert result["generation_mode"] == "deterministic_demo"
    assert result["ai_status"] == "fallback_ai_error"
    assert result["evidence"]


def test_empty_metrics():
    result = generate_ai_qbr_insights({
        "case_id": 1,
        "metrics": [],
        "warnings": [],
    })

    assert result["ai_status"] == "skipped_no_metrics"
