# app/tabs/tab3_partner_recommendations.py

import streamlit as st
import pandas as pd
from app.core.recommendations_partners import recommend_partners, get_all_users

def render(user):
    st.header("👥 Partner Recommendation System")

    mode = st.radio(
        "Choose Mode:",
        ["🧭 Explore Users", "🤖 Personalized Recommendations"],
        horizontal=True,
    )

    # ---------------------------------------------------------------------
    # 1️⃣ EXPLORE USERS
    # ---------------------------------------------------------------------
    if mode == "🧭 Explore Users":
        st.subheader("🔍 Explore Users by Language")

        users = get_all_users(exclude_user_id=user.id)
        if not users:
            st.info("No other users found.")
            return

        df = pd.DataFrame(users)
        languages = ["All"] + sorted(df["language"].dropna().unique().tolist())
        lang = st.selectbox("Language", languages)

        if lang != "All":
            df = df[df["language"] == lang]

        if df.empty:
            st.info("No users match your filters.")
        else:
            st.write(f"Showing **{len(df)}** matching users:")
            st.dataframe(
                df[["name", "email", "language", "created_at"]],
                use_container_width=True
            )

    # ---------------------------------------------------------------------
    # 2️⃣ PERSONALIZED RECOMMENDATIONS
    # ---------------------------------------------------------------------
    else:
        st.subheader("🎯 Personalized Partner Suggestions")

        rec_mode = st.radio(
            "Select Recommendation Type:",
            ["Similar to Yourself", "Good at Your Weaknesses"],
            horizontal=True,
        )
        rec_mode_key = "similar" if rec_mode == "Similar to Yourself" else "complement"

        st.write("⏳ Computing recommendations...")
        recs = recommend_partners(user.id, mode=rec_mode_key)

        if not recs:
            st.warning("No recommendations available yet. Try after receiving feedback!")
            return

        st.write(f"### 👥 Top {len(recs)} Suggested Partners — *{rec_mode}*")

        for i, u in enumerate(recs[:5], 1):
            with st.expander(f"{i}. {u['name']} ({u['language'] or 'N/A'})"):
                st.markdown(f"📧 **Email:** {u.get('email', '-')}")
                st.markdown(f"🗣️ **Language:** {u.get('language', '-')}")
                st.markdown(f"📊 **Experience:** {u['case_count']} accepted feedbacks")
                st.markdown(f"🏆 **Score:** {round(u['score'], 3)}")
