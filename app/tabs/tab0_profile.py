import streamlit as st
from app.core.db import get_user_profile, update_my_profile

from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo
from app.core.scheduling import get_slots_for_user, add_slots, delete_slot, list_my_appointments, update_appointment_status, SLOT_MINUTES


def render(user):
    st.header("👤 My Profile")

    prof = get_user_profile(user.id) or {}
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

    with st.container():
        st.subheader("Calendar")
        with st.expander("📅 My Availability (next 2 weeks)", expanded=False):
            prof = get_user_profile(user.id) or {}
            tz_str = prof.get("timezone") or "Europe/Paris"

            # 1) Create slots
            st.caption(f"Times shown in your timezone: **{tz_str}**")
            col1, col2 = st.columns(2)
            days = col1.multiselect(
                "Pick dates (next 14 days)",
                [date.today() + timedelta(days=i) for i in range(0, 14)],
                []
            )
            start_times = col2.multiselect(
                "Pick start times",
                [time(h, m) for h in range(7, 22) for m in (0,30)],
                []
            )
            if st.button("➕ Add 90-min slots"):
                starts_local = [datetime.combine(d, t) for d in days for t in start_times]
                if starts_local:
                    add_slots(user.id, starts_local, tz_str)
                    st.success(f"Added {len(starts_local)} slot(s).")
                    st.rerun()
                else:
                    st.info("Select at least one date and time.")

            # 2) List & delete my slots
            st.write("### Open Slots")
            slots = get_slots_for_user(user.id, include_booked=False)
            if not slots:
                st.caption("No open slots.")
            else:
                for s in slots:
                    start_local = datetime.fromisoformat(s["start_ts"].replace("Z","+00:00")).astimezone(ZoneInfo(tz_str))
                    end_local   = datetime.fromisoformat(s["end_ts"].replace("Z","+00:00")).astimezone(ZoneInfo(tz_str))
                    cols = st.columns([3,1])
                    cols[0].markdown(f"**{start_local:%a %d %b %H:%M} → {end_local:%H:%M}**")
                    if cols[1].button("🗑️ Delete", key=f"del_{s['id']}"):
                        delete_slot(s["id"], user.id)
                        st.rerun()

        with st.expander("📔 My Appointments", expanded=False):
            tz_str = (get_user_profile(user.id) or {}).get("timezone") or "Europe/Paris"
            appts = list_my_appointments(user.id)
            if not appts:
                st.caption("No appointments yet.")
            else:
                for a in appts:
                    slot = a["availability_slots"]
                    start_local = datetime.fromisoformat(slot["start_ts"].replace("Z","+00:00")).astimezone(ZoneInfo(tz_str))
                    end_local   = datetime.fromisoformat(slot["end_ts"].replace("Z","+00:00")).astimezone(ZoneInfo(tz_str))
                    who = "Host" if a["host_id"] == user.id else "Guest"
                    st.markdown(f"**{start_local:%a %d %b %H:%M} → {end_local:%H:%M}** · _{who}_ · **{a['status']}**")
                    c1, c2, c3 = st.columns(3)
                    if a["host_id"] == user.id and a["status"] == "pending":
                        if c1.button("✅ Confirm", key=f"c_{a['id']}"):
                            update_appointment_status(a["id"], "confirmed", user.id); st.rerun()
                    if a["status"] in ("pending","confirmed"):
                        if c2.button("❌ Cancel", key=f"x_{a['id']}"):
                            update_appointment_status(a["id"], "cancelled", user.id); st.rerun()
                    if a.get("notes"):
                        c3.write(a["notes"])