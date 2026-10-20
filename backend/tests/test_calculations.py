
from app.analytics.calculations import (
    calculate_change,
    movement_status,
)
from app.analytics.target_checks import check_target
from app.analytics.anomaly_detection import detect_anomalies
from app.analytics.ingestion import parse_workbook

from io import BytesIO
from openpyxl import Workbook
import pytest


def test_sla_change():
    absolute, percentage = calculate_change(98, 92)
    assert absolute == -6
    assert percentage == -6.12


def test_zero_baseline():
    absolute, percentage = calculate_change(0, 10)
    assert absolute == 10
    assert percentage is None


def test_missing_data():
    assert calculate_change(None, 92) == (None, None)
    assert movement_status(None, 92, "higher") == "insufficient_data"


def test_higher_is_better():
    assert check_target(92, 95, "higher") is False
    assert check_target(98, 95, "higher") is True


def test_lower_is_better():
    assert check_target(6, 7, "lower") is True
    assert movement_status(8, 6, "lower") == "improved"


def test_anomaly_detection():
    alerts = detect_anomalies(
        previous=98,
        current=92,
        direction="higher",
        target_met=False,
        percentage_change=-6.12,
    )

    assert "Target breach" in alerts
    assert "Unfavorable KPI movement" in alerts


def test_excel_ingestion():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
        "Metric", "Value", "Unit", "Direction", "Target"
    ])
    sheet.append([
        "SLA Compliance", 92, "%", "higher", 95
    ])

    output = BytesIO()
    workbook.save(output)

    records = parse_workbook(output.getvalue())

    assert len(records) == 1
    assert records[0].value == 92
    assert records[0].source_row == 2


def test_duplicate_metric_rejected():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
        "Metric", "Value", "Unit", "Direction", "Target"
    ])
    sheet.append(["CSAT", 90, "%", "higher", 92])
    sheet.append(["csat", 94, "%", "higher", 92])

    output = BytesIO()
    workbook.save(output)

    with pytest.raises(ValueError, match="Duplicate metric"):
        parse_workbook(output.getvalue())
