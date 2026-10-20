
from app.analytics.calculations import movement_status


def detect_anomalies(
    previous: float | None,
    current: float | None,
    direction: str,
    target_met: bool | None,
    percentage_change: float | None,
) -> list[str]:
    alerts = []

    if previous is None or current is None:
        alerts.append("Missing quarter data")

    if target_met is False:
        alerts.append("Target breach")

    status = movement_status(
        previous,
        current,
        direction,
    )

    if status == "declined":
        alerts.append("Unfavorable KPI movement")

    if (
        percentage_change is not None
        and abs(percentage_change) >= 20
    ):
        alerts.append(
            "Large quarter-on-quarter movement (20% or more)"
        )

    if previous == 0 and current not in (None, 0):
        alerts.append(
            "Relative change undefined: previous value is zero"
        )

    return alerts
