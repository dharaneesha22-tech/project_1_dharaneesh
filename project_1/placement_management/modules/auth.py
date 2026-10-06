"""
Authentication module: login/logout UI and session handling.
"""

import streamlit as st
from utils.security import authenticate_user, login_user, logout_user, init_session_state


def show_login_page():
    """Render the login page and handle authentication."""
    # Custom CSS for login page
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 420px;
            margin: 0 auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            padding: 1.5rem 0;
        }
        .college-logo {
            font-size: 3rem;
            text-align: center;
        }
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            border: none;
            padding: 0.6rem;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Centered layout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div class='login-header'>
                <div class='college-logo'>🎓</div>
                <h1 style='color:#1e3c72; margin:0; font-size:1.8rem;'>
                    Smart Placement Portal
                </h1>
                <p style='color:#666; margin:0;'>
                    College Placement Management System
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                help="Use your college-issued username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )
            submitted = st.form_submit_button("Sign In")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                with st.spinner("Authenticating..."):
                    user = authenticate_user(username.strip(), password)
                if user:
                    login_user(user)
                    st.success(f"Welcome back, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")

        st.markdown(
            """
            <div style='text-align:center; margin-top:1.5rem;
                        font-size:0.8rem; color:#888;'>
                For credentials, contact your placement coordinator.<br>
                Default admin: <b>admin</b> / <b>Admin@123</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_logout_button():
    """Show a logout button in the sidebar."""
    st.sidebar.divider()
    user = st.session_state.get("user", {})
    st.sidebar.markdown(
        f"""
        <div style='padding:0.5rem; background:#f0f4ff;
                    border-radius:8px; margin-bottom:0.5rem;'>
            <b>👤 {user.get('full_name','User')}</b><br>
            <span style='color:#666; font-size:0.85rem;'>
                {user.get('role','')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.rerun()
