
from typing import Any
import math


def _number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _format_value(value: Any, unit: str) -> str:
    if not _number(value):
        return "N/A"
    number = f"{value:,.2f}".rstrip("0").rstrip(".")
    if unit == "%":
        return f"{number}%"
    if unit.upper() == "INR":
        return f"INR {number}"
    return f"{number} {unit}".strip()


def _severity(
    current: Any,
    target: Any,
    direction: str,
) -> str:
    if not _number(current) or not _number(target):
        return "medium"

    if direction == "higher":
        shortfall = target - current
    elif direction == "lower":
        shortfall = current - target
    else:
        return "medium"

    if shortfall <= 0:
        return "low"

    if target == 0:
        return "high"

    gap_percent = abs(shortfall) / abs(target) * 100

    if gap_percent >= 20:
        return "critical"
    if gap_percent >= 10:
        return "high"
    if gap_percent >= 5:
        return "medium"
    return "low"


def _recommendation(metric: str) -> tuple[str, str]:
    name = metric.lower()

    if "sla" in name or "compliance" in name:
        return (
            "Review SLA breach incidents, response times, "
            "escalation delays, and service restoration records.",
            "Potential contributors include delayed escalation, "
            "longer outages, or unresolved incident backlogs.",
        )

    if "resolution" in name or "mttr" in name:
        return (
            "Review incident resolution trends, identify "
            "recurring delays, and improve troubleshooting playbooks.",
            "Potential contributors include incident complexity, "
            "handoff delays, or insufficient automation.",
        )

    if "csat" in name or "satisfaction" in name:
        return (
            "Analyze customer feedback, recurring complaints, "
            "and service experience trends.",
            "Potential contributors include service disruption, "
            "communication quality, or unmet expectations.",
        )

    if "budget" in name or "cost" in name or "spend" in name:
        return (
            "Review spending against budget forecasts and "
            "investigate major cost drivers.",
            "Potential contributors include increased usage, "
            "unexpected expenses, or resource inefficiency.",
        )

    return (
        "Review the KPI trend, validate underlying data, "
        "and assign an owner for corrective action.",
        "The underlying cause requires investigation using "
        "operational records and historical evidence.",
    )


def generate_qbr_insights(analysis: Any) -> dict:
    """
    Generate structured, evidence-aware QBR insights.

    Deterministic generation: no external LLM is called.
    """

    if hasattr(analysis, "model_dump"):
        analysis = analysis.model_dump()

    if not isinstance(analysis, dict):
        raise ValueError("Expected an analytics response object")

    metrics = analysis.get("metrics", [])
    if not isinstance(metrics, list):
        raise ValueError("Analytics metrics must be a list")

    insights = []
    risks = []
    recommendations = []
    evidence = []
    risk_details = []
    kpi_details = []

    improved_count = 0
    declined_count = 0
    target_breaches = 0

    for raw_item in metrics:
        item = (
            raw_item.model_dump()
            if hasattr(raw_item, "model_dump")
            else raw_item
        )

        if not isinstance(item, dict):
            continue

        name = str(item.get("metric") or "Unknown KPI")
        unit = str(item.get("unit") or "")
        direction = item.get("direction", "")

        previous = item.get("previous_value")
        current = item.get("current_value")
        change = item.get("percentage_change")
        target = item.get("target")
        target_met = item.get("target_met")
        sources = item.get("sources") or {}
        alerts = item.get("alerts") or []

        recommendation, possible_causes = _recommendation(name)

        trend = "unknown"
        performance = "unknown"

        if _number(change):
            if change > 0:
                trend = "increased"
            elif change < 0:
                trend = "decreased"
            else:
                trend = "unchanged"

            if trend == "unchanged":
                insights.append(
                    f"{name} remained unchanged quarter-on-quarter."
                )
            else:
                insights.append(
                    f"{name} {trend} by {abs(change):.1f}% "
                    "quarter-on-quarter."
                )

        if (
            _number(previous)
            and _number(current)
            and direction in ("higher", "lower")
        ):
            if current == previous:
                performance = "stable"
            else:
                improved = (
                    current > previous
                    if direction == "higher"
                    else current < previous
                )
                performance = (
                    "improved" if improved else "deteriorated"
                )

                if improved:
                    improved_count += 1
                else:
                    declined_count += 1

                insights.append(
                    f"{name} performance {performance} "
                    f"based on its '{direction}' direction."
                )

        # Count one business risk per KPI rather than
        # separately counting its target breach and alerts.
        has_target_breach = target_met is False
        has_alerts = bool(alerts)

        if has_target_breach:
            target_breaches += 1

        if has_target_breach or has_alerts:
            severity = (
                _severity(current, target, direction)
                if has_target_breach
                else "medium"
            )

            if has_target_breach:
                message = (
                    f"{name} missed its target of "
                    f"{_format_value(target, unit)}."
                )
            else:
                message = f"{name} has an analytics alert."

            risks.append(message)

            risk_details.append({
                "metric": name,
                "severity": severity,
                "description": message,
                "alerts": alerts,
                "possible_causes": possible_causes,
                "recommendation": recommendation,
                "sources": sources,
            })

            recommendations.append(
                f"{name}: {recommendation}"
            )

        elif performance == "deteriorated":
            recommendations.append(
                f"{name}: {recommendation}"
            )

        kpi_details.append({
            "metric": name,
            "unit": unit,
            "previous_value": previous,
            "current_value": current,
            "percentage_change": change,
            "target": target,
            "target_met": target_met,
            "trend": trend,
            "performance": performance,
            "sources": sources,
        })

        evidence.append({
            "metric": name,
            "sources": sources,
            "previous_value": previous,
            "current_value": current,
            "target": target,
        })

    if not recommendations:
        recommendations.append(
            "Continue monitoring KPI performance and "
            "review results during the next QBR cycle."
        )

    executive_summary = (
        f"Analyzed {len(kpi_details)} KPI records, "
        f"identified {len(insights)} performance observations "
        f"and {len(risks)} risk alerts. "
        f"{improved_count} KPIs improved, "
        f"{declined_count} deteriorated, "
        f"and {target_breaches} missed their targets."
    )

    return {
        "case_id": analysis.get("case_id"),
        "executive_summary": executive_summary,
        "insights": insights,
        "risks": risks,
        "recommendations": recommendations,
        "evidence": evidence,
        "warnings": analysis.get("warnings", []),
        "generation_mode": "deterministic_demo",
        "risk_details": risk_details,
        "kpi_details": kpi_details,
        "summary_stats": {
            "total_metrics": len(kpi_details),
            "improved": improved_count,
            "declined": declined_count,
            "target_breaches": target_breaches,
            "risk_count": len(risks),
        },
    }
