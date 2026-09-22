from pathlib import Path
import re

from app.models import Evidence


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ---------------------------------------------------------
# Market codes
# ---------------------------------------------------------

MARKET_CODES = {
    "France": "FR",
    "Germany": "DE",
    "United Kingdom": "UK",
}


# ---------------------------------------------------------
# Transcript parser
# ---------------------------------------------------------

def parse_transcript(file_path: Path) -> dict:
    """
    Parse one expert transcript into structured evidence.

    Each evidence record preserves:
    - expert
    - role
    - market
    - timestamp
    - speaker
    - exact transcript text
    - source file
    - unique evidence ID
    """

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # -----------------------------------------------------
    # 1. Extract transcript metadata
    # -----------------------------------------------------

    expert = lines[0]

    # Remove the "Expert X – " prefix
    expert = re.sub(
        r"^Expert\s+\d+\s+[–-]\s*",
        "",
        expert,
    ).strip()

    role = ""
    market = ""

    for line in lines[:5]:

        if line.startswith("Role:"):
            role = line.replace(
                "Role:",
                "",
                1,
            ).strip()

        elif line.startswith("Market:"):
            market = line.replace(
                "Market:",
                "",
                1,
            ).strip()

    # -----------------------------------------------------
    # 2. Extract timestamped transcript turns
    # -----------------------------------------------------

    timestamp_pattern = re.compile(
        r"^\d{2}:\d{2}$"
    )

    turns = []

    current_timestamp = None
    current_text = []

    for line in lines[4:]:

        line = line.strip()

        if not line:
            continue

        # New timestamp
        if timestamp_pattern.match(line):

            # Save previous turn
            if (
                current_timestamp is not None
                and current_text
            ):

                turns.append(
                    {
                        "timestamp": current_timestamp,
                        "text": " ".join(
                            current_text
                        ).strip(),
                    }
                )

            current_timestamp = line
            current_text = []

        else:

            if current_timestamp is not None:
                current_text.append(line)

    # Save final turn
    if (
        current_timestamp is not None
        and current_text
    ):

        turns.append(
            {
                "timestamp": current_timestamp,
                "text": " ".join(
                    current_text
                ).strip(),
            }
        )

    # -----------------------------------------------------
    # 3. Convert transcript turns into Evidence objects
    # -----------------------------------------------------

    evidence = []

    market_code = MARKET_CODES.get(
        market,
        market[:2].upper(),
    )

    for turn in turns:

        raw_text = turn["text"]

        # Extract speaker and exact spoken text
        if ":" in raw_text:

            speaker, quote = raw_text.split(
                ":",
                1,
            )

            speaker = speaker.strip()
            quote = quote.strip()

        else:

            speaker = "Unknown"
            quote = raw_text.strip()

        # Create stable evidence ID
        evidence_id = (
            f"{market_code}-"
            f"{len(evidence) + 1:03d}"
        )

        evidence_item = Evidence(
            evidence_id=evidence_id,
            expert=expert,
            role=role,
            market=market,
            timestamp=turn["timestamp"],
            speaker=speaker,
            text=quote,
            source=file_path.name,
        )

        evidence.append(evidence_item)

    # -----------------------------------------------------
    # 4. Return complete transcript
    # -----------------------------------------------------

    return {
        "expert": expert,
        "role": role,
        "market": market,
        "source": file_path.name,
        "evidence": evidence,
    }


# ---------------------------------------------------------
# Load all transcripts
# ---------------------------------------------------------

def load_all_transcripts() -> list[dict]:
    """
    Load all transcript files from the data directory.
    """

    transcript_files = sorted(
        DATA_DIR.glob("Transcript_*.txt")
    )

    transcripts = []

    for file_path in transcript_files:

        transcript = parse_transcript(
            file_path
        )

        transcripts.append(transcript)

    return transcripts


# ---------------------------------------------------------
# Print parser summary
# ---------------------------------------------------------

def print_summary(
    transcripts: list[dict],
) -> None:
    """
    Print a human-readable summary for validation.
    """

    print("\n" + "=" * 70)
    print(
        "HASAMEX — TRANSCRIPT EVIDENCE PARSER"
    )
    print("=" * 70)

    print(
        f"\nLoaded transcripts: "
        f"{len(transcripts)}"
    )

    for transcript in transcripts:

        print("\n" + "-" * 70)

        print(
            f"Market     : "
            f"{transcript['market']}"
        )

        print(
            f"Expert     : "
            f"{transcript['expert']}"
        )

        print(
            f"Role       : "
            f"{transcript['role']}"
        )

        print(
            f"Source     : "
            f"{transcript['source']}"
        )

        print(
            f"Evidence   : "
            f"{len(transcript['evidence'])} turns"
        )

        print("\nExpert evidence:")

        for item in transcript["evidence"]:

            # Interviewer questions are retained in the
            # parsed data but excluded from expert evidence.
            if item.speaker.lower() == "interviewer":
                continue

            print(
                f"\n[{item.evidence_id}] "
                f"[{item.timestamp}] "
                f"{item.speaker}:"
            )

            print(
                f"  {item.text}"
            )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    transcripts = load_all_transcripts()

    print_summary(transcripts)