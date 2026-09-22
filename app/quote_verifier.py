import re

from app.evidence_store import EvidenceStore


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_quote(quote: str, evidence) -> bool:
    if not quote or not evidence:
        return False

    source_text = normalize_text(evidence.text)
    candidate_quote = normalize_text(quote)

    return candidate_quote in source_text


def verify_evidence(
    quote: str,
    evidence_id: str,
    store: EvidenceStore,
) -> dict:

    matches = [
        evidence
        for evidence in store.expert_statements()
        if evidence.evidence_id == evidence_id
    ]

    if not matches:
        return {
            "verified": False,
            "reason": "Evidence ID not found",
            "evidence_id": evidence_id,
        }

    evidence = matches[0]
    verified = verify_quote(quote, evidence)

    return {
        "verified": verified,
        "evidence_id": evidence.evidence_id,
        "expert": evidence.expert,
        "market": evidence.market,
        "timestamp": evidence.timestamp,
        "quote": quote,
        "reason": (
            "Quote verified against source evidence"
            if verified
            else "Quote not found in source evidence"
        ),
    }


if __name__ == "__main__":
    store = EvidenceStore()

    evidence = store.expert_statements()[0]

    real_quote = evidence.text
    fake_quote = "This is a completely fabricated statement."

    print("\nHASAMEX — QUOTE VERIFIER\n")

    print("Real quote:")
    print(verify_quote(real_quote, evidence))

    print("\nFake quote:")
    print(verify_quote(fake_quote, evidence))

    print("\nDetailed verification:")
    print(
        verify_evidence(
            real_quote,
            evidence.evidence_id,
            store,
        )
    )