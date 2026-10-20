from app.services.evidence_matching_service import (
    match_commitment_to_metric,
    retrieve_metric_evidence,
)
from datetime import date

from app.agents.insight_agent import generate_qbr_insights
from app.services.analytics_service import analyze_case
from app.services.evidence_service import list_commitments


def _as_dict(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def _commitment_status(commitment, today):
    status = str(
        commitment.get("status") or "open"
    ).lower()

    due_date = commitment.get("due_date")

    if status in ("completed", "closed", "done"):
        return "completed"

    if status == "blocked":
        return "blocked"

    if due_date:
        try:
            deadline = date.fromisoformat(str(due_date))

            if deadline < today:
                return "overdue"

        except ValueError:
            pass

    return status


def _keywords(text):
    stopwords = {
        "the", "and", "for", "with", "from",
        "this", "that", "into", "updated",
        "deliver", "review", "team",
    }

    return {
        word.strip(".,:;()[]").lower()
        for word in text.split()
        if len(word.strip(".,:;()[]")) >= 4
        and word.strip(".,:;()[]").lower()
        not in stopwords
    }


def build_qbr_context(case_id: int) -> dict:
    """
    Combine KPI insights and historical commitments.

    No external AI API is required.
    """

    analysis = _as_dict(analyze_case(case_id))
    insights = generate_qbr_insights(analysis)
    commitments = list_commitments(case_id)

    today = date.today()

    commitment_details = []
    related_commitments = []

    metrics = analysis.get("metrics", [])

    for commitment in commitments:
        title = commitment.get("title") or ""

        effective_status = _commitment_status(
            commitment, today
        )

        record = {
            **commitment,
            "effective_status": effective_status,
        }

        commitment_details.append(record)

        for metric in metrics:
            metric = _as_dict(metric)

            match = match_commitment_to_metric(
                record,
                metric,
            )

            if match:
                related_commitments.append(match)

    overdue = sum(
        item["effective_status"] == "overdue"
        for item in commitment_details
    )

    blocked = sum(
        item["effective_status"] == "blocked"
        for item in commitment_details
    )

    completed = sum(
        item["effective_status"] == "completed"
        for item in commitment_details
    )

    # Retrieve relevant document evidence for each KPI
    metric_evidence = []

    for metric in metrics:
        metric = _as_dict(metric)
        metric_name = str(metric.get("metric") or "")

        hits = retrieve_metric_evidence(
            case_id,
            metric_name,
            limit=3,
        )

        metric_evidence.append({
            "metric": metric_name,
            "document_hits": hits,
        })

    # Prioritize KPI risks
    prioritized_risks = []

    for metric in metrics:
        metric = _as_dict(metric)

        name = metric.get("metric")
        target_met = metric.get("target_met")
        status = metric.get("status")

        if target_met is False:
            severity = "high"
            reason = "KPI missed its target"
        elif status == "declined":
            severity = "medium"
            reason = "KPI performance declined"
        else:
            continue

        related = [
            item
            for item in related_commitments
            if item["metric"] == name
        ]

        prioritized_risks.append({
            "metric": name,
            "severity": severity,
            "reason": reason,
            "related_commitments": related,
            "relationship_verified": False,
        })

    return {
        "case_id": case_id,"kpi_details": metrics,
        "executive_summary": insights[
            "executive_summary"
        ],
        "kpi_insights": insights["insights"],
        "kpi_risks": insights["risks"],
        "recommendations": insights[
            "recommendations"
        ],
        "kpi_evidence": insights["evidence"],
        "commitments": commitment_details,
        "related_commitments": related_commitments,
        "metric_document_evidence": metric_evidence,
        "prioritized_risks": prioritized_risks,
        "commitment_summary": {
            "total": len(commitment_details),
            "completed": completed,
            "overdue": overdue,
            "blocked": blocked,
        },
        "warnings": analysis.get("warnings", []),
        "generation_mode": "deterministic_context",
    }
