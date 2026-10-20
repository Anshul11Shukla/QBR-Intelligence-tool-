
from app.agents.insight_agent import generate_qbr_insights


def test_generate_qbr_insights():
    sample_data = {
        "case_id": 1,
        "metrics": [
            {
                "metric": "Incident Resolution",
                "unit": "tickets",
                "direction": "higher",
                "previous_value": 900,
                "current_value": 1080,
                "target": 1000,
                "percentage_change": 20.0,
                "target_met": True,
                "alerts": [],
                "sources": {
                    "previous": "previous.xlsx:Sheet1!B2",
                    "current": "current.xlsx:Sheet1!B2",
                },
            },
            {
                "metric": "SLA Compliance",
                "unit": "%",
                "direction": "higher",
                "previous_value": 98,
                "current_value": 92,
                "target": 95,
                "percentage_change": -6.12,
                "target_met": False,
                "alerts": ["Below target"],
                "sources": {
                    "previous": "previous.xlsx:Sheet1!B3",
                    "current": "current.xlsx:Sheet1!B3",
                },
            },
        ],
        "summary": {},
        "warnings": [],
    }

    result = generate_qbr_insights(sample_data)

    assert result["case_id"] == 1
    assert len(result["insights"]) >= 2
    assert len(result["risks"]) >= 1
    assert len(result["evidence"]) == 2
    assert result["generation_mode"] == "deterministic_demo"


def test_empty_kpi_data():
    result = generate_qbr_insights({
        "case_id": 1,
        "metrics": [],
        "summary": {},
        "warnings": [],
    })

    assert result["insights"] == []
    assert result["risks"] == []
