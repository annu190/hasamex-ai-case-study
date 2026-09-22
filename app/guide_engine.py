import json
from pathlib import Path

from app.evidence_store import EvidenceStore
from app.guide import load_interview_guide
from app.hybrid_retrieval import HybridRetriever
from app.llm_synthesis import LLMSynthesizer
from app.quote_verifier import verify_evidence
from app.topic_map import QUESTION_TOPICS


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = BASE_DIR / "data" / "guide_answers.json"

MARKETS = [
    "France",
    "Germany",
    "United Kingdom",
]


class GuideEngine:
    def __init__(self):
        self.store = EvidenceStore()
        self.retriever = HybridRetriever(self.store)
        self.synthesizer = LLMSynthesizer(
            self.store,
            self.retriever,
        )
        self.guide = load_interview_guide()

    def _get_topic_evidence(
        self,
        question_id: str,
        question: str,
    ) -> dict:

        topic = QUESTION_TOPICS[question_id]["topic"]

        results = self.retriever.search(
            question,
            top_k=len(self.store.expert_statements()),
        )

        grouped = {
            market: []
            for market in MARKETS
        }

        for item in results:
            if item["topic"] != topic:
                continue

            evidence = item["evidence"]
            market = evidence.market

            if market in grouped:
                grouped[market].append(item)

        return {
            market: items[:5]
            for market, items in grouped.items()
        }

    def _build_prompt(
        self,
        question: str,
        evidence_by_market: dict,
    ) -> str:

        sections = []

        for market in MARKETS:
            evidence_items = evidence_by_market[market]

            if not evidence_items:
                sections.append(
                    f"{market}:\n"
                    "No relevant evidence retrieved."
                )
                continue

            context = (
                self.synthesizer
                .build_evidence_context(
                    evidence_items
                )
            )

            sections.append(
                f"{market}:\n{context}"
            )

        evidence_context = "\n\n---\n\n".join(
            sections
        )

        return f"""
You are an evidence-grounded market research assistant.

Answer the interview question separately for:
- France
- Germany
- United Kingdom

Use ONLY the evidence provided below.

Rules:
- Do not use outside knowledge.
- Do not invent facts.
- Do not invent quotes.
- Do not invent timestamps.
- Do not infer unsupported information.
- Keep each market separate.
- Answer only what the question asks.
- Do not mix evidence between markets.
- Every quote must be copied exactly.
- If evidence is insufficient for a market, say:
  "Insufficient evidence in the provided transcript."

Return JSON with exactly this structure:

{{
  "markets": {{
    "France": {{
      "answer": "concise answer",
      "evidence": [
        {{
          "evidence_id": "ID",
          "quote": "exact quote",
          "timestamp": "MM:SS",
          "expert": "expert name",
          "market": "France"
        }}
      ]
    }},
    "Germany": {{
      "answer": "concise answer",
      "evidence": []
    }},
    "United Kingdom": {{
      "answer": "concise answer",
      "evidence": []
    }}
  }}
}}

Question:
{question}

Evidence:
{evidence_context}
""".strip()

    def _generate_question(
        self,
        question_id: str,
        question: str,
    ) -> dict:

        evidence_by_market = self._get_topic_evidence(
            question_id,
            question,
        )

        client = self.synthesizer._get_client()

        prompt = self._build_prompt(
            question,
            evidence_by_market,
        )

        response = client.models.generate_content(
            model=self.synthesizer.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )

        try:
            result = json.loads(
                response.text.strip()
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        output = {
            "question": question,
            "markets": {},
        }

        for market in MARKETS:
            market_result = result.get(
                "markets",
                {},
            ).get(
                market,
                {},
            )

            verified_evidence = []

            for item in market_result.get(
                "evidence",
                [],
            ):
                verification = verify_evidence(
                    quote=item.get(
                        "quote",
                        "",
                    ),
                    evidence_id=item.get(
                        "evidence_id"
                    ),
                    store=self.store,
                )

                if (
                    verification["verified"]
                    and verification["market"].lower()
                    == market.lower()
                ):
                    verified_evidence.append(
                        verification
                    )

            answer = market_result.get(
                "answer",
                (
                    "Insufficient evidence in the "
                    "provided transcript."
                ),
            )

            if not verified_evidence:
                answer = (
                    "The generated answer could not be "
                    "verified against the source evidence."
                )

            output["markets"][market] = {
                "answer": answer,
                "evidence": verified_evidence,
                "verified": bool(
                    verified_evidence
                ),
                "retrieved_count": len(
                    evidence_by_market[market]
                ),
                "market": market,
            }

        return output

    def generate_all(self) -> dict:

        output = {}

        for question_item in self.guide:
            question_id = question_item[
                "question_id"
            ]
            question = question_item[
                "question"
            ]

            print(
                f"Generating {question_id}..."
            )

            output[question_id] = (
                self._generate_question(
                    question_id,
                    question,
                )
            )

        return output

    def save(self, results: dict) -> None:
        CACHE_FILE.write_text(
            json.dumps(
                results,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def run(self) -> dict:
        results = self.generate_all()
        self.save(results)
        return results


if __name__ == "__main__":
    engine = GuideEngine()
    results = engine.run()

    print("\n" + "=" * 70)
    print("HASAMEX — INTERVIEW GUIDE ENGINE")
    print("=" * 70)

    for question_id, question_data in results.items():

        print(
            f"\n{question_id}: "
            f"{question_data['question']}"
        )

        for market, result in question_data[
            "markets"
        ].items():

            print(f"\n  {market}")
            print(
                f"  Answer: "
                f"{result['answer']}"
            )
            print(
                f"  Verified evidence: "
                f"{len(result['evidence'])}"
            )

    print(
        f"\nSaved to: {CACHE_FILE}"
    )