
from app.analytics.calculations import (
    calculate_change,
    movement_status,
)
from app.analytics.normalization import metric_key
from app.analytics.target_checks import check_target
from app.analytics.anomaly_detection import detect_anomalies
from app.database import get_connection
from app.schemas.kpi import AnalysisResponse, KPIResult
from app.services.file_service import get_kpi_snapshots


def analyze_case(case_id: int) -> AnalysisResponse:
    with get_connection() as connection:
        case = connection.execute(
            "SELECT id FROM qbr_cases WHERE id = ?",
            (case_id,),
        ).fetchone()

    if case is None:
        raise LookupError("QBR workspace not found")

    snapshots = get_kpi_snapshots(case_id)

    previous = snapshots.get("previous", {})
    current = snapshots.get("current", {})

    previous_records = {
        metric_key(item["metric"]): item
        for item in previous.get("records", [])
    }

    current_records = {
        metric_key(item["metric"]): item
        for item in current.get("records", [])
    }

    keys = sorted(set(previous_records) | set(current_records))

    results = []
    warnings = []

    if not previous:
        warnings.append("Previous-quarter spreadsheet missing")

    if not current:
        warnings.append("Current-quarter spreadsheet missing")

    for key in keys:
        old = previous_records.get(key)
        new = current_records.get(key)

        reference = new or old
        assert reference is not None

        if old and new:
            if (
                old["unit"] != new["unit"]
                or old["direction"] != new["direction"]
            ):
                warnings.append(
                    f"{reference['metric']}: incompatible units "
                    "or directions across quarters"
                )
                continue

            if (
                old["target"] is not None
                and new["target"] is not None
                and old["target"] != new["target"]
            ):
                warnings.append(
                    f"{reference['metric']}: target changed "
                    "between quarters; current target used"
                )

        previous_value = old["value"] if old else None
        current_value = new["value"] if new else None

        target = (
            new["target"]
            if new and new["target"] is not None
            else old["target"] if old else None
        )

        direction = reference["direction"]

        absolute, percentage = calculate_change(
            previous_value,
            current_value,
        )

        target_met = check_target(
            current_value,
            target,
            direction,
        )

        status = movement_status(
            previous_value,
            current_value,
            direction,
        )

        alerts = detect_anomalies(
            previous_value,
            current_value,
            direction,
            target_met,
            percentage,
        )

        sources = {}

        if old:
            sources["previous"] = (
                f"{previous['filename']} / "
                f"{old['source_sheet']} / "
                f"row {old['source_row']}"
            )

        if new:
            sources["current"] = (
                f"{current['filename']} / "
                f"{new['source_sheet']} / "
                f"row {new['source_row']}"
            )

        results.append(
            KPIResult(
                metric=reference["metric"],
                unit=reference["unit"],
                direction=direction,
                previous_value=previous_value,
                current_value=current_value,
                target=target,
                absolute_change=absolute,
                percentage_change=percentage,
                target_met=target_met,
                status=status,
                alerts=alerts,
                sources=sources,
            )
        )

    summary = {
        "total_metrics": len(results),
        "improved": sum(
            item.status == "improved" for item in results
        ),
        "declined": sum(
            item.status == "declined" for item in results
        ),
        "target_breaches": sum(
            item.target_met is False for item in results
        ),
        "metrics_with_alerts": sum(
            bool(item.alerts) for item in results
        ),
    }

    return AnalysisResponse(
        case_id=case_id,
        metrics=results,
        summary=summary,
        warnings=warnings,
    )
