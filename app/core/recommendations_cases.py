from app.core.db import supabase
import pandas as pd
from app.core.analytics_utils import get_user_feedback, feedback_to_dataframe, compute_skill_averages

@st.cache_data(ttl=600)
def get_all_cases():
    """Fetch all available cases from Supabase."""
    res = supabase.table("cases").select("*").execute()
    return res.data or []


def compute_case_score(user_avgs: dict, case: dict, mode: str):
    """Compute a weighted score for a given case based on user skill averages."""
    skill_weights = case.get("skill_weights", {}) or {}

    if not skill_weights:
        return 0

    score = 0
    for skill, weight in skill_weights.items():
        user_rating = user_avgs.get(skill, 3)

        if mode == "fix_weaknesses":
            # Prefer cases that target low-rated skills
            score += weight * (5 - user_rating)
        else:  # build_strengths
            # Prefer cases that use strong skills
            score += weight * user_rating

    return score

@st.cache_data(ttl=600)
def recommend_cases(user_avgs: dict, mode: str = "fix_weaknesses", top_n: int = 5):
    """Recommend top N cases for the user given their strengths or weaknesses."""
    cases = get_all_cases()
    if not cases:
        return []

    for c in cases:
        c["score"] = compute_case_score(user_avgs, c, mode)

    sorted_cases = sorted(cases, key=lambda x: x["score"], reverse=True)
    return sorted_cases[:top_n]
