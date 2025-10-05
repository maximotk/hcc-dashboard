import streamlit as st
import pandas as pd
from app.core.db import supabase
from app.core.charts import radar_chart, performance_line_chart
from app.core.analytics_utils import (
    get_user_feedback,
    feedback_to_dataframe,
    compute_skill_averages
)

def render(user):
    st.header("📊 Your Performance")

    # --- Fetch data ---
    feedback_data = get_user_feedback(user.id)
    if not feedback_data:
        st.info("No accepted feedback yet — complete some cases to see analytics!")
        return

    # --- Prepare data ---
    df = feedback_to_dataframe(feedback_data)

    case_map = {c["id"]: c["title"] for c in supabase.table("cases").select("id, title").execute().data}
    df["Case"] = df["case_id"].map(case_map)
    df.drop(columns=["case_id"], inplace=True)
    cols = ["Date", "Case"] + [c for c in df.columns if c not in ["Date", "Case"]]
    df = df[cols]

    # --- Compute averages ---
    skill_avgs, skill_cols = compute_skill_averages(df) 

    st.write("### 📈 Summary Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Cases Completed", len(df))
    col2.metric("Avg Rating", round(df[skill_cols].values.mean(), 2))
    col3.metric("Skills Rated", len(skill_avgs))

    # --- Charts ---
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(radar_chart(skill_avgs), use_container_width=True)

    with col2:
        mode = st.radio(
            "View Progress Over:",
            ["Time (by Date)", "Number of Cases Practiced"],
            horizontal=True,
        )
        st.plotly_chart(
            performance_line_chart(df, skill_cols, mode),
            use_container_width=True
        )

    # --- Table ---
    with st.expander("📋 View Detailed Feedback Data"):
        st.dataframe(df, use_container_width=True)
