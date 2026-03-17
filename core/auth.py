from __future__ import annotations

import streamlit as st


def auth_is_configured() -> bool:
    try:
        auth_config = st.secrets.get("auth", {})
        return bool(
            auth_config.get("client_id")
            and auth_config.get("client_secret")
            and auth_config.get("redirect_uri")
        )
    except (AttributeError, KeyError):
        return False


def init_auth() -> None:
    return None


def auth_sidebar() -> None:
    st.markdown("### Account")

    if not auth_is_configured():
        st.info("Authentication not configured yet.")
        st.caption("Guest mode is active.")
        return

    try:
        if getattr(st.user, "is_logged_in", False):
            name = getattr(st.user, "name", "User")
            email = getattr(st.user, "email", "")

            st.success(f"Signed in as {name}")
            if email:
                st.caption(email)

            if st.button("Log out", use_container_width=True):
                st.logout()
        else:
            st.info("Guest mode (progress saved locally).")
            if st.button("Sign in with Google", use_container_width=True):
                st.login()
    except (AttributeError, RuntimeError):
        st.info("Authentication UI temporarily unavailable.")


def account_badge() -> None:
    try:
        if getattr(st.user, "is_logged_in", False):
            email = getattr(st.user, "email", "")
            if email:
                st.caption(f"☁️ Synced account: {email}")
            else:
                st.caption("☁️ Synced account")
        else:
            st.caption("💾 Local guest progress")
    except (AttributeError, RuntimeError):
        st.caption("💾 Local guest progress")