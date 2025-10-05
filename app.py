import streamlit as st
from app.core.auth import check_session, login_ui, logout_button
from app.tabs import (
    tab1_analytics,
    tab2_case_recommendations,
    tab3_partner_recommendations,
    tab4_feedback_input
)

st.set_page_config(page_title="HEC Case Club", page_icon="🎓", layout="wide")



user = check_session()

if not user:
    login_ui()
else:
    st.sidebar.write(f"👋 Logged in as {user.email}")
    logout_button()

    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Settings")

    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.sidebar.success("Data was updated.")

    tabs = st.tabs([
        "📊 Analytics",
        "💼 Case Recommendations",
        "🤝 Partner Recommendations",
        "📝 Feedback Input"
    ])

    with tabs[0]:
        tab1_analytics.render(user)

    with tabs[1]:
        tab2_case_recommendations.render(user)

    with tabs[2]:
        tab3_partner_recommendations.render(user)

    with tabs[3]:
        tab4_feedback_input.render(user)
