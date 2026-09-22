import re

from app.evidence_store import EvidenceStore
from app.topic_map import QUESTION_TOPICS


class RetrievalEngine:
    """
    Deterministic baseline retrieval engine.

    It combines:
    1. Query keyword matching
    2. Research-topic detection
    3. Topic-specific evidence matching
    4. Topic-specific relevance signals
    5. Cross-topic penalties

    This is our baseline before introducing semantic embeddings.
    """

    def __init__(self, evidence_store: EvidenceStore):
        self.store = evidence_store

    # ---------------------------------------------------------
    # Text normalization
    # ---------------------------------------------------------

    @staticmethod
    def tokenize(text: str) -> set[str]:
        """
        Convert text into normalized tokens.
        """

        text = text.lower()

        words = re.findall(
            r"[a-zA-Z]+",
            text,
        )

        return set(words)

    # ---------------------------------------------------------
    # Topic detection
    # ---------------------------------------------------------

    def detect_topic(self, query: str) -> str | None:
        """
        Detect the most likely research topic.

        Specific phrases such as:
            "barriers to adoption"

        receive a much stronger score than generic words such as:
            "adoption"
        """

        query_lower = query.lower()

        topic_scores = {}

        for question_id, info in QUESTION_TOPICS.items():

            score = 0

            # -------------------------------------------------
            # 1. Priority phrases
            # -------------------------------------------------

            for phrase in info.get(
                "priority_phrases",
                [],
            ):

                if phrase.lower() in query_lower:
                    score += 10

            # -------------------------------------------------
            # 2. Individual keywords
            # -------------------------------------------------

            for keyword in info["keywords"]:

                keyword_lower = keyword.lower()

                if keyword_lower in query_lower:

                    # "adoption" is intentionally weak because
                    # it appears in several research questions.
                    if keyword_lower == "adoption":
                        score += 1
                    else:
                        score += 2

            topic_scores[info["topic"]] = score

        if not topic_scores:
            return None

        best_topic = max(
            topic_scores,
            key=topic_scores.get,
        )

        if topic_scores[best_topic] == 0:
            return None

        return best_topic

    # ---------------------------------------------------------
    # Find topic information
    # ---------------------------------------------------------

    def get_topic_info(
        self,
        topic: str | None,
    ) -> dict | None:
        """
        Return the configuration for a detected topic.
        """

        if topic is None:
            return None

        for info in QUESTION_TOPICS.values():

            if info["topic"] == topic:
                return info

        return None

    # ---------------------------------------------------------
    # Score evidence
    # ---------------------------------------------------------

    def score_evidence(
        self,
        query: str,
        evidence,
        topic: str | None = None,
    ) -> float:
        """
        Calculate a transparent relevance score.

        The score combines:

        1. Direct query overlap
        2. Topic-specific keyword overlap
        3. Priority phrase matching
        4. Strong topic signals
        5. Cross-topic penalties

        The goal is to retrieve evidence that actually
        answers the detected research topic rather than
        simply matching generic words.
        """

        query_tokens = self.tokenize(query)
        text_tokens = self.tokenize(evidence.text)

        if not query_tokens or not text_tokens:
            return 0.0

        # -----------------------------------------------------
        # Generic words that should not drive retrieval
        # -----------------------------------------------------

        ignored_terms = {
            "what",
            "are",
            "the",
            "main",
            "is",
            "how",
            "would",
            "you",
            "describe",
            "current",
            "in",
            "your",
            "market",
            "to",
            "of",
            "and",
            "do",
            "does",
            "did",
            "for",
            "on",
            "a",
            "an",
            "with",
            "over",
            "next",
        }

        useful_query_tokens = (
            query_tokens - ignored_terms
        )

        # -----------------------------------------------------
        # 1. Direct query overlap
        # -----------------------------------------------------

        direct_overlap = (
            useful_query_tokens & text_tokens
        )

        keyword_score = (
            len(direct_overlap) * 2
        )

        # -----------------------------------------------------
        # 2. Topic-specific keyword scoring
        # -----------------------------------------------------

        topic_score = 0.0

        topic_info = self.get_topic_info(topic)

        if topic_info:

            topic_keywords = set()

            for keyword in topic_info["keywords"]:

                topic_keywords.update(
                    self.tokenize(keyword)
                )

            topic_overlap = (
                text_tokens & topic_keywords
            )

            # Topic keywords are stronger than
            # generic query overlap.
            topic_score += (
                len(topic_overlap) * 3
            )

            # -------------------------------------------------
            # 3. Priority phrase matching
            # -------------------------------------------------

            evidence_text_lower = (
                evidence.text.lower()
            )

            for phrase in topic_info.get(
                "priority_phrases",
                [],
            ):

                phrase_lower = phrase.lower()

                if phrase_lower in evidence_text_lower:
                    topic_score += 5

        # -----------------------------------------------------
        # 4. Strong topic-specific signals
        # -----------------------------------------------------
        #
        # These signals give additional weight to evidence
        # that directly represents the detected topic.

        strong_signals = {

            "adoption": [
                "adoption",
                "access",
                "standard",
                "concentrated",
            ],

            "barriers": [
                "barrier",
                "barriers",
                "funding",
                "cost",
                "capital",
                "budget",
                "finances",
                "under pressure",
                "holding",
                "stalls",
            ],

            "economics": [
                "roi",
                "economic case",
                "economics",
                "cost",
                "maintenance",
                "procedure volume",
                "utilisation",
                "utilization",
                "pay for itself",
                "total cost of ownership",
                "service contracts",
            ],

            "training_and_outcomes": [
                "training",
                "trained",
                "surgeon",
                "theatre staff",
                "clinical outcomes",
                "outcomes",
                "length of stay",
                "clinical position",
            ],

            "future_adoption": [
                "growth",
                "annually",
                "accelerate",
                "gradual",
                "future",
                "next",
                "years",
                "procedure growth",
            ],

            "purchase_timeline": [
                "months",
                "timeline",
                "procurement",
                "purchase",
                "capital cycle",
                "budget cycle",
                "management",
                "align",
            ],
        }

        if topic in strong_signals:

            evidence_text_lower = (
                evidence.text.lower()
            )

            for signal in strong_signals[topic]:

                if signal.lower() in evidence_text_lower:
                    topic_score += 4

        # -----------------------------------------------------
        # 5. Cross-topic penalties
        # -----------------------------------------------------
        #
        # Some evidence contains generic words such as
        # "adoption", "growth", or "training" but primarily
        # answers a different research question.
        #
        # These signals reduce the score when they strongly
        # indicate another topic.

        cross_topic_signals = {

            "adoption": [
                "growth",
                "annually",
                "months",
                "procurement",
                "capital cycle",
            ],

            "barriers": [
                "procedure growth",
                "annually",
                "high single digits",
                "low double digits",
                "months",
                "six to twelve months",
                "six to nine months",
                "nine to eighteen months",
            ],

            "economics": [
                "months",
                "capital cycle",
                "budget cycle",
            ],

            "training_and_outcomes": [
                "months",
                "capital cycle",
                "procedure growth",
                "annually",
            ],

            "future_adoption": [
                "months",
                "procurement",
                "capital cycle",
                "budget cycle",
            ],

            "purchase_timeline": [
                "annually",
                "procedure growth",
                "clinical outcomes",
            ],
        }

        if topic in cross_topic_signals:

            evidence_text_lower = (
                evidence.text.lower()
            )

            for signal in cross_topic_signals[topic]:

                if signal.lower() in evidence_text_lower:
                    topic_score -= 4

        # -----------------------------------------------------
        # 6. Final score
        # -----------------------------------------------------

        final_score = (
            keyword_score
            + topic_score
        )

        # Never return a negative relevance score.
        return max(
            final_score,
            0.0,
        )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[float, object]]:
        """
        Retrieve the most relevant expert evidence.

        Returns:

            [
                (score, evidence),
                ...
            ]
        """

        topic = self.detect_topic(query)

        scored_results = []

        for evidence in self.store.expert_statements():

            score = self.score_evidence(
                query=query,
                evidence=evidence,
                topic=topic,
            )

            if score > 0:

                scored_results.append(
                    (score, evidence)
                )

        # Highest score first
        scored_results.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return scored_results[:top_k]


# ---------------------------------------------------------
# Test retrieval
# ---------------------------------------------------------

if __name__ == "__main__":

    store = EvidenceStore()

    engine = RetrievalEngine(store)

    query = "What are the main barriers to adoption?"

    print("\n" + "=" * 70)
    print("HASAMEX — RETRIEVAL BASELINE")
    print("=" * 70)

    print(
        f"\nQuery:\n{query}"
    )

    topic = engine.detect_topic(query)

    print(
        f"\nDetected topic: {topic}"
    )

    results = engine.search(
        query=query,
        top_k=10,
    )

    print("\nRetrieved evidence:")

    for rank, (score, evidence) in enumerate(
        results,
        start=1,
    ):

        print("\n" + "-" * 70)

        print(
            f"Rank      : {rank}"
        )

        print(
            f"Score     : {score}"
        )

        print(
            f"Evidence  : {evidence.evidence_id}"
        )

        print(
            f"Market    : {evidence.market}"
        )

        print(
            f"Expert    : {evidence.expert}"
        )

        print(
            f"Timestamp : {evidence.timestamp}"
        )

        print(
            f"Quote     : {evidence.text}"
        )