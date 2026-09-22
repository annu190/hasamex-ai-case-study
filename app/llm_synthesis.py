import json
import os

from app.evidence_store import EvidenceStore
from app.quote_verifier import verify_evidence
from app.hybrid_retrieval import HybridRetriever


DEFAULT_MODEL = "gemini-3.5-flash-lite"


class LLMSynthesizer:
    def __init__(
        self,
        store: EvidenceStore,
        retriever: HybridRetriever,
    ):
        self.store = store
        self.retriever = retriever
        self.api_key = os.getenv(
            "GEMINI_API_KEY"
        )
        self.model = os.getenv(
            "LLM_MODEL",
            DEFAULT_MODEL,
        )

    def _get_client(self):
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Google GenAI SDK is not installed. "
                "Run: pip install -U google-genai"
            ) from exc

        return genai.Client(
            api_key=self.api_key
        )

    def build_evidence_context(
        self,
        evidence_items: list,
    ) -> str:

        context = []

        for item in evidence_items:

            evidence = item[
                "evidence"
            ]

            context.append(
                f"Evidence ID: "
                f"{evidence.evidence_id}\n"
                f"Expert: "
                f"{evidence.expert}\n"
                f"Role: "
                f"{evidence.role}\n"
                f"Market: "
                f"{evidence.market}\n"
                f"Timestamp: "
                f"{evidence.timestamp}\n"
                f"Quote: "
                f"{evidence.text}\n"
            )

        return "\n---\n".join(
            context
        )

    def build_prompt(
        self,
        question: str,
        evidence_items: list,
    ) -> str:

        context = (
            self.build_evidence_context(
                evidence_items
            )
        )

        return f"""
You are an evidence-grounded market research assistant.

Answer the question using ONLY the evidence provided below.

Strict rules:

- Do not invent facts.
- Do not invent quotes.
- Do not invent timestamps.
- Do not use outside knowledge.
- Do not infer unsupported information.
- Every quote must be copied exactly from the provided evidence.
- Use only evidence that directly supports the answer.
- Do not cite evidence that does not support the answer.
- If the evidence does not support an answer, say:
  "Insufficient evidence in the provided transcripts."

Return JSON with exactly these fields:

{{
  "answer": "concise synthesis",
  "evidence": [
    {{
      "evidence_id": "ID",
      "quote": "exact quote from the evidence",
      "timestamp": "MM:SS",
      "expert": "expert name",
      "market": "market"
    }}
  ]
}}

Question:
{question}

Evidence:
{context}
""".strip()

    def generate(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict:

        retrieved = self.retriever.search(
            question,
            top_k=top_k,
        )

        if not retrieved:
            return {
                "answer": (
                    "Insufficient evidence in the "
                    "provided transcripts."
                ),
                "evidence": [],
                "verified": False,
                "retrieved_count": 0,
            }

        client = self._get_client()

        prompt = self.build_prompt(
            question,
            retrieved,
        )

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": (
                    "application/json"
                ),
            },
        )

        raw_text = response.text.strip()

        try:
            result = json.loads(
                raw_text
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        verified_evidence = []

        for item in result.get(
            "evidence",
            [],
        ):

            evidence_id = item.get(
                "evidence_id"
            )

            quote = item.get(
                "quote",
                "",
            )

            verification = (
                verify_evidence(
                    quote=quote,
                    evidence_id=evidence_id,
                    store=self.store,
                )
            )

            if verification[
                "verified"
            ]:

                verified_evidence.append(
                    verification
                )

        result[
            "evidence"
        ] = verified_evidence

        result[
            "verified"
        ] = bool(
            verified_evidence
        )

        result[
            "retrieved_count"
        ] = len(retrieved)

        if not verified_evidence:
            result[
                "answer"
            ] = (
                "The generated answer could not "
                "be verified against the source "
                "evidence."
            )

        return result


if __name__ == "__main__":

    store = EvidenceStore()

    retriever = HybridRetriever(
        store
    )

    synthesizer = LLMSynthesizer(
        store,
        retriever,
    )

    question = (
        "What are the main barriers "
        "to robotic surgery adoption?"
    )

    try:

        result = synthesizer.generate(
            question,
            top_k=5,
        )

        print(
            "\nHASAMEX — "
            "RETRIEVAL + GEMINI\n"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    except Exception as error:

        print(
            f"\nLLM synthesis unavailable:\n"
            f"{error}"
        )