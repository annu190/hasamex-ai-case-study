from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

GUIDE_FILE = DATA_DIR / "Interview_Guide.txt"


def load_interview_guide() -> list[dict]:
    """
    Load and parse the interview guide.

    Returns each question with a stable question ID.
    """

    text = GUIDE_FILE.read_text(encoding="utf-8")

    questions = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Match numbered questions such as:
        # 1. How would you describe...
        if line[0].isdigit() and ". " in line:

            number, question = line.split(". ", 1)

            if number.isdigit():

                questions.append(
                    {
                        "question_id": f"Q{int(number):02d}",
                        "number": int(number),
                        "question": question.strip(),
                    }
                )

    return questions


if __name__ == "__main__":

    questions = load_interview_guide()

    print("\n" + "=" * 60)
    print("HASAMEX — INTERVIEW GUIDE")
    print("=" * 60)

    print(
        f"\nLoaded questions: {len(questions)}"
    )

    for item in questions:

        print(
            f"\n{item['question_id']}: "
            f"{item['question']}"
        )