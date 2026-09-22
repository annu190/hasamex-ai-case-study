from app.models import Evidence
from app.parser import load_all_transcripts


class EvidenceStore:
    """
    Central store for all transcript evidence.

    This gives the rest of the application one consistent
    interface for accessing and filtering evidence.
    """

    def __init__(self):
        self.evidence: list[Evidence] = []

        self._load_evidence()

    def _load_evidence(self) -> None:
        """
        Load evidence from all transcripts.
        """

        transcripts = load_all_transcripts()

        for transcript in transcripts:
            self.evidence.extend(transcript["evidence"])

    def all(self) -> list[Evidence]:
        """
        Return all evidence.
        """

        return self.evidence

    def by_market(self, market: str) -> list[Evidence]:
        """
        Return evidence from a specific market.
        """

        return [
            item
            for item in self.evidence
            if item.market.lower() == market.lower()
        ]

    def by_expert(self, expert: str) -> list[Evidence]:
        """
        Return evidence from a specific expert.
        """

        return [
            item
            for item in self.evidence
            if item.expert.lower() == expert.lower()
        ]

    def expert_statements(self) -> list[Evidence]:
        """
        Return only statements made by experts.

        Interviewer questions are excluded.
        """

        return [
            item
            for item in self.evidence
            if item.speaker.lower() != "interviewer"
        ]

    def search_text(self, query: str) -> list[Evidence]:
        """
        Simple keyword-based search.

        This is intentionally NOT our final AI retrieval system.
        It gives us a deterministic baseline before embeddings.
        """

        query_words = set(
            query.lower().split()
        )

        results = []

        for item in self.expert_statements():

            text_words = set(
                item.text.lower().split()
            )

            if query_words & text_words:
                results.append(item)

        return results


if __name__ == "__main__":

    store = EvidenceStore()

    print("\n" + "=" * 60)
    print("HASAMEX EVIDENCE STORE")
    print("=" * 60)

    print(
        f"\nTotal evidence records: "
        f"{len(store.all())}"
    )

    print(
        f"Expert statements: "
        f"{len(store.expert_statements())}"
    )

    print("\nMarkets:")

    for market in ["France", "Germany", "United Kingdom"]:

        evidence = store.by_market(market)

        print(
            f"  {market}: {len(evidence)} records"
        )