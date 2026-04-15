import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import anthropic
from openai import OpenAI

LLM_MODE = os.getenv("LLM_MODE", "local")

if LLM_MODE == "claude":
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
else:
    from openai import OpenAI
    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio"
    )
    
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

lang = st.sidebar.radio("Analysis Language", ["한국어", "English"], horizontal=True)

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

def get_rejection_feedback(analysis, jd, company, position, lang="English"):
    if lang == "English":
        system_prompt = """You are a honest career advisor. Analyze why a candidate was likely rejected and provide actionable feedback. Be concise and direct. No sugarcoating."""
        user_message = f"""
This candidate applied to {company} - {position} but was rejected.

Previous Analysis:
{analysis[:2000]}

Job Description:
{jd[:1000]}

Provide ONLY:
**Likely Rejection Reasons:**
- (2-3 keywords/short phrases)

**Improve For Next Time:**
- (2-3 specific actionable items)
"""
    else:
        system_prompt = """당신은 솔직한 커리어 어드바이저입니다. 지원자가 왜 탈락했는지 분석하고 실질적인 피드백을 제공하세요. 간결하고 직접적으로. 과도한 긍정 표현 금지."""
        user_message = f"""
이 지원자는 {company} - {position}에 지원했지만 탈락했습니다.

이전 분석 결과:
{analysis[:2000]}

Job Description:
{jd[:1000]}

아래 형식으로만 답변하세요:
**탈락 예상 원인:**
- (2-3개 키워드/짧은 문장)

**다음 지원을 위한 개선점:**
- (2-3개 구체적인 실행 항목)
"""

    if LLM_MODE == "claude":
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    else:
        response = client.chat.completions.create(
            model="gemma-3-27b",
            max_tokens=1500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content

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
                with st.expander("📊 View Analysis"):
                    st.markdown(app['analysis_result'])
            
            if app.get("status") == "rejected":
                if st.button("🔍 Get Rejection Feedback", key=f"btn_feedback_{app['id']}"):
                    with st.spinner("Analyzing rejection..."):
                        try:
                            feedback = get_rejection_feedback(
                                analysis=app.get("analysis_result", ""),
                                jd=app.get("jd_text", ""),
                                company=app.get("company_name", ""),
                                position=app.get("job_title", ""),
                                lang=lang
                            )
                            st.session_state[f"result_feedback_{app['id']}"] = feedback
                        except Exception as e:
                            st.error(f"에러: {e}")

# expander 루프 끝난 후
for app in applications:
    feedback_key = f"result_feedback_{app['id']}"
    if st.session_state.get(feedback_key):
        st.markdown(f"### 💡 {app['company_name']} - {app['job_title']} Rejection Feedback")
        st.markdown(st.session_state[feedback_key])
        if st.button("닫기", key=f"close_feedback_{app['id']}"):
            del st.session_state[feedback_key]
            st.rerun()