import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

st.set_page_config(page_title="Profile", page_icon="👤", layout="centered")
st.title("👤 My Profile")

if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.stop()

user_id = st.session_state.user["id"]
user_email = st.session_state.user["email"]

def load_profile():
    try:
        response = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        return {}
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        return {}

def save_profile(profile):
    try:
        existing = supabase.table("user_profiles").select("id").eq("id", user_id).execute()
        if existing.data:
            supabase.table("user_profiles").update(profile).eq("id", user_id).execute()
        else:
            profile["id"] = user_id
            profile["email"] = user_email
            supabase.table("user_profiles").insert(profile).execute()
        return True
    except Exception as e:
        st.error(f"Error saving profile: {e}")
        return False

profile = load_profile()

with st.form("profile_form"):
    st.markdown("#### Basic Info")
    full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
    current_location = st.text_input("Current Location", value=profile.get("current_location", ""), placeholder="e.g. Centreville, VA")

    st.markdown("---")
    st.markdown("#### Job Search Preferences")

    willing_to_relocate = st.selectbox(
        "Willing to Relocate?",
        options=["yes", "no", "open"],
        format_func=lambda x: {"yes": "Yes", "no": "No", "open": "Open to Discussion"}[x],
        index=["yes", "no", "open"].index(profile.get("willing_to_relocate", "open"))
    )

    relocation_cities = st.text_input(
        "Preferred Relocation Cities (if any)",
        value=profile.get("relocation_cities", ""),
        placeholder="e.g. Charlotte NC, Austin TX"
    )

    require_sponsorship = st.selectbox(
        "Will you require sponsorship?",
        options=["no", "yes", "authorized"],
        format_func=lambda x: {
            "no": "No",
            "yes": "Yes, I need sponsorship",
            "authorized": "No, I'm authorized to work"
        }[x],
        index=["no", "yes", "authorized"].index(profile.get("require_sponsorship", "no"))
    )

    security_clearance = st.selectbox(
        "Security Clearance",
        options=["none", "active", "expired"],
        format_func=lambda x: {
            "none": "None",
            "active": "Active",
            "expired": "Expired"
        }[x],
        index=["none", "active", "expired"].index(profile.get("security_clearance", "none"))
    )

    st.markdown("---")
    st.markdown("#### Target Salary")
    col1, col2 = st.columns(2)
    with col1:
        salary_min = st.number_input("Minimum ($)", value=profile.get("salary_min", 0), step=5000)
    with col2:
        salary_max = st.number_input("Maximum ($)", value=profile.get("salary_max", 0), step=5000)

    st.markdown("---")
    st.markdown("#### Education")
    degree = st.selectbox(
        "Highest Degree",
        options=["", "High School", "Associate's", "Bachelor's", "Master's", "MBA", "PhD", "Other"],
        index=["", "High School", "Associate's", "Bachelor's", "Master's", "MBA", "PhD", "Other"].index(
            profile.get("degree", "")
        )
    )
    major = st.text_input("Major / Field of Study", value=profile.get("major", ""))
    school = st.text_input("School", value=profile.get("school", ""))
    graduation_year = st.number_input("Graduation Year", value=profile.get("graduation_year", 2000), min_value=1970, max_value=2030, step=1)

    st.markdown("---")
    st.markdown("#### Career Direction")
    target_industries = st.multiselect(
        "Target Industries",
        options=["Financial Services", "FinTech", "Technology", "Healthcare", "Consulting", "Government", "Retail", "Other"],
        default=profile.get("target_industries", "").split(",") if profile.get("target_industries") else []
    )

    target_functions = st.multiselect(
        "Target Functions",
        options=["Strategy & Planning", "Data & Analytics", "Product Management", "Business Operations", "Marketing", "Risk & Compliance", "Finance", "Other"],
        default=profile.get("target_functions", "").split(",") if profile.get("target_functions") else []
    )

    target_title_level = st.selectbox(
        "Target Title Level",
        options=["", "Analyst", "Senior Analyst", "Manager", "Senior Manager", "Director", "VP", "SVP/C-Suite"],
        index=["", "Analyst", "Senior Analyst", "Manager", "Senior Manager", "Director", "VP", "SVP/C-Suite"].index(
            profile.get("target_title_level", "")
        )
    )

    submitted = st.form_submit_button("💾 Save Profile", type="primary")

    if submitted:
        new_profile = {
            "full_name": full_name,
            "current_location": current_location,
            "willing_to_relocate": willing_to_relocate,
            "relocation_cities": relocation_cities,
            "require_sponsorship": require_sponsorship,
            "security_clearance": security_clearance,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "degree": degree,
            "major": major,
            "school": school,
            "graduation_year": graduation_year,
            "target_industries": ",".join(target_industries),
            "target_functions": ",".join(target_functions),
            "target_title_level": target_title_level,
            "updated_at": "now()"
        }
        if save_profile(new_profile):
            st.success("Profile saved!")