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

        # Ensure expected columns exist
        for col in ["experience_level","firms_applying","availability","timezone","linkedin_url","bio"]:
            if col not in df.columns:
                df[col] = None

        # --- Filters row (3 columns) ---
        c1, c2, c3 = st.columns(3)
        languages = ["All"] + sorted(df["language"].dropna().unique().tolist())
        lang = c1.selectbox("Language", languages)

        levels = ["All","Beginner","Intermediate","Advanced"]
        lvl = c2.selectbox("Experience", levels)

        firms_universe = sorted({f for arr in (df["firms_applying"].dropna() if "firms_applying" in df else []) for f in (arr or [])})
        firms_filter = c3.multiselect("Firms (must include all selected)", firms_universe)

        # --- Apply filters ---
        if lang != "All":
            df = df[df["language"] == lang]
        if lvl != "All":
            df = df[df["experience_level"] == lvl]
        if firms_filter:
            def has_all_firms(arr):
                s = set(arr or [])
                return set(firms_filter).issubset(s)
            df = df[df["firms_applying"].apply(has_all_firms)]

        # --- Results ---
        if df.empty:
            st.info("No users match your filters.")
        else:
            st.write(f"Showing **{len(df)}** matching users:")
            # Profile cards
            for _, row in df.sort_values("created_at", ascending=False).iterrows():
                st.markdown("---")
                cA, cB = st.columns([3,1])
                with cA:
                    name = row.get("name") or row.get("email","").split("@")[0]
                    st.markdown(f"### {name}")
                    st.caption(row.get("bio") or "No bio yet.")
                    meta = [
                        f"🗣️ {row.get('language') or '—'}",
                        f"🎯 {row.get('experience_level') or '—'}",
                        f"🕒 {row.get('timezone') or '—'}",
                    ]
                    st.markdown(" · ".join(meta))
                    firms = ", ".join(row.get("firms_applying", []) or [])
                    st.markdown(f"**Firms:** {firms or '—'}")
                    st.markdown(f"**Availability:** {row.get('availability') or '—'}")
                    # Contact links
                    email = row.get("email")
                    if email:
                        st.markdown(f"📧 [Email {name}](mailto:{email}?subject=Case%20practice%20partner)")
                with cB:
                    if row.get("linkedin_url"):
                        st.link_button("LinkedIn", row["linkedin_url"])


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

        recs = recommend_partners(user.id, mode=rec_mode_key)

        if not recs:
            st.warning("No recommendations available yet. Try after receiving feedback!")
            return

        st.write(f"### 👥 Top {len(recs)} Suggested Partners — *{rec_mode}*")

        for i, u in enumerate(recs[:5], 1):
            title_name = u.get("name") or u.get("email","").split("@")[0]
            with st.expander(f"{i}. {title_name} ({u.get('language') or 'N/A'})"):
                st.markdown(f"**Experience level:** {u.get('experience_level') or '—'}")
                st.markdown(f"**Accepted feedbacks (experience):** {u.get('case_count', 0)}")
                st.markdown(f"**Timezone:** {u.get('timezone') or '—'}")
                firms = ", ".join(u.get("firms_applying", []) or [])
                st.markdown(f"**Firms:** {firms or '—'}")
                st.markdown(f"**Availability:** {u.get('availability') or '—'}")
                bio = u.get("bio")
                if bio:
                    st.info(bio)
                # Contact + score
                email = u.get("email")
                if email:
                    st.markdown(f"📧 [Email {title_name}](mailto:{email}?subject=Case%20practice%20partner)")
                if u.get("linkedin_url"):
                    st.link_button("LinkedIn", u["linkedin_url"])
                st.caption(f"🏆 Match score: {round(u.get('score', 0), 3)}")

