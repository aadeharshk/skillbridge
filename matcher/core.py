"""Resume-to-job matching: parse, extract skills, semantic requirement matching, score."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

import numpy as np

from matcher.skills import category, extract_skills

_embedder = None


def embed(texts: list[str]) -> np.ndarray:
    """all-MiniLM-L6-v2 sentence embeddings via ONNX (no PyTorch needed), L2-normalised."""
    global _embedder
    if _embedder is None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        _embedder = DefaultEmbeddingFunction()
    vecs = np.array(_embedder(texts), dtype=np.float32)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True).clip(min=1e-9)


# ---------- Parsing ----------

def read_document(name: str, data: bytes) -> str:
    ext = name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    if ext == "docx":
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")


_ANY_OF = re.compile(r"\bor\b|at least one|any of|either", re.I)
_BULLET = re.compile(r"^\s*(?:[-•*●▪◦]|\d+[.)])\s*")
_OPTIONAL_HINT = re.compile(r"nice to have|good to have|preferred|bonus|is a plus|a plus|desirable|optional", re.I)
_OPTIONAL_HEADER = re.compile(r"^\s*(nice|good) to have|^\s*preferred|^\s*bonus", re.I)
_REQUIRED_HEADER = re.compile(r"^\s*(requirements|required|must have|qualifications|what you.ll need|responsibilities|what you.ll do|skills)", re.I)


def split_lines(text: str, min_len: int = 25) -> list[str]:
    """Split a document into meaningful lines/sentences (bullets, sentences)."""
    out = []
    for raw in text.splitlines():
        line = _BULLET.sub("", raw).strip()
        if not line:
            continue
        parts = re.split(r"(?<=[.;])\s+(?=[A-Z])", line) if len(line) > 220 else [line]
        out.extend(p.strip() for p in parts if len(p.strip()) >= min_len)
    return out


@dataclass
class Requirement:
    text: str
    optional: bool
    best_evidence: str = ""
    similarity: float = 0.0

    @property
    def met(self) -> bool:
        return self.similarity >= MET_THRESHOLD


MET_THRESHOLD = 0.5   # cosine similarity at which a resume line counts as evidence
FLOOR = 0.3           # below this, the closest resume line is unrelated


def credit(sim: float) -> float:
    """Linear ramp: 0 credit at FLOOR, full credit at MET_THRESHOLD and above."""
    return float(np.clip((sim - FLOOR) / (MET_THRESHOLD - FLOOR), 0.0, 1.0))


def parse_requirements(jd: str) -> list[Requirement]:
    reqs, optional_block = [], False
    lines = [l for l in jd.splitlines() if l.strip()]
    if lines and len(lines[0]) < 80 and not _BULLET.match(lines[0]):
        lines = lines[1:]  # first short line is the job title, not a requirement
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if _OPTIONAL_HEADER.search(stripped) and len(stripped) < 60:
            optional_block = True
            continue
        if _REQUIRED_HEADER.search(stripped) and len(stripped) < 60:
            optional_block = False
            continue
        for line in split_lines(stripped):
            reqs.append(Requirement(line, optional_block or bool(_OPTIONAL_HINT.search(line))))
    return reqs


# ---------- Matching ----------

@dataclass
class MatchReport:
    score: float
    skill_score: float
    semantic_score: float
    matched_skills: list[str]
    missing_required: list[str]
    missing_optional: list[str]
    extra_skills: list[str]
    requirements: list[Requirement]


def match(resume: str, jd: str) -> MatchReport:
    resume_skills = extract_skills(resume, expand=True)
    reqs = parse_requirements(jd)
    required_text = "\n".join(r.text for r in reqs if not r.optional) or jd
    optional_text = "\n".join(r.text for r in reqs if r.optional)
    jd_required = extract_skills(required_text)
    jd_optional = extract_skills(optional_text) - jd_required

    # "PostgreSQL or MySQL", "at least one of n8n, Zapier or Make.com": any one option satisfies the line.
    alternatives_covered = set()
    for r in reqs:
        if _ANY_OF.search(r.text):
            options = extract_skills(r.text)
            if options & resume_skills:
                alternatives_covered |= options - resume_skills
    jd_required -= alternatives_covered
    jd_optional -= alternatives_covered

    # Skill coverage: required skills count double.
    weight_total = 2 * len(jd_required) + len(jd_optional)
    weight_hit = 2 * len(jd_required & resume_skills) + len(jd_optional & resume_skills)
    skill_score = weight_hit / weight_total if weight_total else 0.0

    # Semantic coverage: for each JD requirement, find the closest resume line.
    resume_lines = split_lines(resume, min_len=15)
    if reqs and resume_lines:
        sims = embed([r.text for r in reqs]) @ embed(resume_lines).T
        best = sims.argmax(axis=1)
        for i, r in enumerate(reqs):
            r.similarity = float(sims[i, best[i]])
            r.best_evidence = resume_lines[best[i]]
        weights = np.array([1.0 if r.optional else 2.0 for r in reqs])
        met = np.array([credit(r.similarity) for r in reqs])
        semantic_score = float((weights * met).sum() / weights.sum())
    else:
        semantic_score = 0.0

    score = 0.6 * skill_score + 0.4 * semantic_score
    order = lambda s: (category(s), s)
    return MatchReport(
        score=round(100 * score, 1),
        skill_score=round(100 * skill_score, 1),
        semantic_score=round(100 * semantic_score, 1),
        matched_skills=sorted((jd_required | jd_optional) & resume_skills, key=order),
        missing_required=sorted(jd_required - resume_skills, key=order),
        missing_optional=sorted(jd_optional - resume_skills, key=order),
        extra_skills=sorted(resume_skills - jd_required - jd_optional, key=order),
        requirements=reqs,
    )
