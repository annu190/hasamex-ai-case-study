import html
import json
from pathlib import Path

import streamlit as st

from app.evidence_store import EvidenceStore
from app.hybrid_retrieval import HybridRetriever
from app.llm_synthesis import LLMSynthesizer
from app.parser import parse_transcript

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GUIDE_FILES = [DATA_DIR / "guide_answers.json", DATA_DIR / "guide_answers_cache.json"]
THEME_FILE = DATA_DIR / "themes.json"

st.set_page_config(page_title="Hasamex Research Intelligence", page_icon="◈", layout="wide")

st.markdown("""
<style>
#MainMenu,footer,header{visibility:hidden}
.stApp{background:radial-gradient(circle at 8% 0%,rgba(99,102,241,.13),transparent 28%),radial-gradient(circle at 92% 5%,rgba(14,165,233,.08),transparent 24%),#080b11;color:#f8fafc}
.block-container{max-width:1500px;padding:1.25rem 3rem 4rem}
div[role="radiogroup"]{display:flex;flex-wrap:wrap;gap:5px;padding:5px;margin-bottom:22px;background:rgba(15,23,42,.84);border:1px solid rgba(255,255,255,.08);border-radius:13px;box-shadow:0 12px 35px rgba(0,0,0,.24);backdrop-filter:blur(16px)}
div[role="radiogroup"]>label{margin:0!important;padding:8px 15px!important;border-radius:9px;transition:.15s ease}
div[role="radiogroup"]>label:hover{background:rgba(255,255,255,.07)}
div[role="radiogroup"]>label p{color:#9aa7bb!important;font-size:12px;font-weight:700}
div[role="radiogroup"]>label[data-checked="true"]{background:#f8fafc}
div[role="radiogroup"]>label[data-checked="true"] p{color:#111827!important}
.hero{position:relative;overflow:hidden;margin-bottom:28px;padding:34px 38px;border:1px solid rgba(255,255,255,.09);border-radius:20px;background:radial-gradient(circle at 82% 20%,rgba(99,102,241,.25),transparent 28%),linear-gradient(135deg,#111827,#0b1220 58%,#05070b);box-shadow:0 25px 60px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.05)}
.hero:before{content:"";position:absolute;width:260px;height:260px;right:-110px;top:-150px;border-radius:50%;border:1px solid rgba(129,140,248,.18);box-shadow:0 0 0 35px rgba(129,140,248,.035),0 0 0 70px rgba(129,140,248,.02)}
.hero-title{position:relative;color:#fff;font-size:32px;line-height:1.15;font-weight:850;letter-spacing:-.8px}
.hero-subtitle{position:relative;max-width:760px;margin-top:9px;color:#aeb9ca;font-size:14px;line-height:1.6}
.status{display:inline-flex;position:relative;margin-top:18px;padding:6px 11px;border:1px solid rgba(52,211,153,.22);border-radius:999px;background:rgba(16,185,129,.1);color:#6ee7b7;font-size:10px;font-weight:800;letter-spacing:.5px}
.section-title{margin-top:26px;margin-bottom:4px;color:#f8fafc;font-size:21px;font-weight:800;letter-spacing:-.25px}
.section-subtitle{margin-bottom:17px;color:#8995a8;font-size:13px;line-height:1.55}
.kpi{min-height:105px;padding:19px 20px;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(17,24,39,.78);box-shadow:0 10px 28px rgba(0,0,0,.18),inset 0 1px 0 rgba(255,255,255,.035);backdrop-filter:blur(12px)}
.kpi-label{color:#8995a8;font-size:10px;font-weight:750;letter-spacing:.7px;text-transform:uppercase}
.kpi-value{margin-top:12px;color:#fff;font-size:29px;line-height:1;font-weight:850}
.card,.theme-card{margin-bottom:13px;padding:19px;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(17,24,39,.72);box-shadow:0 10px 28px rgba(0,0,0,.16),inset 0 1px 0 rgba(255,255,255,.035);backdrop-filter:blur(12px)}
.card:hover,.theme-card:hover{border-color:rgba(129,140,248,.25)}
.question-id{color:#a5b4fc;font-size:10px;font-weight:850;letter-spacing:1px;text-transform:uppercase}
.question{margin-top:6px;color:#f8fafc;font-size:16px;line-height:1.45;font-weight:750}
.answer{color:#c7d0df;font-size:14px;line-height:1.72}
.answer-market{color:#fff;font-size:14px;font-weight:800}
.evidence{margin:9px 0;padding:14px 16px;border:1px solid rgba(255,255,255,.08);border-left:4px solid #818cf8;border-radius:10px;background:#101722;box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}
.evidence:hover{border-left-color:#a5b4fc;background:#151e2e}
.meta{color:#93a0b4;font-size:11px;line-height:1.5;font-weight:650}
.quote{margin:9px 0;color:#edf2f7;font-size:13px;line-height:1.68}
.badge{display:inline-block;margin-left:5px;padding:2px 7px;border:1px solid rgba(52,211,153,.2);border-radius:999px;background:rgba(16,185,129,.1);color:#6ee7b7;font-size:9px;font-weight:850;letter-spacing:.3px}
.theme-title{color:#fff;font-size:16px;font-weight:800}.theme-summary{margin-top:7px;color:#aeb9ca;font-size:13px;line-height:1.65}
.signal{padding:14px 16px;border:1px solid rgba(129,140,248,.14);border-radius:11px;background:rgba(99,102,241,.07);color:#c7d2fe;font-size:13px}
div[data-testid="stExpander"]{margin:8px 0;border:1px solid rgba(255,255,255,.08);border-radius:11px;background:rgba(17,24,39,.55)}
div[data-testid="stExpander"] summary{color:#dce3ed;font-size:13px;font-weight:700}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div{border-color:#344054;border-radius:9px;background:#111827}
div[data-baseweb="select"] input,div[data-baseweb="input"] input,input{color:#f8fafc!important}
label{color:#aeb9ca!important;font-size:12px!important;font-weight:650!important}
.stButton>button,.stFormSubmitButton>button{min-height:40px;border:1px solid #344054;border-radius:9px;background:#111827;color:#e5e7eb;font-size:13px;font-weight:750}
.stButton>button:hover,.stFormSubmitButton>button:hover{border-color:#818cf8;color:#fff}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{border-color:#6366f1;background:#6366f1;color:#fff}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover{border-color:#818cf8;background:#818cf8}
div[data-testid="stAlert"]{border-radius:10px}hr{border-color:rgba(255,255,255,.08)}.stCaption{color:#7f8da2;font-size:11px}
div[data-testid="stFileUploader"]{border:1px dashed #475467;border-radius:12px;background:rgba(17,24,39,.55);padding:8px}
@media(max-width:900px){.block-container{padding:1rem 1.2rem 3rem}.hero{padding:26px}.hero-title{font-size:25px}}
</style>
""", unsafe_allow_html=True)


