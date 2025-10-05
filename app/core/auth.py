# app/core/auth.py

import streamlit as st
from supabase import create_client
from app.core.db import insert_user_if_not_exists

@st.cache_resource
def get_supabase_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase_client()

# --- AUTH HANDLERS --- #

def check_session():
    """Return current user session, if logged in."""
    return st.session_state.get("user", None)

def login_ui():
    """Render login/signup UI."""
    st.title("🔐 Login to HEC Case Club")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # ---- LOGIN ---- #
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["user"] = user.user
                st.success(f"Welcome back, {email}")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    # ---- SIGN UP ---- #
    with tab2:
        email2 = st.text_input("Email (Sign Up)", key="signup_email")
        password2 = st.text_input("Password (Sign Up)", type="password", key="signup_pw")
        name = st.text_input("Full name", key="signup_name")
        if st.button("Create Account"):
            try:
                user = supabase.auth.sign_up({"email": email2, "password": password2})
                insert_user_if_not_exists(user.user, name=name)
                st.success("✅ Account created! Please log in.")
            except Exception as e:
                st.error(f"Signup failed: {e}")

def logout_button():
    """Show logout button in sidebar."""
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.rerun()
