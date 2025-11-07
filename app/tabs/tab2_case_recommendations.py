import streamlit as st
import pandas as pd
from app.core.analytics_utils import get_user_skill_avgs
from app.core.recommendations_cases import (
    recommend_cases,
    get_all_cases
)

def render(user):
    st.header("🧠 Case Recommendation System")

    # --- Mode switch ---
    mode = st.radio(
        "Choose Mode:",
        ["🧭 Explore Cases", "🤖 Personalized Recommendations"],
        horizontal=True,
    )

    # -------------------------------------------------------------------------
    # 1️⃣  EXPLORE MODE
    # -------------------------------------------------------------------------
    if mode == "🧭 Explore Cases":
        st.subheader("🔍 Explore Cases by Filters")

        cases = get_all_cases()
        if not cases:
            st.warning("No cases found in the database.")
            return

        df = pd.DataFrame(cases)

        # --- Filters ---
        c1, c2, c3, c4 = st.columns(4)

        difficulties = ["All"] + sorted(df["difficulty"].dropna().unique().tolist())
        industries = ["All"] + sorted(df["industry"].dropna().unique().tolist())
        focuses = ["All"] + sorted(df["focus_area"].dropna().unique().tolist())
        styles = ["All"] + sorted(df["case_style"].dropna().unique().tolist()) if "case_style" in df else ["All"]

        difficulty = c1.selectbox("Difficulty", difficulties)
        industry = c2.selectbox("Industry", industries)
        focus = c3.selectbox("Focus Area", focuses)
        style = c4.selectbox("Case Style", styles)

        # --- Apply filters ---
        if difficulty != "All":
            df = df[df["difficulty"] == difficulty]
        if industry != "All":
            df = df[df["industry"] == industry]
        if focus != "All":
            df = df[df["focus_area"] == focus]
        if style != "All":
            df = df[df["case_style"] == style]


        if df.empty:
            st.info("No cases match your filters.")
        else:
            st.write(f"Showing **{len(df)}** matching cases:")
            st.dataframe(
                df[["title", "difficulty", "industry", "focus_area", "description"]],
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # 2️⃣  PERSONALIZED RECOMMENDATIONS
    # -------------------------------------------------------------------------
    else:
        st.subheader("🎯 Personalized Recommendations")

        user_avgs = get_user_skill_avgs(user.id)
        if not user_avgs:
            st.info("You need at least one accepted feedback to receive personalized recommendations.")
            return

        # --- Show user current profile ---
        st.write("### 🧩 Your Skill Profile (Average Ratings)")
        profile_df = pd.DataFrame.from_dict(user_avgs, orient="index", columns=["Average Rating"]).sort_index()
        st.table(profile_df.style.format({"Average Rating": "{:.2f}"}))

        # --- Recommendation type ---
        rec_mode = st.radio(
            "Select Recommendation Type:",
            ["Fix Weaknesses", "Build on Strengths"],
            horizontal=True,
        )
        rec_mode_key = "fix_weaknesses" if rec_mode == "Fix Weaknesses" else "build_strengths"

        pref_style = st.radio(
            "Preferred Case Style",
            ["Any", "Candidate-led", "Interviewer-led"],
            horizontal=True,
        )

        # --- Get recommendations ---
        recs = recommend_cases(user_avgs, mode=rec_mode_key, top_n=5, pref_style=None if pref_style == "Any" else pref_style)


        if not recs:
            st.warning("No recommendations available.")
            return

        st.write(f"### 🏆 Top {len(recs)} Recommended Cases — *{rec_mode}*")

        for i, case in enumerate(recs, 1):
            with st.expander(f"{i}. {case['title']} — ({case['difficulty']})"):
                st.markdown(f"**Industry:** {case.get('industry', '—')}")
                st.markdown(f"**Focus Area:** {case.get('focus_area', '—')}")
                st.markdown(f"**Description:** {case.get('description', '')}")

                # Visualize how relevant each skill is to this case
                skills = case.get("skill_weights", {})
                if skills:
                    skill_df = pd.DataFrame(skills.items(), columns=["Skill", "Weight"]).sort_values("Weight", ascending=False)
                    st.bar_chart(skill_df.set_index("Skill"))
                else:
                    st.caption("No skill breakdown available for this case.")
