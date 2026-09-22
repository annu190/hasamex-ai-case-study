from app.topic_map import QUESTION_TOPICS


TOPIC_PRIORITY = {
    "adoption": {
        "positive": [
            "adoption",
            "growing",
            "increasing",
            "access",
            "standard",
            "hospitals",
        ],
        "negative": [
            "months",
            "timeline",
            "maintenance",
            "pay for itself",
        ],
    },
    "barriers": {
        "positive": [
            "barrier",
            "barriers",
            "cost",
            "funding",
            "capital budget",
            "budget approval",
            "training",
            "staff",
            "finance",
            "economic case",
            "utilisation",
            "utilization",
            "procedure volume",
        ],
        "negative": [
            "six to twelve months",
            "six to nine months",
            "months",
            "capital cycle",
            "budget cycle",
            "next",
            "annually",
            "outlook",
            "growth",
        ],
    },
    "economics": {
        "positive": [
            "roi",
            "economic",
            "economics",
            "cost",
            "budget",
            "maintenance",
            "procedure volume",
            "utilisation",
            "utilization",
            "pay for itself",
            "tco",
            "service contracts",
        ],
        "negative": [
            "months",
            "capital cycle",
            "annually",
        ],
    },
    "training_and_outcomes": {
        "positive": [
            "training",
            "surgeon",
            "surgeons",
            "clinical",
            "outcomes",
            "staff",
            "theatre",
            "utilisation",
            "utilization",
        ],
        "negative": [
            "months",
            "capital cycle",
            "annually",
        ],
    },
    "future_adoption": {
        "positive": [
            "future",
            "growth",
            "accelerate",
            "gradual",
            "increase",
            "annually",
            "years",
            "outlook",
            "procedure growth",
        ],
        "negative": [
            "purchase",
            "procurement",
            "months",
            "budget approval",
        ],
    },
    "purchase_timeline": {
        "positive": [
            "months",
            "timeline",
            "purchase",
            "procurement",
            "capital cycle",
            "budget cycle",
            "decision",
        ],
        "negative": [
            "annually",
            "growth",
            "clinical outcomes",
        ],
    },
}


def rerank(
    results: list[dict],
    topic: str | None,
) -> list[dict]:

    if not topic:
        return results

    profile = TOPIC_PRIORITY.get(
        topic,
        {},
    )

    positive = [
        item.lower()
        for item in profile.get(
            "positive",
            [],
        )
    ]

    negative = [
        item.lower()
        for item in profile.get(
            "negative",
            [],
        )
    ]

    reranked = []

    for item in results:

        text = item[
            "evidence"
        ].text.lower()

        positive_hits = sum(
            1
            for signal in positive
            if signal in text
        )

        negative_hits = sum(
            1
            for signal in negative
            if signal in text
        )

        rerank_score = (
            item["hybrid_score"]
            + (0.08 * positive_hits)
            - (0.12 * negative_hits)
        )

        updated = dict(item)

        updated[
            "positive_hits"
        ] = positive_hits

        updated[
            "negative_hits"
        ] = negative_hits

        updated[
            "rerank_score"
        ] = round(
            max(
                rerank_score,
                0.0,
            ),
            4,
        )

        reranked.append(updated)

    reranked.sort(
        key=lambda item: item[
            "rerank_score"
        ],
        reverse=True,
    )

    return reranked