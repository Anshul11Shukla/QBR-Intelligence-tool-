
import re

from app.retrieval.retriever import search_evidence


TOPIC_TERMS = {
    "incident": {
        "incident", "incidents", "playbook",
        "response", "escalation", "ticket",
        "triage", "restoration",
    },
    "sla": {
        "sla", "compliance", "availability",
        "service level", "breach",
    },
    "resolution": {
        "resolution", "resolve", "recovery",
        "mttr", "restoration",
    },
    "customer": {
        "csat", "customer", "satisfaction",
        "feedback",
    },
    "cost": {
        "budget", "spend", "spent",
        "cost", "expense", "financial",
    },
}

RELATED_TOPICS = {
    "incident": {"sla", "resolution"},
    "sla": {"incident", "resolution"},
    "resolution": {"incident", "sla"},
    "customer": set(),
    "cost": set(),
}


def detect_topics(text: str) -> set[str]:
    normalized = re.sub(
        r"\s+", " ", str(text).lower()
    )

    tokens = set(
        re.findall(r"\b\w+\b", normalized)
    )

    topics = set()

    for topic, terms in TOPIC_TERMS.items():
        for term in terms:
            if " " in term:
                matched = term in normalized
            else:
                matched = term in tokens

            if matched:
                topics.add(topic)
                break

    return topics


def match_commitment_to_metric(
    commitment: dict,
    metric: dict,
) -> dict | None:
    title = str(commitment.get("title") or "")
    metric_name = str(metric.get("metric") or "")

    commitment_topics = detect_topics(title)
    metric_topics = detect_topics(metric_name)

    direct_topics = commitment_topics & metric_topics

    related_topics = set()

    for topic in commitment_topics:
        related_topics.update(
            RELATED_TOPICS.get(topic, set())
        )

    inferred_topics = related_topics & metric_topics

    if not direct_topics and not inferred_topics:
        return None

    match_type = (
        "shared_topic"
        if direct_topics
        else "related_topic"
    )

    return {
        "commitment_id": commitment["id"],
        "commitment_title": title,
        "commitment_status": commitment.get(
            "effective_status",
            commitment.get("status"),
        ),
        "metric": metric_name,
        "match_type": match_type,
        "matching_topics": sorted(
            direct_topics or inferred_topics
        ),
        "source_document_id": commitment.get(
            "source_document_id"
        ),
        "source_location": commitment.get(
            "source_location"
        ),
        "relationship": "potential_relevance_only",
    }


def retrieve_metric_evidence(
    case_id: int,
    metric_name: str,
    limit: int = 3,
) -> list[dict]:
    """
    Retrieve supporting document passages.

    A search hit is not proof of causation.
    """

    topics = detect_topics(metric_name)

    search_terms = [metric_name]

    for topic in sorted(topics):
        search_terms.extend(
            sorted(TOPIC_TERMS[topic])[:4]
        )

    query = " ".join(search_terms)

    hits = search_evidence(
        case_id=case_id,
        query=query,
        limit=limit,
    )

    return [
        hit.model_dump()
        if hasattr(hit, "model_dump")
        else dict(hit)
        for hit in hits
    ]

