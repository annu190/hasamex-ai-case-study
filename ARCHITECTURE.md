# System Architecture

## Evidence-First Research Pipeline

```text
                         ┌──────────────────────────┐
                         │   Expert Transcripts     │
                         │ France / Germany / UK    │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │    Transcript Parser      │
                         │                          │
                         │ Expert / Role / Market   │
                         │ Timestamp / Speaker     │
                         │ Source / Evidence ID    │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │      Evidence Store      │
                         │                          │
                         │ 42 transcript records    │
                         │ 21 expert statements     │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
          ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
          │ Interview      │ │ Hybrid         │ │ Evidence       │
          │ Guide Engine   │ │ Retrieval      │ │ Explorer       │
          └───────┬────────┘ └───────┬────────┘ └────────────────┘
                  │                  │
                  ▼                  ▼
          ┌────────────────┐ ┌────────────────┐
          │ 18 Market      │ │ Relevant       │
          │ Answers        │ │ Evidence       │
          └───────┬────────┘ └───────┬────────┘
                  │                  │
                  ▼                  ▼
          ┌────────────────┐ ┌────────────────┐
          │ Theme Engine   │ │ Gemini LLM     │
          │                │ │                │
          │ Common themes  │ │ Synthesis only │
          │ Differences    │ │ No source      │
          └───────┬────────┘ └───────┬────────┘
                  │                  │
                  │                  ▼
                  │         ┌────────────────┐
                  │         │ Structured     │
                  │         │ Answer         │
                  │         └───────┬────────┘
                  │                 │
                  │                 ▼
                  │         ┌────────────────┐
                  │         │ Quote          │
                  │         │ Verification   │
                  │         └───────┬────────┘
                  │                 │
                  │          ┌──────┴──────┐
                  │          │             │
                  │          ▼             ▼
                  │       VERIFIED      REJECTED
                  │          │             │
                  └──────────┼─────────────┘
                             ▼
                  ┌────────────────────────┐
                  │   Streamlit Interface  │
                  │                        │
                  │ Overview               │
                  │ Interview Guide        │
                  │ Compare Markets        │
                  │ Themes & Disagreements │
                  │ Evidence Explorer      │
                  │ Ask Research Assistant │
                  │ Source Management      │
                  └────────────────────────┘
```

## Core Data Flow

```text
Transcript
    ↓
Parse
    ↓
Evidence ID
    ↓
Retrieve
    ↓
Grounded Context
    ↓
LLM Synthesis
    ↓
Quote Verification
    ↓
Verified Answer
```

## Evidence Object

Every evidence record maintains:

```text
evidence_id
expert
role
market
timestamp
speaker
text
source
```

This metadata allows every generated research finding to be traced back to the original transcript.

## Hallucination Control

The system uses two independent controls.

### Prompt-level grounding

The model is instructed to:

- Use only retrieved evidence
- Never invent facts
- Never invent quotes
- Never invent timestamps
- Avoid unsupported inference

### Code-level verification

After generation:

```text
Generated Quote
       ↓
Evidence ID
       ↓
Original Evidence
       ↓
Exact Quote Match
       ↓
Verified / Rejected
```

A generated quote that does not exist in the source evidence cannot be presented as verified.

## Scaling

Current:

```text
3 transcripts
42 records
21 expert statements
```

Larger deployment:

```text
30+ transcripts
       ↓
Chunking
       ↓
Embeddings
       ↓
Vector Database
       ↓
Metadata Filtering
       ↓
Reranking
       ↓
LLM
       ↓
Verification
```

The evidence metadata remains unchanged, allowing the retrieval implementation to scale without changing the application's core research workflow.

## Demo Flow

1. Open **Overview** and show the research dataset.
2. Open **Interview Guide** and select a question.
3. Expand an answer to show exact supporting evidence.
4. Open **Compare Markets** and compare the same question across countries.
5. Open **Themes & Disagreements** to show common themes and market differences.
6. Open **Evidence Explorer** and search terms such as `ROI`, `training`, or `budget`.
7. Open **Ask Research Assistant** and ask:
   `What are the main barriers to robotic surgery adoption?`
8. Show the answer and its verified evidence trail.
9. Ask an unsupported question such as:
   `What is the market share of robotic surgery manufacturers in France?`
10. Show that the system does not present unsupported information as verified.

## Key Explanation

> I designed the system around evidence rather than treating the LLM as the source of truth. The transcripts are parsed into structured evidence records containing the expert, market, timestamp and source. Retrieval selects the relevant evidence, Gemini synthesizes an answer from that evidence, and a separate verification layer checks every generated quote against the original transcript. If the quote cannot be verified, it isn't presented as a verified answer.
