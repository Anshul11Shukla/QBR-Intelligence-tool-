
from typing import Any


def _as_dict(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


def enhance_qa_questions(
    questions: list[dict],
) -> list[dict]:
    """
    Add presentation coaching to existing Q&A results.

    Does not modify verified KPI data or invent evidence.
    """

    enhanced = []

    for question in questions:
        item = _as_dict(question).copy()

        category = item.get("category")
        facts = _as_dict(item.get("kpi_facts") or {})
        sources = item.get("source_references") or []
        documents = item.get("document_evidence") or []
        commitments = item.get(
            "related_commitments"
        ) or []

        evidence_gaps = []
        preparation_actions = []

        if category == "performance_risk":
            metric = item.get("metric") or "KPI"

            if not facts:
                evidence_gaps.append(
                    "Verified KPI values are missing."
                )

            if not sources:
                evidence_gaps.append(
                    "Spreadsheet source references "
                    "are unavailable."
                )

            if not documents:
                evidence_gaps.append(
                    "No supporting document passages "
                    "were retrieved."
                )

            evidence_gaps.append(
                "A verified root cause has not "
                "been established."
            )

            evidence_gaps.append(
                "A confirmed corrective action plan "
                "and timeline are not recorded "
                "in this Q&A response."
            )

            preparation_actions.extend([
                f"Confirm the root cause for {metric}.",
                "Validate corrective actions with "
                "the responsible operations team.",
                "Confirm action ownership and "
                "completion timelines.",
            ])

            if commitments:
                preparation_actions.append(
                    "Review potentially related "
                    "historical commitments."
                )

            if facts and sources:
                readiness = "partially_ready"
            else:
                readiness = "needs_evidence"

            talking_points = [
                "Start with the verified KPI values "
                "and quarter-on-quarter movement.",
                "Explain the configured target "
                "and whether it was achieved.",
                "Distinguish potential contributing "
                "factors from confirmed root causes.",
                "Close with the next validation "
                "or corrective action."
            ]

        elif category == "historical_commitment":
            commitment = (
                _as_dict(commitments[0])
                if commitments else {}
            )

            owner = commitment.get("owner")
            due_date = commitment.get("due_date")

            if not owner:
                evidence_gaps.append(
                    "Commitment owner is not recorded."
                )

            if not due_date:
                evidence_gaps.append(
                    "Original due date is not recorded."
                )

            evidence_gaps.extend([
                "Reason for delay is not verified.",
                "Revised completion date is "
                "not confirmed.",
            ])

            preparation_actions.extend([
                "Contact the recorded commitment owner.",
                "Confirm current progress and blockers.",
                "Agree on a revised completion date.",
                "Record the updated commitment status.",
            ])

            readiness = "partially_ready" if (
                owner and due_date
            ) else "needs_evidence"

            talking_points = [
                "Acknowledge the historical commitment.",
                "State the recorded owner and due date.",
                "Explain the stored status separately "
                "from the calculated overdue status.",
                "Request a confirmed recovery plan "
                "without promising an unverified date.",
            ]

        else:
            readiness = "needs_review"
            talking_points = [
                "Verify the supporting evidence.",
                "Prepare a concise factual answer.",
            ]
            preparation_actions.append(
                "Review the question before presenting."
            )

        item["answer_readiness"] = readiness
        item["executive_talking_points"] = talking_points
        item["evidence_gaps"] = evidence_gaps
        item["preparation_actions"] = preparation_actions

        enhanced.append(item)

    return enhanced
