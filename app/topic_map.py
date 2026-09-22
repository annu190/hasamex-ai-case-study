QUESTION_TOPICS = {

    "Q01": {
        "topic": "adoption",

        "priority_phrases": [
            "current adoption",
            "adoption today",
            "current market adoption",
            "describe adoption",
            "adoption in your market",
        ],

        "keywords": [
            "adoption",
            "growing",
            "increasing",
            "hospitals",
            "access",
            "market",
        ],
    },

    "Q02": {
        "topic": "barriers",

        "priority_phrases": [
            "main barriers",
            "barriers to adoption",
            "barrier to adoption",
            "holding adoption back",
            "what is holding adoption back",
        ],

        "keywords": [
            "barrier",
            "barriers",
            "cost",
            "funding",
            "capital",
            "budget",
            "utilisation",
            "utilization",
            "training",
        ],
    },

    "Q03": {
        "topic": "economics",

        "priority_phrases": [
            "hospital budgets",
            "purchasing decisions",
            "return on investment",
            "economic case",
            "pay for itself",
        ],

        "keywords": [
            "ROI",
            "economic",
            "economics",
            "cost",
            "budget",
            "utilisation",
            "utilization",
            "maintenance",
            "procedure volume",
            "pay",
        ],
    },

    "Q04": {
        "topic": "training_and_outcomes",

        "priority_phrases": [
            "surgeon training",
            "clinical outcomes",
            "training and clinical outcomes",
            "training capacity",
        ],

        "keywords": [
            "training",
            "surgeon",
            "clinical",
            "outcomes",
            "staff",
            "utilisation",
            "utilization",
        ],
    },

    "Q05": {
        "topic": "future_adoption",

        "priority_phrases": [
            "next 3-5 years",
            "next three to five years",
            "adoption trend",
            "future adoption",
            "over the next",
            "expect over the next",
        ],

        "keywords": [
            "future",
            "growth",
            "accelerate",
            "gradual",
            "increase",
            "years",
            "annually",
        ],
    },

    "Q06": {
        "topic": "purchase_timeline",

        "priority_phrases": [
            "decision making timeline",
            "decision-making timeline",
            "purchase timeline",
            "purchasing timeline",
            "how long",
            "purchase process",
        ],

        "keywords": [
            "timeline",
            "months",
            "purchase",
            "procurement",
            "capital cycle",
            "decision",
        ],
    },
}


if __name__ == "__main__":

    print("\nHASAMEX TOPIC MAP\n")

    for question_id, info in QUESTION_TOPICS.items():

        print(
            f"{question_id} → "
            f"{info['topic']}"
        )