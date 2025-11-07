import streamlit as st
from app.core.db import get_user_profile, update_my_profile

def render(user):
    st.header("👤 My Profile")

    prof = get_user_profile(user.id) or {}

    # Quick preview card
    with st.container():
        st.subheader("Profile Preview")
        colA, colB = st.columns([2, 1])
        with colA:
            st.markdown(f"**Name:** {prof.get('name', user.email.split('@')[0])}")
            st.markdown(f"**Language:** {prof.get('language', 'English')}")
            st.markdown(f"**Experience:** {prof.get('experience_level', 'Beginner')}")
            st.markdown(f"**Timezone:** {prof.get('timezone', 'Europe/Paris')}")
            firms = ", ".join(prof.get("firms_applying", []) or [])
            st.markdown(f"**Firms applying to:** {firms or '—'}")
            st.markdown(f"**Availability:** {prof.get('availability', '—')}")
            st.markdown(f"**LinkedIn:** {prof.get('linkedin_url', '—')}")
        with colB:
            st.info(prof.get("bio") or "Add a short bio so others can get to know you.")


    st.divider()
    with st.expander("✏️ Edit Profile", expanded=False):
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Full name", prof.get("name", user.email.split("@")[0]))
            language = col2.text_input("Language", prof.get("language", "English"))

            exp_level = col1.selectbox(
                "Experience level",
                ["Beginner", "Intermediate", "Advanced"],
                index=["Beginner","Intermediate","Advanced"].index(
                    prof.get("experience_level", "Beginner")
                ),
            )
            tz = col2.text_input("Timezone (IANA)", prof.get("timezone", "Europe/Paris"))

            firms_all = [
                "McKinsey","BCG","Bain","Roland Berger","Oliver Wyman",
                "EY-Parthenon","Strategy&","Kearney"
            ]
            firms = st.multiselect(
                "Firms you’re applying to",
                firms_all,
                prof.get("firms_applying", []),
            )

            bio = st.text_area("Short bio", prof.get("bio", ""))
            availability = st.text_input("Availability (e.g., Evenings, Weekends, CET)", prof.get("availability", ""))
            linkedin = st.text_input("LinkedIn URL", prof.get("linkedin_url", ""))

            saved = st.form_submit_button("💾 Save Profile")
            if saved:
                update_my_profile(user.id, {
                    "name": name,
                    "language": language,
                    "experience_level": exp_level,
                    "timezone": tz,
                    "firms_applying": firms,
                    "bio": bio,
                    "availability": availability,
                    "linkedin_url": linkedin,
                })
                st.success("Profile updated ✅")
                st.rerun()
