import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os


load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard")
# 세션 복구
if not st.session_state.get("user"):
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = {
                "id": session.user.id,
                "email": session.user.email
            }
    except:
        pass

if not st.session_state.get("user"):
    st.warning("Please log in first.")
    st.stop()

def load_applications():
    try:
        response = supabase.table("applications").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading applications: {e}")
        return []

applications = load_applications()

if not applications:
    st.info("No application data yet. Start applying and tracking to see your dashboard!")
else:
    # 기본 통계
    total = len(applications)
    status_counts = {}
    for app in applications:
        s = app["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    screening = status_counts.get("screening", 0)
    interview = status_counts.get("interview", 0)
    offer = status_counts.get("offer", 0)
    rejected = status_counts.get("rejected", 0)

    # 상단 메트릭
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Applied", total)
    col2.metric("Screening", screening, f"{round(screening/total*100)}%" if total else "0%")
    col3.metric("Interview", interview, f"{round(interview/total*100)}%" if total else "0%")
    col4.metric("Offer", offer, f"{round(offer/total*100)}%" if total else "0%")
    col5.metric("Rejected", rejected, f"{round(rejected/total*100)}%" if total else "0%")

    st.markdown("---")

    # 회사별 / 상태별 테이블
    st.subheader("Application List")
    status_labels = {
        "applied": "📝 Applied",
        "screening": "📞 Screening",
        "interview": "🤝 Interview",
        "offer": "🎉 Offer",
        "rejected": "❌ Rejected",
        "withdrawn": "🚫 Withdrawn"
    }

    for app in applications:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{app['company_name']}** — {app['job_title']}")
        with col2:
            st.write(status_labels.get(app["status"], app["status"]))
        with col3:
            st.write(app["applied_date"])