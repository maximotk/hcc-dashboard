# app/core/recommendations_partners.py

from app.core.db import supabase
from app.core.analytics_utils import get_user_skill_avgs
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data(ttl=600)
def get_all_users(exclude_user_id=None):
    res = supabase.table("users").select(
        "id, name, email, language, experience_level, firms_applying, bio, availability, timezone, linkedin_url, created_at"
    ).execute()
    users = res.data or []
    if exclude_user_id:
        users = [u for u in users if u["id"] != exclude_user_id]
    return users



def get_user_case_count(user_id):
    """Count how many accepted feedbacks this user has received."""
    res = (
        supabase.table("feedback")
        .select("id", count="exact")
        .eq("to_user", user_id)
        .eq("status", "accepted")
        .execute()
    )
    return res.count or 0


def compute_similarity(user_a_skills, user_b_skills):
    """Compute similarity between two users' skill vectors."""
    skills = list(set(user_a_skills.keys()) | set(user_b_skills.keys()))
    a = np.array([user_a_skills.get(s, 3) for s in skills])
    b = np.array([user_b_skills.get(s, 3) for s in skills])

    # cosine similarity (1 = identical)
    num = np.dot(a, b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(num / denom) if denom else 0.0


def compute_complementarity(user_a_skills, user_b_skills):
    """Compute how much user B complements user A's weaknesses."""
    skills = list(set(user_a_skills.keys()) | set(user_b_skills.keys()))
    complement = 0
    for s in skills:
        a = user_a_skills.get(s, 3)
        b = user_b_skills.get(s, 3)
        complement += (5 - a) * b  # high if A is weak and B is strong
    return complement / len(skills)

@st.cache_data(ttl=600)
def recommend_partners(current_user_id, mode="similar"):
    """Return a ranked list of recommended partners."""
    current_avgs = get_user_skill_avgs(current_user_id)
    if not current_avgs:
        return []

    users = get_all_users(exclude_user_id=current_user_id)
    recs = []

    for u in users:
        u_avgs = get_user_skill_avgs(u["id"])
        if not u_avgs:
            continue

        case_count = get_user_case_count(u["id"])

        if mode == "similar":
            score = compute_similarity(current_avgs, u_avgs) + 0.05 * case_count
        else:  # complement mode
            score = compute_complementarity(current_avgs, u_avgs)

        u["score"] = score
        u["case_count"] = case_count
        recs.append(u)

    return sorted(recs, key=lambda x: x["score"], reverse=True)
