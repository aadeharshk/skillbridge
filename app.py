"""SkillBridge: resume-to-job matching with skill gap analysis (Streamlit app)."""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from matcher.core import MET_THRESHOLD, match, read_document
from matcher.skills import category

ROOT = Path(__file__).parent
SAMPLES = ROOT / "samples"
st.set_page_config(page_title="SkillBridge", page_icon="🎯", layout="wide")


@st.cache_data(show_spinner="Matching…")
def run_match(resume: str, jd: str):
    return match(resume, jd)


def verdict(score: float) -> str:
    if score >= 75:
        return "🟢 Strong match: apply now"
    if score >= 55:
        return "🟠 Partial match: tailor your resume first"
    return "🔴 Weak match: close the skill gaps first"


st.title("🎯 SkillBridge")
st.caption("Upload a resume and paste a job description to get a match score, the skills you're missing and the resume lines that back each requirement. Rank several jobs at once to decide where to apply first.")

# ---------------- Inputs ----------------
left, right = st.columns(2)
with left:
    st.subheader("1. Resume")
    up = st.file_uploader("PDF, DOCX or TXT", type=["pdf", "docx", "txt"])
    if up:
        resume = read_document(up.name, up.getvalue())
    else:
        resume = (SAMPLES / "sample_resume.txt").read_text()
        st.info("Using a fictional sample resume. Upload yours to try it.")
    with st.expander("Resume text"):
        st.text(resume[:4000])
with right:
    st.subheader("2. Job description(s)")
    sample_jds = {p.stem.replace("jd_", "").replace("_", " ").title(): p.read_text() for p in sorted(SAMPLES.glob("jd_*.txt"))}
    pasted = st.text_area("Paste one job description, or several separated by a line with ---", height=220,
                          placeholder="Paste a JD here…")
    if pasted.strip():
        parts = [p.strip() for p in pasted.split("\n---") if p.strip()]
        jds = {(p.splitlines()[0][:60] or f"JD {i + 1}"): p for i, p in enumerate(parts)}
    else:
        jds = sample_jds
        st.info(f"Using {len(jds)} fictional sample JDs: " + ", ".join(jds))

if not resume.strip():
    st.error("Couldn't read any text from the resume. If it's a scanned PDF, upload a text-based PDF or DOCX.")
    st.stop()

reports = {name: run_match(resume, jd) for name, jd in jds.items()}

# ---------------- Ranking ----------------
st.subheader("3. Ranking")
rank = pd.DataFrame([{
    "Job": n, "Match score": r.score, "Skill coverage": r.skill_score, "Requirement coverage (semantic)": r.semantic_score,
    "Missing required skills": ", ".join(r.missing_required) or "None", "Verdict": verdict(r.score)}
    for n, r in reports.items()]).sort_values("Match score", ascending=False)
st.dataframe(rank, width="stretch", hide_index=True,
             column_config={"Match score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f")})

# ---------------- Detail ----------------
st.subheader("4. Detailed report")
job = st.selectbox("Job", list(rank["Job"]))
r = reports[job]
c1, c2, c3 = st.columns(3)
c1.metric("Match score", f"{r.score:.0f}/100")
c2.metric("Skill coverage", f"{r.skill_score:.0f}%", help="Required skills count double compared with nice-to-have skills.")
c3.metric("Requirements backed by resume lines", f"{sum(q.met for q in r.requirements)}/{len(r.requirements)}")
st.markdown(f"**{verdict(r.score)}**")

a, b, c = st.columns(3)
with a:
    st.markdown("**✅ Skills you have**")
    st.write(", ".join(r.matched_skills) or "None")
with b:
    st.markdown("**❌ Missing (required)**")
    st.write(", ".join(r.missing_required) or "None 🎉")
with c:
    st.markdown("**➕ Missing (nice to have)**")
    st.write(", ".join(r.missing_optional) or "None")

if r.missing_required or r.missing_optional:
    gaps = pd.DataFrame([{"skill": s, "category": category(s), "priority": "Required"} for s in r.missing_required] +
                        [{"skill": s, "category": category(s), "priority": "Nice to have"} for s in r.missing_optional])
    st.altair_chart(alt.Chart(gaps).mark_bar().encode(
        x=alt.X("count():Q", title="Missing skills"), y=alt.Y("category:N", title=None),
        color=alt.Color("priority:N", scale=alt.Scale(domain=["Required", "Nice to have"], range=["#d1495b", "#edae49"]),
                        legend=alt.Legend(orient="bottom", title=None))).properties(height=180), width="stretch")

st.markdown("**Requirement by requirement:** the closest line in your resume for each JD requirement (semantic similarity).")
req_df = pd.DataFrame([{
    "Requirement": q.text, "Type": "Nice to have" if q.optional else "Required",
    "Best evidence in resume": q.best_evidence, "Similarity": round(q.similarity, 2),
    "Covered": "✅" if q.met else ("〰️" if q.similarity >= 0.3 else "❌")} for q in r.requirements])
st.dataframe(req_df, width="stretch", hide_index=True)
st.caption(f"✅ similarity ≥ {MET_THRESHOLD} · 〰️ partly related · ❌ nothing related in the resume. "
           "Tip: for ❌ requirements you genuinely meet, add a resume bullet that says so in the JD's words.")

st.download_button("⬇️ Download report (JSON)", json.dumps({
    "job": job, "score": r.score, "skill_coverage": r.skill_score, "semantic_coverage": r.semantic_score,
    "matched": r.matched_skills, "missing_required": r.missing_required, "missing_optional": r.missing_optional,
    "requirements": req_df.to_dict("records")}, indent=2), "skillbridge_report.json", "application/json")

with st.expander("ℹ️ How the score works"):
    st.markdown("""
- **Skill coverage (60%)**: skills are extracted with a 89-skill taxonomy (aliases and word-boundary rules, so *Java* ≠ *JavaScript*). Required skills count double. Tools imply broader skills (n8n → Workflow Automation). For "X **or** Y" requirements, either one counts.
- **Requirement coverage (40%)**: every JD requirement is embedded with all-MiniLM-L6-v2 and compared with every resume line. Credit ramps from 0 at similarity 0.30 to full at 0.50.
- **Skill extractor accuracy** on 25 hand-labelled lines (58 skills): precision **1.00**, recall **0.97**. Reproduce with `python -m eval.evaluate_extraction`.
""")

st.divider()
st.caption("Built by Harsh Aade · Python, NLP, sentence embeddings (all-MiniLM-L6-v2, ONNX), Streamlit")
