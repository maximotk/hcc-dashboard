# app/core/scheduling.py
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional
from app.core.db import supabase
import streamlit as st

SLOT_MINUTES = 90

def _to_utc(dt_local: datetime, tz_str: str) -> datetime:
    """Assumes dt_local naive in user's tz; returns aware UTC."""
    tz = ZoneInfo(tz_str or "Europe/Paris")
    return dt_local.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))

@st.cache_data(ttl=300)
def get_slots_for_user(user_id: str, include_booked: bool = False):
    q = supabase.table("availability_slots").select("*").eq("user_id", user_id)
    if not include_booked:
        q = q.eq("is_booked", False)
    return q.order("start_ts", desc=False).execute().data or []

@st.cache_data(ttl=300)
def get_bookable_slots_for_host(host_id: str, now_utc: Optional[datetime] = None):
    now_utc = now_utc or datetime.utcnow()
    return (
        supabase.table("availability_slots")
        .select("*")
        .eq("user_id", host_id)
        .eq("is_booked", False)
        .gte("start_ts", now_utc.isoformat() + "Z")
        .order("start_ts", desc=False)
        .execute()
        .data or []
    )

def add_slots(user_id: str, starts_local: List[datetime], tz_str: str):
    """Create 90-min slots from given local datetimes."""
    rows = []
    for dt in starts_local:
        start_utc = _to_utc(dt, tz_str)
        rows.append({"start_ts": start_utc.isoformat()})  # ⟵ only start_ts

    if not rows:
        st.info("Select at least one date and time.")
        return

    try:
        supabase.table("availability_slots").insert(rows).execute()
    except Exception as e:
        st.error(f"Failed to add slots. {type(e).__name__}: {getattr(e, 'args', [''])[0]}")
        raise
    finally:
        st.cache_data.clear()

def delete_slot(slot_id: str, user_id: str):
    supabase.table("availability_slots").delete().eq("id", slot_id).eq("user_id", user_id).execute()
    st.cache_data.clear()

def _mark_slot_booked(slot_id: str) -> bool:
    # try to atomically mark booked; if already booked, no row returns
    res = supabase.table("availability_slots").update({"is_booked": True}).eq("id", slot_id).eq("is_booked", False).execute()
    return bool(res.data)

def book_slot(slot_id: str, host_id: str, guest_id: str, notes: str = "") -> Optional[str]:
    """Returns appointment id if success, else None."""
    if not _mark_slot_booked(slot_id):
        return None
    appt = {
        "slot_id": slot_id,
        "host_id": host_id,
        "guest_id": guest_id,
        "status": "pending",
        "notes": notes
    }
    res = supabase.table("appointments").insert(appt).execute()
    st.cache_data.clear()
    return res.data[0]["id"] if res.data else None

def list_my_appointments(user_id: str):
    return (
        supabase.table("appointments")
        .select("id, slot_id, host_id, guest_id, status, notes, created_at, availability_slots(start_ts,end_ts,user_id)")
        .or_(f"host_id.eq.{user_id},guest_id.eq.{user_id}")
        .order("created_at", desc=True)
        .execute()
        .data or []
    )

def update_appointment_status(appt_id: str, new_status: str, actor_id: str):
    # Trust RLS to authorize
    supabase.table("appointments").update({"status": new_status}).eq("id", appt_id).execute()
    if new_status in ("cancelled",):
        # free the slot again
        appt = supabase.table("appointments").select("slot_id").eq("id", appt_id).single().execute().data
        if appt:
            supabase.table("availability_slots").update({"is_booked": False}).eq("id", appt["slot_id"]).execute()
    st.cache_data.clear()