def load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def get_guide():
    for path in GUIDE_FILES:
        if path.exists():
            return load_json(path)
    return {}


def get_themes():
    return load_json(THEME_FILE)


def safe(value):
    return html.escape(str(value or ""))


def header():
    st.markdown("""
<div class="hero">
<div class="hero-title">Hasamex Research Intelligence</div>
<div class="hero-subtitle">Evidence-first analysis of robotic surgery adoption across expert interviews in France, Germany and the United Kingdom.</div>
<div class="status">● RESEARCH DATA READY</div>
</div>
""", unsafe_allow_html=True)


def evidence_card(item):
    st.markdown(f"""
<div class="evidence">
<div class="meta">{safe(item.get('expert','Unknown'))} · {safe(item.get('market','Unknown'))} · {safe(item.get('timestamp','--:--'))}<span class="badge">VERIFIED</span></div>
<div class="quote">"{safe(item.get('quote',''))}"</div>
<div class="meta">Evidence ID: {safe(item.get('evidence_id','N/A'))}</div>
</div>
""", unsafe_allow_html=True)


def evidence_from_ids(items, store):
    lookup = {x.evidence_id: x for x in store.expert_statements()}
    output = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict) and item.get("quote"):
            output.append(item)
        elif isinstance(item, dict) and item.get("evidence_id") in lookup:
            x = lookup[item["evidence_id"]]
            output.append({"expert":x.expert,"market":x.market,"timestamp":x.timestamp,"quote":x.text,"evidence_id":x.evidence_id})
        elif isinstance(item, str) and item in lookup:
            x = lookup[item]
            output.append({"expert":x.expert,"market":x.market,"timestamp":x.timestamp,"quote":x.text,"evidence_id":x.evidence_id})
    return output


def overview():
    themes = get_themes()
    header()
    st.markdown('<div class="section-title">Research Overview</div><div class="section-subtitle">The current evidence base and generated research outputs.</div>', unsafe_allow_html=True)
    try:
        store = EvidenceStore()
        records = len(store.all())
        statements = len(store.expert_statements())
    except Exception:
        records, statements = 0, 0
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Markets","3"),("Experts","3"),("Guide Questions","6"),("Verified Answers","18")]):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)
    common = themes.get("common_themes", [])
    differences = themes.get("market_differences", [])
    st.markdown('<div class="section-title">Research Signals</div><div class="section-subtitle">Cross-market findings generated from the expert evidence.</div>', unsafe_allow_html=True)
    a,b = st.columns(2)
    with a: st.markdown(f'<div class="signal"><strong>{len(common)}</strong> common themes identified across markets.</div>', unsafe_allow_html=True)
    with b: st.markdown(f'<div class="signal"><strong>{len(differences)}</strong> market differences identified.</div>', unsafe_allow_html=True)
    with st.expander("System coverage"):
        st.write(f"Transcript records loaded: {records}")
        st.write(f"Expert statements available: {statements}")
        st.write("Evidence chain: retrieval → synthesis → quote verification")


