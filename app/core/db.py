# app/core/db.py

import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize and cache Supabase client"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase_client()


def get_user_by_email(email: str):
    """Return user record by email."""
    res = supabase.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None


def insert_user_if_not_exists(auth_user, name: str = None):
    """Ensure a profile exists for a given Supabase auth user."""
    uid = auth_user.id
    email = auth_user.email

    existing = supabase.table("users").select("*").eq("id", uid).execute()
    if existing.data:
        return existing.data[0]

    new_user = {
        "id": uid,
        "email": email,
        "name": name or email.split("@")[0],
        "language": "English"
    }
    supabase.table("users").insert(new_user).execute()
    return new_user



def insert_feedback(from_user, to_user, case_id, skill_scores, comments):
    """Insert a new feedback entry (status='pending')."""
    entry = {
        "from_user": from_user,
        "to_user": to_user,
        "case_id": case_id,
        "skill_scores": skill_scores,
        "comments": comments,
        "status": "pending"
    }
    supabase.table("feedback").insert(entry).execute()


def get_feedback_for_user(user_id: str, status: str = "accepted"):
    """Fetch feedback received by user (default = accepted)."""
    res = supabase.table("feedback").select("*").eq("to_user", user_id).eq("status", status).execute()
    return res.data


def update_feedback_status(feedback_id: str, status: str):
    """Accept or reject feedback entry."""
    supabase.table("feedback").update({"status": status}).eq("id", feedback_id).execute()
