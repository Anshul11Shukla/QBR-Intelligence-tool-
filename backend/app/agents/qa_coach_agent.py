
from typing import Any


def _as_dict(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def _format_value(value, unit=""):
    if value is None:
        return "not available"

    if isinstance(value, (int, float)):
        number = f"{value:,.2f}".rstrip("0").rstrip(".")
    else:
        number = str(value)

    if unit == "%":
        return f"{number}%"

    if unit == "INR":
        return f"INR {number}"

    return f"{number} {unit}".strip()


def _find_metric(kpi_details, metric_name):
    for item in kpi_details:
        item = _as_dict(item)
        if item.get("metric") == metric_name:
            return item
    return {}


def _find_evidence(evidence, metric_name):
    for item in evidence:
        item = _as_dict(item)
        if item.get("metric") == metric_name:
            return item.get("document_hits") or []
    return []


def _source_references(metric_data):
    sources = metric_data.get("sources") or {}

    references = []

    if sources.get("previous"):
        references.append({
            "period": "previous",
            "source": sources["previous"],
        })

    if sources.get("current"):
        references.append({
            "period": "current",
            "source": sources["current"],
        })

    return references


def _metric_answer(metric_name, metric_data, related):
    previous = metric_data.get("previous_value")
    current = metric_data.get("current_value")
    target = metric_data.get("target")
    change = metric_data.get("percentage_change")
    unit = metric_data.get("unit") or ""

    sentences = []

    if previous is not None and current is not None:
        sentences.append(
            f"{metric_name} changed from "
            f"{_format_value(previous, unit)} in the "
            f"previous quarter to "
            f"{_format_value(current, unit)} "
            "in the current quarter."
        )
    elif current is not None:
        sentences.append(
            f"The current recorded value for "
            f"{metric_name} is "
            f"{_format_value(current, unit)}."
        )

    if isinstance(change, (int, float)):
        movement = (
            "increased" if change > 0
            else "decreased" if change < 0
            else "remained unchanged"
        )
        sentences.append(
            f"The relative quarter-on-quarter "
            f"change {movement} by "
            f"{abs(change):.2f}%."
        )

    if target is not None:
        sentences.append(
            f"The configured target is "
            f"{_format_value(target, unit)}."
        )

        if metric_data.get("target_met") is False:
            sentences.append(
                "The current result does not meet "
                "the configured target."
            )

            if (
                unit == "%"
                and isinstance(current, (int, float))
                and isinstance(target, (int, float))
            ):
                gap = abs(current - target)
                sentences.append(
                    f"The difference from the target "
                    f"is {gap:.2f} percentage points."
                )

    if related:
        sentences.append(
            f"{len(related)} historical commitment(s) "
            "have been identified as potentially "
            "relevant. This does not establish "
            "a causal relationship."
        )

    sentences.append(
        "The available evidence does not establish "
        "a verified root cause. The responsible "
        "team should confirm contributing factors, "
        "corrective actions, ownership, and timelines."
    )

    return " ".join(sentences)


def generate_customer_questions(
    qbr_context: dict,
) -> list[dict]:
    """
    Generate evidence-grounded customer QBR coaching.

    Uses verified KPI records and historical commitments.
    No external AI API is required.
    """

    if not isinstance(qbr_context, dict):
        raise ValueError("QBR context must be a dictionary")

    questions = []

    risks = qbr_context.get("prioritized_risks", [])
    commitments = qbr_context.get("commitments", [])
    evidence = qbr_context.get(
        "metric_document_evidence", []
    )
    kpi_details = qbr_context.get("kpi_details", [])

    for risk in risks:
        risk = _as_dict(risk)

        metric = str(risk.get("metric") or "KPI")
        severity = risk.get("severity", "medium")
        reason = risk.get("reason", "Requires review")

        metric_data = _find_metric(kpi_details, metric)
        matching_evidence = _find_evidence(evidence, metric)
        related = risk.get("related_commitments") or []

        if reason == "KPI missed its target":
            question = (
                f"Why did {metric} miss its target, "
                "and what corrective actions are planned?"
            )
        else:
            question = (
                f"What caused the deterioration in "
                f"{metric}, and how will it be addressed?"
            )

        answer = _metric_answer(
            metric,
            metric_data,
            related,
        )

        questions.append({
            "question_id": len(questions) + 1,
            "category": "performance_risk",
            "metric": metric,
            "severity": severity,
            "customer_question": question,
            "suggested_answer": answer,
            "follow_up_question": (
                f"What evidence and timeline can "
                f"you provide for improving {metric}?"
            ),
            "coaching_tip": (
                "Lead with verified KPI figures. "
                "Explain target gaps accurately. "
                "Do not invent root causes or dates. "
                "Confirm owners and corrective actions."
            ),
            "kpi_facts": metric_data,
            "source_references": _source_references(
                metric_data
            ),
            "related_commitments": related,
            "document_evidence": matching_evidence,
            "confidence": (
                "document_references_available"
                if matching_evidence
                else "kpi_sources_only"
                if metric_data.get("sources")
                else "limited_evidence"
            ),
        })

    overdue = [
        item for item in commitments
        if item.get("effective_status") == "overdue"
    ]

    for commitment in overdue:
        title = commitment.get(
            "title", "Historical commitment"
        )
        owner = commitment.get("owner") or "Not recorded"
        due_date = commitment.get("due_date") or "Not recorded"
        stored_status = commitment.get("status") or "unknown"

        answer = (
            f"The commitment '{title}' is assigned "
            f"to {owner}, with a recorded due date "
            f"of {due_date}. Its stored status is "
            f"'{stored_status}', and it is currently "
            "classified as overdue because its due "
            "date has passed without a completed status. "
            "The available record does not establish "
            "the reason for the delay. The owner should "
            "confirm progress and a revised completion date."
        )

        questions.append({
            "question_id": len(questions) + 1,
            "category": "historical_commitment",
            "metric": None,
            "severity": "medium",
            "customer_question": (
                f"Why is the commitment '{title}' "
                "still overdue?"
            ),
            "suggested_answer": answer,
            "follow_up_question": (
                "Who owns this action, and what is "
                "the confirmed revised completion date?"
            ),
            "coaching_tip": (
                "Acknowledge the recorded due date "
                "and current status. Do not promise "
                "an unconfirmed completion date."
            ),
            "kpi_facts": {},
            "source_references": (
                [{
                    "document_id": commitment[
                        "source_document_id"
                    ],
                    "source_location": commitment.get(
                        "source_location"
                    ),
                }]
                if commitment.get("source_document_id")
                is not None
                else []
            ),
            "related_commitments": [commitment],
            "document_evidence": [],
            "confidence": "commitment_record_only",
        })

    return questions