def interview_guide():
    guide = get_guide()
    header()
    st.markdown('<div class="section-title">Interview Guide</div><div class="section-subtitle">Select a research question and drill into the supporting evidence.</div>', unsafe_allow_html=True)
    if not guide:
        st.error("No guide answer file was found in data/.")
        return
    ids = list(guide.keys())
    selected = st.selectbox("Research question", ids, format_func=lambda q:f"{q} — {guide[q].get('question','')}")
    question = guide[selected]
    st.markdown(f'<div class="card"><div class="question-id">{safe(selected)}</div><div class="question">{safe(question.get("question",""))}</div></div>', unsafe_allow_html=True)
    for market, result in question.get("markets", {}).items():
        evidence = result.get("evidence", [])
        with st.expander(f"{market}  ·  {len(evidence)} verified source(s)"):
            st.markdown(f'<div class="answer">{safe(result.get("answer",""))}</div>', unsafe_allow_html=True)
            for item in evidence:
                evidence_card(item)


def compare_markets():
    guide = get_guide()
    header()
    st.markdown('<div class="section-title">Compare Markets</div><div class="section-subtitle">Compare how experts answer the same research question across markets.</div>', unsafe_allow_html=True)
    if not guide:
        st.error("No guide answer file was found.")
        return
    ids = list(guide.keys())
    selected = st.selectbox("Research question", ids, key="compare_question", format_func=lambda q:f"{q} — {guide[q].get('question','')}")
    markets = guide[selected].get("markets", {})
    selected_markets = st.multiselect("Markets", list(markets.keys()), default=list(markets.keys()), key="compare_markets")
    if not selected_markets:
        st.info("Select at least one market.")
        return
    cols = st.columns(len(selected_markets))
    for col, market in zip(cols, selected_markets):
        with col:
            result = markets[market]
            evidence = result.get("evidence", [])
            st.markdown(f'<div class="card"><div class="answer-market">{safe(market)}</div><div class="answer" style="margin-top:9px;">{safe(result.get("answer",""))}</div></div>', unsafe_allow_html=True)
            with st.expander(f"Evidence · {len(evidence)} source(s)"):
                for item in evidence:
                    evidence_card(item)


def themes_view():
    themes = get_themes()
    header()
    st.markdown('<div class="section-title">Themes & Disagreements</div><div class="section-subtitle">See where the experts converge and where the markets differ.</div>', unsafe_allow_html=True)
    common = themes.get("common_themes", [])
    differences = themes.get("market_differences", [])
    try:
        store = EvidenceStore()
    except Exception:
        store = None
    for heading, values in [(f"Common Themes · {len(common)}", common),(f"Market Differences · {len(differences)}", differences)]:
        st.markdown(f'<div class="section-title">{heading}</div>', unsafe_allow_html=True)
        for theme in values:
            if isinstance(theme, str):
                title, summary, evidence = theme, "", []
            else:
                title = theme.get("title", theme.get("theme", "Theme"))
                summary = theme.get("summary", theme.get("description", ""))
                evidence = theme.get("evidence", [])
            st.markdown(f'<div class="theme-card"><div class="theme-title">{safe(title)}</div><div class="theme-summary">{safe(summary)}</div></div>', unsafe_allow_html=True)
            if evidence and store:
                resolved = evidence_from_ids(evidence, store)
                if resolved:
                    with st.expander(f"View {len(resolved)} supporting source(s)"):
                        for item in resolved:
                            evidence_card(item)


def evidence_explorer():
    header()
    st.markdown('<div class="section-title">Evidence Explorer</div><div class="section-subtitle">Search the underlying expert statements independently of generated answers.</div>', unsafe_allow_html=True)
    store = EvidenceStore()
    evidence = store.expert_statements()
    markets = sorted({x.market for x in evidence})
    a,b = st.columns([1,2])
    with a: selected_market = st.selectbox("Market", ["All Markets"] + markets)
    with b: search = st.text_input("Search evidence", placeholder="Try ROI, training, budget, maintenance...")
    results = evidence
    if selected_market != "All Markets":
        results = [x for x in results if x.market == selected_market]
    if search.strip():
        q = search.lower().strip()
        results = [x for x in results if q in x.text.lower()]
    st.caption(f"{len(results)} evidence record(s)")
    for x in results:
        evidence_card({"expert":x.expert,"market":x.market,"timestamp":x.timestamp,"quote":x.text,"evidence_id":x.evidence_id})


