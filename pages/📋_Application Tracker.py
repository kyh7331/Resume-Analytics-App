import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

st.set_page_config(
    page_title="지원 이력",
    page_icon="📋",
    layout="wide"
)
st.title("📋 지원 이력")
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

status_labels = {
    "applied": "📝 지원 완료",
    "screening": "📞 스크리닝 콜",
    "interview": "🤝 인터뷰",
    "offer": "🎉 오퍼",
    "rejected": "❌ 탈락",
    "withdrawn": "🚫 지원 취소"
}

def load_applications():
    try:
        response = supabase.table("applications").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"지원 이력 로드 오류: {e}")
        return []

def update_application_status(application_id, status, notes=""):
    try:
        supabase.table("applications").update({
            "status": status,
            "notes": notes
        }).eq("id", application_id).execute()
        
        supabase.table("application_status_history").insert({
            "application_id": application_id,
            "status": status,
            "notes": notes
        }).execute()
    except Exception as e:
        st.error(f"상태 업데이트 오류: {e}")

applications = load_applications()

if not applications:
    st.info("아직 지원한 이력이 없습니다.")
else:
    for app in applications:
        with st.expander(f"{app['company_name']} - {app['job_title']} | {status_labels.get(app['status'], app['status'])} | {app['applied_date']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**회사:** {app['company_name']}")
                st.write(f"**포지션:** {app['job_title']}")
                st.write(f"**지원일:** {app['applied_date']}")
                st.write(f"**현재 상태:** {status_labels.get(app['status'], app['status'])}")
            
            with col2:
                new_status = st.selectbox(
                    "상태 변경",
                    options=list(status_labels.keys()),
                    format_func=lambda x: status_labels[x],
                    index=list(status_labels.keys()).index(app['status']),
                    key=f"status_{app['id']}"
                )
                notes = st.text_input("메모", value=app.get("notes", "") or "", key=f"notes_{app['id']}")
                
                if st.button("업데이트", key=f"update_{app['id']}"):
                    update_application_status(app['id'], new_status, notes)
                    st.success("업데이트 완료!")
                    st.rerun()
            
            if app.get("notes"):
                st.write(f"**메모:** {app['notes']}")
            
            if app.get("analysis_result"):
                with st.expander("📊 분석 결과 보기"):
                    st.markdown(app['analysis_result'])