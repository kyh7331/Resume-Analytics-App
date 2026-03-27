import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")
st.title("🔐 Resume Analyzer")

if st.session_state.get("user"):
    st.success(f"Logged in as {st.session_state.user['email']}")
    if st.button("Log Out"):
        st.session_state.user = None
        st.rerun()
else:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = {
                    "id": response.user.id,
                    "email": response.user.email
                }
                st.success("Logged in!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")
    
    with tab2:
        st.subheader("Sign Up")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        new_password2 = st.text_input("Confirm Password", type="password", key="signup_password2")
        
        if st.button("Sign Up", type="primary"):
            if new_password != new_password2:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    response = supabase.auth.sign_up({
                        "email": new_email,
                        "password": new_password
                    })
                    st.session_state.user = {
                        "id": response.user.id,
                        "email": response.user.email
                    }
                    st.success("Account created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign up failed: {e}")