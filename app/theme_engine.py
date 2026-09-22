import json
from pathlib import Path

from app.evidence_store import EvidenceStore
from app.llm_synthesis import LLMSynthesizer
from app.hybrid_retrieval import HybridRetriever
from app.quote_verifier import verify_evidence


BASE_DIR = Path(__file__).resolve().parent.parent
GUIDE_FILE = BASE_DIR / "data" / "guide_answers.json"
THEME_FILE = BASE_DIR / "data" / "themes.json"

MARKETS = [
    "France",
    "Germany",
    "United Kingdom",
]


class ThemeEngine:
    def __init__(self):
        self.store = EvidenceStore()
        self.retriever = HybridRetriever(self.store)
        self.synthesizer = LLMSynthesizer(
            self.store,
            self.retriever,
        )

    def load_answers(self) -> dict:
        if not GUIDE_FILE.exists():
            raise FileNotFoundError(
                "guide_answers.json not found. "
                "Run: python -m app.guide_engine"
            )

        return json.loads(
            GUIDE_FILE.read_text(
                encoding="utf-8"
            )
        )

    def build_context(self, answers: dict) -> str:
        sections = []

        for question_id, question_data in answers.items():
            sections.append(
                f"{question_id}: "
                f"{question_data['question']}"
            )

            for market in MARKETS:
                result = question_data[
                    "markets"
                ][market]

                sections.append(
                    f"\nMarket: {market}\n"
                    f"Answer: {result['answer']}"
                )

                for evidence in result[
                    "evidence"
                ]:
                    sections.append(
                        f"Evidence ID: "
                        f"{evidence['evidence_id']}\n"
                        f"Timestamp: "
                        f"{evidence['timestamp']}\n"
                        f"Expert: "
                        f"{evidence['expert']}\n"
                        f"Quote: "
                        f"{evidence['quote']}"
                    )

            sections.append("\n---\n")

        return "\n".join(sections)

    def build_prompt(
        self,
        context: str,
    ) -> str:
        return f"""
You are an evidence-grounded market research analyst.

Analyze the verified interview answers below across
France, Germany, and the United Kingdom.

Identify the major cross-market themes and meaningful
market differences.

Focus on:
1. Adoption
2. Economics and ROI
3. Training
4. Clinical outcomes
5. Future growth
6. Purchasing timelines

Rules:
- Use ONLY the supplied evidence.
- Do not use outside knowledge.
- Do not invent facts.
- Do not invent quotes.
- Do not invent timestamps.
- Do not claim consensus unless multiple markets support it.
- Clearly distinguish common themes from differences.
- Do not rank the markets.
- Every supporting quote must be copied exactly.

Return JSON with exactly this structure:

{{
  "common_themes": [
    {{
      "theme": "theme name",
      "summary": "cross-market summary",
      "markets": ["France", "Germany"],
      "evidence": [
        {{
          "evidence_id": "ID",
          "market": "France",
          "expert": "expert name",
          "timestamp": "MM:SS",
          "quote": "exact quote"
        }}
      ]
    }}
  ],
  "market_differences": [
    {{
      "theme": "theme name",
      "summary": "description of the difference",
      "markets": [
        {{
          "market": "France",
          "position": "market-specific position"
        }},
        {{
          "market": "Germany",
          "position": "market-specific position"
        }},
        {{
          "market": "United Kingdom",
          "position": "market-specific position"
        }}
      ],
      "evidence": [
        {{
          "evidence_id": "ID",
          "market": "France",
          "expert": "expert name",
          "timestamp": "MM:SS",
          "quote": "exact quote"
        }}
      ]
    }}
  ]
}}

Verified interview evidence:
{context}
""".strip()

    def verify_evidence(
        self,
        evidence_items: list,
    ) -> list:

        verified = []

        for item in evidence_items:
            result = verify_evidence(
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
                result["verified"]
                and result["market"].lower()
                == item.get(
                    "market",
                    "",
                ).lower()
            ):
                verified.append(result)

        return verified

    def run(self) -> dict:
        answers = self.load_answers()
        context = self.build_context(answers)

        client = self.synthesizer._get_client()

        response = client.models.generate_content(
            model=self.synthesizer.model,
            contents=self.build_prompt(
                context
            ),
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

        for theme in result.get(
            "common_themes",
            [],
        ):
            theme["evidence"] = self.verify_evidence(
                theme.get(
                    "evidence",
                    [],
                )
            )

        for difference in result.get(
            "market_differences",
            [],
        ):
            difference["evidence"] = (
                self.verify_evidence(
                    difference.get(
                        "evidence",
                        [],
                    )
                )
            )

        THEME_FILE.write_text(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return result


if __name__ == "__main__":
    engine = ThemeEngine()
    result = engine.run()

    print("\n" + "=" * 70)
    print("HASAMEX — THEMES & DISAGREEMENTS")
    print("=" * 70)

    print(
        f"\nCommon themes: "
        f"{len(result.get('common_themes', []))}"
    )

    for theme in result.get(
        "common_themes",
        [],
    ):
        print(
            f"\n• {theme['theme']}"
        )
        print(
            f"  {theme['summary']}"
        )
        print(
            f"  Verified evidence: "
            f"{len(theme['evidence'])}"
        )

    print(
        f"\nMarket differences: "
        f"{len(result.get('market_differences', []))}"
    )

    for difference in result.get(
        "market_differences",
        [],
    ):
        print(
            f"\n• {difference['theme']}"
        )
        print(
            f"  {difference['summary']}"
        )
        print(
            f"  Verified evidence: "
            f"{len(difference['evidence'])}"
        )

    print(
        f"\nSaved to: {THEME_FILE}"
    )