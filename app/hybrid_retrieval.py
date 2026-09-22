import re
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.evidence_store import EvidenceStore
from app.topic_map import QUESTION_TOPICS
from app.reranker import rerank


TOPIC_SIGNALS = {
    "adoption": [
        "adoption",
        "increasing",
        "growing",
        "access",
        "standard",
        "hospitals",
    ],
    "barriers": [
        "barrier",
        "barriers",
        "cost",
        "funding",
        "capital",
        "budget",
        "utilisation",
        "utilization",
        "training",
        "staff",
        "finance",
    ],
    "economics": [
        "roi",
        "economic",
        "economics",
        "cost",
        "budget",
        "utilisation",
        "utilization",
        "maintenance",
        "procedure",
        "volume",
        "pay",
        "tco",
        "financial",
    ],
    "training_and_outcomes": [
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
    "future_adoption": [
        "future",
        "growth",
        "accelerate",
        "gradual",
        "increase",
        "annually",
        "years",
        "outlook",
    ],
    "purchase_timeline": [
        "timeline",
        "months",
        "purchase",
        "procurement",
        "capital cycle",
        "decision",
        "budget cycle",
    ],
}


GENERIC_TOPIC_TERMS = {
    "adoption",
    "increase",
    "increasing",
    "growing",
    "growth",
    "hospitals",
    "market",
}


class HybridRetriever:
    def __init__(
        self,
        store: EvidenceStore,
        keyword_weight: float = 0.65,
        tfidf_weight: float = 0.35,
    ):
        self.store = store
        self.keyword_weight = keyword_weight
        self.tfidf_weight = tfidf_weight

        self.evidence = store.expert_statements()

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )

        self.matrix = self.vectorizer.fit_transform(
            [item.text for item in self.evidence]
        )

    def _tokenize(self, text: str) -> set[str]:
        return set(
            re.findall(
                r"\b[a-zA-Z]+\b",
                text.lower(),
            )
        )

    def _detect_topic(
        self,
        query: str,
    ) -> str | None:

        query_lower = query.lower()

        best_topic = None
        best_score = 0

        for info in QUESTION_TOPICS.values():
            score = 0

            for phrase in info.get(
                "priority_phrases",
                [],
            ):
                if phrase.lower() in query_lower:
                    score += 10

            for keyword in info.get(
                "keywords",
                [],
            ):
                if keyword.lower() in query_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_topic = info["topic"]

        return best_topic

    def _direct_overlap_score(
        self,
        query: str,
        evidence,
    ) -> float:

        query_tokens = self._tokenize(query)
        evidence_tokens = self._tokenize(
            evidence.text
        )

        if not query_tokens:
            return 0.0

        useful_query_tokens = (
            query_tokens
            - GENERIC_TOPIC_TERMS
        )

        if not useful_query_tokens:
            useful_query_tokens = query_tokens

        overlap = (
            useful_query_tokens
            & evidence_tokens
        )

        return len(overlap) / len(
            useful_query_tokens
        )

    def _topic_score(
        self,
        topic: str | None,
        evidence,
    ) -> float:

        if not topic:
            return 0.0

        signals = TOPIC_SIGNALS.get(
            topic,
            [],
        )

        if not signals:
            return 0.0

        evidence_text = evidence.text.lower()

        matched = 0

        for signal in signals:
            if signal.lower() in evidence_text:
                matched += 1

        return min(
            matched / 3.0,
            1.0,
        )

    def _topic_penalty(
        self,
        topic: str | None,
        evidence,
    ) -> float:

        if not topic:
            return 0.0

        text = evidence.text.lower()

        topic_signals = set(
            TOPIC_SIGNALS.get(
                topic,
                [],
            )
        )

        competing_signals = set()

        for other_topic, signals in TOPIC_SIGNALS.items():
            if other_topic == topic:
                continue

            for signal in signals:
                if signal.lower() in text:
                    competing_signals.add(
                        signal.lower()
                    )

        matched_topic = sum(
            1
            for signal in topic_signals
            if signal.lower() in text
        )

        matched_competing = len(
            competing_signals
        )

        if (
            matched_topic == 0
            and matched_competing > 0
        ):
            return min(
                0.20 * matched_competing,
                0.45,
            )

        return 0.0

    def _keyword_score(
        self,
        query: str,
        evidence,
        topic: str | None,
    ) -> float:

        direct_score = (
            self._direct_overlap_score(
                query,
                evidence,
            )
        )

        topic_score = (
            self._topic_score(
                topic,
                evidence,
            )
        )

        penalty = (
            self._topic_penalty(
                topic,
                evidence,
            )
        )

        score = (
            0.30 * direct_score
            + 0.70 * topic_score
            - penalty
        )

        return max(
            0.0,
            min(score, 1.0),
        )

    def _tfidf_scores(
        self,
        query: str,
    ):

        query_vector = (
            self.vectorizer.transform(
                [query]
            )
        )

        return cosine_similarity(
            query_vector,
            self.matrix,
        )[0]

    def search(
        self,
        query: str,
        top_k: int = 8,
    ) -> list[dict]:

        if not query.strip():
            return []

        topic = self._detect_topic(
            query
        )

        tfidf_scores = self._tfidf_scores(
            query
        )

        results = []

        for index, evidence in enumerate(
            self.evidence
        ):

            keyword_score = (
                self._keyword_score(
                    query,
                    evidence,
                    topic,
                )
            )

            tfidf_score = float(
                tfidf_scores[index]
            )

            hybrid_score = (
                self.keyword_weight
                * keyword_score
                + self.tfidf_weight
                * tfidf_score
            )

            results.append(
                {
                    "evidence": evidence,
                    "topic": topic,
                    "keyword_score": round(
                        keyword_score,
                        4,
                    ),
                    "tfidf_score": round(
                        tfidf_score,
                        4,
                    ),
                    "hybrid_score": round(
                        hybrid_score,
                        4,
                    ),
                }
            )

        results.sort(
            key=lambda item: item[
                "hybrid_score"
            ],
            reverse=True,
        )

        reranked = rerank(
            results,
            topic,
        )

        return reranked[:top_k]

    def search_by_market(
        self,
        query: str,
        market: str,
        top_k: int = 5,
    ) -> list[dict]:

        results = self.search(
            query,
            top_k=len(self.evidence),
        )

        filtered = [
            item
            for item in results
            if item["evidence"].market.lower()
            == market.lower()
        ]

        return filtered[:top_k]

    def search_all_markets(
        self,
        query: str,
        top_k_per_market: int = 3,
    ) -> dict:

        results = self.search(
            query,
            top_k=len(self.evidence),
        )

        grouped = defaultdict(list)

        for item in results:
            market = item["evidence"].market

            if len(
                grouped[market]
            ) < top_k_per_market:
                grouped[market].append(
                    item
                )

        return dict(grouped)


