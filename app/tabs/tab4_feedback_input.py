import streamlit as st
from app.core.db import (
    supabase,
    get_feedback_for_user,
    update_feedback_status,
    insert_feedback
)

def render(user):
    st.header("📝 Feedback Input & Validation")

    tab1, tab2 = st.tabs(["➕ Give Feedback", "✅ Review Received Feedback"])

    # --- TAB 1: GIVE FEEDBACK ---
    with tab1:
        st.subheader("Give Feedback")

        # Get available users & cases
        users_res = supabase.table("users").select("id, name, email").neq("id", user.id).execute()
        cases_res = supabase.table("cases").select("id, title").execute()

        if not users_res.data or not cases_res.data:
            st.warning("⚠️ No users or cases found in the database.")
            return

        # --- Prepare users and cases lists with placeholder ---
        users_options = [{"id": None, "name": "👉 Please choose a partner", "email": ""}] + users_res.data
        cases_options = [{"id": None, "title": "👉 Please choose a case"}] + cases_res.data

        # --- Select partner ---
        to_user = st.selectbox(
            "Select partner to give feedback to:",
            options=users_options,
            format_func=lambda u: f"{u['name']} ({u['email']})" if u["id"] else u["name"],
        )

        # --- Select case ---
        case = st.selectbox(
            "Select case practiced:",
            options=cases_options,
            format_func=lambda c: c["title"],
        )

        # --- Optional validation before proceeding ---
        if not to_user["id"] or not case["id"]:
            st.warning("⚠️ Please select both a partner and a case before submitting feedback.")
        else:
            # Skill ratings
            st.write("### Rate the skills (1–5)")
            skills = ["Estimation", "Framework", "Brainstorming", "Chart Interpretation", "Numerical Calculations"]
            skill_scores = {skill: st.slider(skill, 1, 5, 3) for skill in skills}

            comments = st.text_area("Comments (optional)")

            if st.button("Submit Feedback"):
                insert_feedback(
                    from_user=user.id,
                    to_user=to_user["id"],
                    case_id=case["id"],
                    skill_scores=skill_scores,
                    comments=comments
                )
                st.success("✅ Feedback submitted! Pending approval from your partner.")


    # --- TAB 2: REVIEW RECEIVED FEEDBACK ---
    with tab2:
        st.subheader("Feedback Awaiting Your Approval")

        pending = (
            supabase.table("feedback")
            .select("id, from_user, case_id, skill_scores, comments, created_at")
            .eq("to_user", user.id)
            .eq("status", "pending")
            .execute()
            .data
        )

        if not pending:
            st.info("No pending feedback at the moment.")
        else:
            # Preload mapping for names and case titles
            user_map = {
                u["id"]: u["name"]
                for u in supabase.table("users").select("id, name").execute().data
            }
            case_map = {
                c["id"]: c["title"]
                for c in supabase.table("cases").select("id, title").execute().data
            }

            for fb in pending:
                from_name = user_map.get(fb["from_user"], fb["from_user"])
                case_title = case_map.get(fb["case_id"], fb["case_id"])

                st.markdown(f"**🧑 From:** {from_name}")
                st.markdown(f"**💼 Case:** {case_title}")
                st.caption(f"🕒 Submitted on: {fb['created_at'][:16]}")

                # Display skill ratings as a nice table
                skills = fb["skill_scores"]
                st.table(
                    [{"Skill": k, "Rating (1–5)": v} for k, v in skills.items()]
                )

                if fb.get("comments"):
                    st.write("💬 **Comments:**")
                    st.info(fb["comments"])

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Accept", key=f"accept_{fb['id']}"):
                        update_feedback_status(fb["id"], "accepted")
                        st.success("Accepted feedback ✅")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{fb['id']}"):
                        update_feedback_status(fb["id"], "rejected")
                        st.warning("Rejected feedback ❌")
                        st.rerun()

