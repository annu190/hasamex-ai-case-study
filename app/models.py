from dataclasses import dataclass


@dataclass
class Evidence:
    """
    A single traceable piece of evidence from an expert transcript.
    """

    evidence_id: str
    expert: str
    role: str
    market: str
    timestamp: str
    speaker: str
    text: str
    source: str

    @property
    def citation(self) -> str:
        """
        Human-readable citation for the UI.
        """
        return f"{self.expert} | {self.market} | {self.timestamp}"

    def to_dict(self) -> dict:
        """
        Convert the evidence object into a dictionary.
        Useful for JSON, APIs and the UI.
        """
        return {
            "evidence_id": self.evidence_id,
            "expert": self.expert,
            "role": self.role,
            "market": self.market,
            "timestamp": self.timestamp,
            "speaker": self.speaker,
            "text": self.text,
            "source": self.source,
        }
    