def print_results(
    results: list[dict],
) -> None:

    print(
        "\n"
        + "=" * 80
    )

    print(
        "HASAMEX — HYBRID RETRIEVAL"
    )

    print(
        "=" * 80
    )

    if results:
        print(
            f"\nDetected topic: "
            f"{results[0]['topic']}"
        )

    for rank, item in enumerate(
        results,
        start=1,
    ):

        evidence = item["evidence"]

        print(
            f"\nRank {rank}"
        )

        print(
            f"ID       : "
            f"{evidence.evidence_id}"
        )

        print(
            f"Market   : "
            f"{evidence.market}"
        )

        print(
            f"Expert   : "
            f"{evidence.expert}"
        )

        print(
            f"Timestamp: "
            f"{evidence.timestamp}"
        )

        print(
            f"Keyword  : "
            f"{item['keyword_score']}"
        )

        print(
            f"TF-IDF   : "
            f"{item['tfidf_score']}"
        )

        print(
            f"Hybrid   : "
            f"{item['hybrid_score']}"
        )

        print(
            f"Rerank   : "
            f"{item['rerank_score']}"
        )

        print(
            f"Positive : "
            f"{item['positive_hits']}"
        )

        print(
            f"Negative : "
            f"{item['negative_hits']}"
        )

        print(
            f"Quote    : "
            f"{evidence.text}"
        )


if __name__ == "__main__":

    store = EvidenceStore()

    retriever = HybridRetriever(
        store
    )

    query = (
        "What are the main barriers "
        "to robotic surgery adoption?"
    )

    results = retriever.search(
        query,
        top_k=10,
    )

    print_results(
        results
    )