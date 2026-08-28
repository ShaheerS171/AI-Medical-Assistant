"""
streamlit_auth.py - Plug-and-Play Streamlit Authentication Component for Supabase

Your friend can import this component directly into frontend.py to add Sign In & Sign Out:
    from streamlit_auth import render_auth_ui

    is_authenticated, user_info = render_auth_ui()
    if not is_authenticated:
        st.stop()  # Require Sign In to access the rest of the application
"""

import os
import streamlit as st
from supabase_auth import SupabaseAuthManager

# Initialize Auth Manager
auth_manager = SupabaseAuthManager()

def render_auth_ui(location="sidebar"):
    """
    Renders Sign In / Sign Up / Sign Out UI components in Streamlit.
    
    Returns:
        tuple: (is_authenticated: bool, user_info: dict | None)
    """
    # Check session state
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "session" not in st.session_state:
        st.session_state["session"] = None

    container = st.sidebar if location == "sidebar" else st

    # =========================================================================
    # USER IS LOGGED IN -> Show Profile & Sign Out Button
    # =========================================================================
    if st.session_state["user"] is not None:
        user = st.session_state["user"]
        email = user.get("email", "User")
        name = user.get("metadata", {}).get("full_name", email.split("@")[0])

        with container:
          st.markdown("### 👤 User Profile")
          st.success(f"Logged in as **{name}**")
          st.caption(f"📧 {email}")

          if st.button("🚪 Sign Out", type="secondary", key="btn_st_signout", use_container_width=True):
              # Perform Sign Out
              token = st.session_state["session"].get("access_token", "") if st.session_state["session"] else ""
              if token:
                  auth_manager.sign_out(token)
              
              st.session_state["user"] = None
              st.session_state["session"] = None
              st.toast("Signed out successfully!", icon="ℹ️")
              st.rerun()

        return True, st.session_state["user"]

    # =========================================================================
    # USER IS NOT LOGGED IN -> Show Sign In / Sign Up Forms
    # =========================================================================
    with container:
        st.markdown("### 🔑 Authentication")

        if not auth_manager.is_configured():
            st.warning(
                "⚠️ **Supabase Credentials Needed**\n\n"
                "Please add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to your `.env` file."
            )
            return False, None

        tab_signin, tab_signup = st.tabs(["🔒 Sign In", "📝 Sign Up"])

        # ------------ SIGN IN TAB ------------
        with tab_signin:
            with st.form("form_signin"):
                email = st.text_input("Email", placeholder="user@example.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Please enter email and password.")
                    else:
                        res = auth_manager.sign_in(email, password)
                        if res.get("success"):
                            st.session_state["user"] = res["user"]
                            st.session_state["session"] = res["session"]
                            st.success("Signed in successfully!")
                            st.rerun()
                        else:
                            st.error(f"Sign in failed: {res.get('error')}")

        # ------------ SIGN UP TAB ------------
        with tab_signup:
            with st.form("form_signup"):
                full_name = st.text_input("Full Name", placeholder="John Doe")
                email_up = st.text_input("Email", placeholder="user@example.com")
                password_up = st.text_input("Password", type="password", help="At least 6 characters")
                submit_up = st.form_submit_button("Create Account", use_container_width=True)

                if submit_up:
                    if not email_up or not password_up:
                        st.error("Please fill in all required fields.")
                    else:
                        res = auth_manager.sign_up(email_up, password_up, full_name=full_name)
                        if res.get("success"):
                            if res.get("requires_email_confirmation"):
                                st.info("Registration successful! Please check your email to confirm.")
                            else:
                                st.session_state["user"] = res.get("user")
                                st.session_state["session"] = res.get("session")
                                st.success("Account created and logged in!")
                                st.rerun()
                        else:
                            st.error(f"Sign up failed: {res.get('error')}")

    return False, None
