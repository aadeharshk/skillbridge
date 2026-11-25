# 🎯 SkillBridge: Resume-to-Job Matching with Skill Gap Analysis

Upload a resume, paste one or more job descriptions, and get a **match score**, the **required skills you're missing**, and, for every JD requirement, **the resume line that best backs it up**. Rank several jobs at once to decide where to apply first.

**Live demo:** [aadeharshk-skillbridge-app-smvgqm.streamlit.app](https://aadeharshk-skillbridge-app-smvgqm.streamlit.app) · **Stack:** Python, NLP (rule-based skill extraction), sentence embeddings (all-MiniLM-L6-v2 via ONNX), NumPy, Streamlit

## Results

- **Skill extraction:** precision **1.00**, recall **0.97** (F1 0.98) on 25 hand-labelled resume/JD lines with 58 skills. Reproduce with `python -m eval.evaluate_extraction`. Remaining misses are word forms like "fine-tuned" vs "fine-tuning".
- **Taxonomy:** 89 skills across 10 categories (data engineering, ML, GenAI, automation, BI, cloud…), each with aliases and word-boundary rules, so *Java* never matches *JavaScript*, and *R* doesn't match *R&D*.
- **Sanity check:** on the fictional sample resume (a data analyst), the app ranks the Data Analyst JD first (81/100), ahead of Data Engineer (58) and AI Automation Engineer (53).

## How the score works

```
Resume ─► text ─► skills (taxonomy + implied skills) ──┐
                 └► lines ─► embeddings ──┐            ├─► 60% skill coverage (required ×2)
JD ─► requirements (required / nice-to-have) ─► embeddings ─► cosine similarity ─► 40% requirement coverage
```

1. **Parse the JD into requirements** and mark each as *required* or *nice to have* (based on "Nice to have", "Preferred" and similar headers or phrases).
2. **Skill coverage (60%):** extract skills from both sides. Required skills count double. Tools imply broader skills (n8n → Workflow Automation, LangChain → LLMs). For "PostgreSQL **or** MySQL" requirements, either one counts.
3. **Requirement coverage (40%):** embed every requirement and every resume line, and find the closest resume line for each requirement. Credit ramps from 0 at cosine 0.30 to full at 0.50. This catches matches that keyword matching misses (e.g. "present insights to stakeholders" ↔ "presented findings to warehouse managers").
4. **Output:** ranking table, gap chart by category, requirement-by-evidence table, JSON report download.

Why combine both: keyword matching alone misses paraphrases, and embeddings alone can't tell *Spark* from *Pandas*. Using both makes the score harder to game and easier to explain.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
pytest -q                             # 4 tests
python -m eval.evaluate_extraction    # skill extraction precision/recall
```

The embedding model (~80 MB) downloads automatically on first run. No API key is needed.

## Ideas for next versions
- LLM-written resume bullet suggestions for each ❌ requirement
- Learn score weights from real recruiter shortlist decisions
- Integrate with [UpNxtWork](https://upnxtwork.in) to recommend internships to students

---
Built by **Harsh Aade** · [LinkedIn](https://linkedin.com/in/harsh-aade) · [GitHub](https://github.com/aadeharshk)