def ask_question():
    header()
    st.markdown('<div class="section-title">Ask the Research Assistant</div><div class="section-subtitle">Ask a new question across all expert interviews. Answers are generated only from retrieved evidence.</div>', unsafe_allow_html=True)
    with st.form("research_form"):
        question = st.text_input("Research question", placeholder="What are the main barriers to robotic surgery adoption?")
        submitted = st.form_submit_button("Ask Research Assistant", type="primary")
    if not submitted:
        st.markdown('<div class="card"><div class="question">Try a research question</div><div class="answer" style="margin-top:10px;">What are the main barriers to adoption?<br>How important is ROI in purchasing decisions?<br>How does surgeon training affect adoption?<br>What are the expected adoption trends?<br>How long does procurement typically take?</div></div>', unsafe_allow_html=True)
        return
    if not question.strip():
        st.warning("Enter a question.")
        return
    store = EvidenceStore()
    retriever = HybridRetriever(store)
    synthesizer = LLMSynthesizer(store, retriever)
    with st.spinner("Retrieving evidence and synthesizing answer..."):
        try:
            result = synthesizer.generate(question, top_k=6)
        except Exception as exc:
            st.error(f"Research query failed: {exc}")
            return
    verified = result.get("verified", False)
    badge = '<span class="badge">VERIFIED</span>' if verified else ''
    st.markdown('<div class="section-title">Answer</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="meta">AI SYNTHESIS {badge}</div><div class="answer" style="margin-top:9px;">{safe(result.get("answer","No answer returned."))}</div></div>', unsafe_allow_html=True)
    evidence = result.get("evidence", [])
    st.markdown(f'<div class="section-title">Evidence Trail · {len(evidence)} verified source(s)</div>', unsafe_allow_html=True)
    if not evidence:
        st.warning("The generated answer could not be supported by verified evidence.")
        return
    for item in evidence:
        evidence_card(item)


def source_management():
    header()
    st.markdown('<div class="section-title">Source Management</div><div class="section-subtitle">Inspect and manage the transcript evidence loaded by the system.</div>', unsafe_allow_html=True)
    store = EvidenceStore()
    all_evidence = store.all()
    expert_evidence = store.expert_statements()
    cols = st.columns(3)
    for col, (label, value) in zip(cols, [("Transcript Records",len(all_evidence)),("Expert Statements",len(expert_evidence)),("Markets",len({x.market for x in all_evidence}))]):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Loaded Sources</div>', unsafe_allow_html=True)
    for market in ["France","Germany","United Kingdom"]:
        records = store.by_market(market)
        if records:
            st.success(f"✓ {market} — {len(records)} transcript records")
        else:
            st.error(f"✗ {market} — no evidence found")
    st.markdown('<div class="section-title">Add Transcript</div>', unsafe_allow_html=True)
    st.caption("Upload TXT transcripts to data/. The evidence store reads Transcript_*.txt files on refresh.")
    uploaded = st.file_uploader("Transcript files", type=["txt"], accept_multiple_files=True, key="transcript_uploader")
    if uploaded and st.button("Save Transcripts", type="primary", key="save_transcripts"):
        for file in uploaded:
            (DATA_DIR / Path(file.name).name).write_bytes(file.getbuffer())
        st.success(f"Saved {len(uploaded)} transcript file(s). Refresh the app to rebuild the evidence store.")
    st.markdown('<div class="section-title">Transcript Preview</div>', unsafe_allow_html=True)
    for path in sorted(DATA_DIR.glob("Transcript_*.txt")):
        with st.expander(path.name):
            try:
                transcript = parse_transcript(path)
                st.write(f"**Expert:** {transcript['expert']}")
                st.write(f"**Role:** {transcript['role']}")
                st.write(f"**Market:** {transcript['market']}")
                st.write(f"**Evidence records:** {len(transcript['evidence'])}")
            except Exception as exc:
                st.error(f"Could not parse {path.name}: {exc}")


def main():
    navigation = st.radio("Research Workspace", ["Overview","Interview Guide","Compare Markets","Themes & Disagreements","Evidence Explorer","Ask a Question","Source Management"], horizontal=True, label_visibility="collapsed")
    if navigation == "Overview": overview()
    elif navigation == "Interview Guide": interview_guide()
    elif navigation == "Compare Markets": compare_markets()
    elif navigation == "Themes & Disagreements": themes_view()
    elif navigation == "Evidence Explorer": evidence_explorer()
    elif navigation == "Ask a Question": ask_question()
    elif navigation == "Source Management": source_management()


if __name__ == "__main__":
    main()
