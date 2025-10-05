
from app.core.db import supabase
import pandas as pd
import streamlit as st

@st.cache_data(ttl=600)
def get_user_feedback(user_id: str, status: str = "accepted"):
    """Fetch feedback entries for a user."""
    res = (
        supabase.table("feedback")
        .select("skill_scores, created_at, case_id")
        .eq("to_user", user_id)
        .eq("status", status)
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


def feedback_to_dataframe(feedback_data: list):
    """Convert feedback JSON objects into a clean dataframe."""
    if not feedback_data:
        return pd.DataFrame()

    df = pd.json_normalize(feedback_data)
    df.columns = [c.replace("skill_scores.", "") for c in df.columns]
    df.rename(columns={"created_at": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df


def compute_skill_averages(feedback_df: pd.DataFrame):
    """Compute per-skill averages from a feedback dataframe."""
    if feedback_df.empty:
        return {}

    # Detect skill columns dynamically
    skill_cols = [c for c in feedback_df.columns if c not in ["Date", "case_id", "Case"]]
    skill_avgs = feedback_df[skill_cols].mean().to_dict()

    # Fill missing skills with neutral 3.0 to avoid NaNs
    all_skills = ["Estimation", "Framework", "Brainstorming", "Chart Interpretation", "Numerical Calculations"]
    for s in all_skills:
        skill_avgs.setdefault(s, 3.0)

    return skill_avgs, skill_cols

@st.cache_data(ttl=600)
def get_user_skill_avgs(user_id: str):
    """Compute user's average rating per skill from accepted feedback."""
    feedback_data = get_user_feedback(user_id)
    feedback_df = feedback_to_dataframe(feedback_data)
    skill_avgs, _ = compute_skill_averages(feedback_df)
    return skill_avgs

