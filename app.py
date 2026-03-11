from __future__ import annotations

from typing import Any, Callable, Dict

import streamlit as st

import lessons
from core import ai, debug, explain, file_analyzer, memory, practice, project, review, run_project
from progress import get_learning_profile, init_progress_db, load_progress

try:
    from core.auth import account_badge, auth_sidebar, init_auth
except ImportError:
    account_badge = None
    auth_sidebar = None
    init_auth = None


APP_TITLE = "Pylot"
APP_ICON = "🐍"

MODE_RENDERERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "Course Mode": lessons.render,
    "Practice Mode": practice.render,
    "Project Mode": project.render,
    "Run/Test Mode": run_project.render,
    "AI Mode": ai.render,
    "Debug Mode": debug.render,
    "Explain Mode": explain.render,
    "Review Mode": review.render,
    "File Analyzer Mode": file_analyzer.render,
    "Shared Memory Admin": memory.render,
}

MODE_OPTIONS = [
    "Home",
    "Course Mode",
    "Practice Mode",
    "Project Mode",
    "Run/Test Mode",
    "AI Mode",
    "Debug Mode",
    "Explain Mode",
    "Review Mode",
    "File Analyzer Mode",
    "Shared Memory Admin",
]


def configure_page() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        div[data-testid="stSidebar"] {
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }

        .pylot-shell-card {
            padding: 1rem;
            border-radius: 18px;
            background: rgb(248, 250, 252);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-bottom: 1rem;
        }

        .pylot-hero {
            padding: 1.25rem;
            border-radius: 22px;
            background: linear-gradient(
                135deg,
                rgba(15, 23, 42, 1) 0%,
                rgba(30, 41, 59, 1) 100%
            );
            color: white;
            margin-bottom: 1rem;
        }

        .pylot-card {
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 1rem;
            background: white;
            min-height: 170px;
            margin-bottom: 0.85rem;
        }

        .pylot-muted {
            color: rgb(71, 85, 105);
        }

        .pylot-hero-muted {
            color: rgba(255, 255, 255, 0.78);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_app_state() -> Dict[str, Any]:
    init_progress_db()

    st.session_state.setdefault("selected_mode", "Home")
    st.session_state.setdefault("selected_lesson_id", None)
    st.session_state.setdefault("selected_project_id", None)
    st.session_state.setdefault("review_target_type", None)
    st.session_state.setdefault("review_target_id", None)
    st.session_state.setdefault("review_target_code", "")

    progress_data = load_progress()
    st.session_state["progress_data"] = progress_data
    return progress_data


def init_auth_safely() -> str:
    if init_auth is None:
        return "Authentication module unavailable. Running in guest mode."

    try:
        init_auth()
        return ""
    except (AttributeError, RuntimeError, KeyError):
        return "Authentication is not configured. Running in guest mode."


def render_auth_block() -> None:
    if auth_sidebar is not None:
        try:
            auth_sidebar()
            if account_badge is not None:
                account_badge()
            return
        except (AttributeError, RuntimeError, KeyError):
            pass

    st.markdown("### Account")
    st.info("Guest mode is active.")
    st.caption("Authentication is unavailable or not configured.")


def clear_detail_navigation() -> None:
    st.session_state["selected_lesson_id"] = None
    st.session_state["selected_project_id"] = None


def navigate_to(mode: str) -> None:
    clear_detail_navigation()
    st.session_state["selected_mode"] = mode
    st.rerun()


def render_sidebar() -> None:
    profile = get_learning_profile()
    current_mode = st.session_state.get("selected_mode", "Home")
    current_index = MODE_OPTIONS.index(current_mode) if current_mode in MODE_OPTIONS else 0

    with st.sidebar:
        st.markdown("## Navigation")

        selected_mode = st.radio(
            "Choose a mode",
            options=MODE_OPTIONS,
            index=current_index,
            key="mode_selector",
            label_visibility="collapsed",
        )
        st.session_state["selected_mode"] = selected_mode

        st.markdown("---")
        st.markdown("### Learning Profile")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Lessons", profile["completed_lessons"])
        with col2:
            st.metric("Projects", profile["completed_projects"])

        st.caption(f"Recommended mode: {profile['recommended_mode']}")
        st.caption(f"Focus topic: {profile['recommended_topic']}")

        top_weak_topics = profile.get("top_weak_topics", [])
        if top_weak_topics:
            st.markdown("### Weak Topics")
            for topic, score in top_weak_topics:
                st.write(f"- {topic} ({score})")
        else:
            st.caption("No major weak topics detected yet.")

        st.markdown("---")
        render_auth_block()

        st.markdown("---")
        if st.button("Return to Home", use_container_width=True):
            navigate_to("Home")


def render_shell_header(mode: str, auth_message: str) -> None:
    st.markdown(
        f"""
        <div class="pylot-shell-card">
            <h2 style="margin:0;">{APP_ICON} {APP_TITLE}</h2>
            <p class="pylot-muted" style="margin:0.35rem 0 0 0;">
                Interactive Python learning with lessons, practice, projects, AI tutoring,
                debugging tools, code review, and progress tracking.
            </p>
            <p class="pylot-muted" style="margin:0.45rem 0 0 0;">
                Current mode: <strong>{mode}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if auth_message:
        st.caption(auth_message)


def render_home_hero(profile: Dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="pylot-hero">
            <h2 style="margin:0;">Build real Python skills with guided practice</h2>
            <p class="pylot-hero-muted" style="margin:0.45rem 0 0 0;">
                Pylot combines structured lessons, adaptive practice, milestone projects,
                code review, and an AI tutor into one learning workflow.
            </p>
            <p class="pylot-hero-muted" style="margin:0.75rem 0 0 0;">
                Recommended next step: <strong>{profile["recommended_mode"]}</strong>
                &nbsp;•&nbsp;
                Focus topic: <strong>{profile["recommended_topic"]}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_metrics(profile: Dict[str, Any]) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Completed Lessons", profile["completed_lessons"])
    with col2:
        st.metric("Completed Projects", profile["completed_projects"])
    with col3:
        st.metric("Review Passes", profile["review_passed_count"])
    with col4:
        weak_topic_count = len(profile.get("weak_topics", {}))
        st.metric("Weak Topics", weak_topic_count)


def render_quick_start_actions(profile: Dict[str, Any]) -> None:
    st.markdown("### Quick Start")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Open Recommended Mode", use_container_width=True):
            navigate_to(profile["recommended_mode"])

    with col2:
        if st.button("Continue Lessons", use_container_width=True):
            navigate_to("Course Mode")

    with col3:
        if st.button("Practice Weak Topics", use_container_width=True):
            navigate_to("Practice Mode")


def render_focus_panel(profile: Dict[str, Any]) -> None:
    st.markdown("### Focus Areas")

    top_weak_topics = profile.get("top_weak_topics", [])
    if not top_weak_topics:
        st.success("No major weak topics detected yet. You are in a good position to keep progressing.")
        return

    for topic, score in top_weak_topics:
        st.markdown(
            f"""
            <div class="pylot-card">
                <h4 style="margin:0;">{topic}</h4>
                <p class="pylot-muted" style="margin:0.4rem 0 0 0;">
                    Current weakness score: <strong>{score}</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_home_mode_cards() -> None:
    st.markdown("### Explore Modes")

    mode_descriptions = [
        ("Course Mode", "Follow structured lessons across beginner, intermediate, and advanced topics."),
        ("Practice Mode", "Get targeted exercises based on weak topics and recent review results."),
        ("Project Mode", "Build milestone-based Python projects and unlock completion through review."),
        ("Run/Test Mode", "Validate syntax and run Python code directly inside the app."),
        ("AI Mode", "Ask natural Python questions, debug code, and request examples or exercises."),
        ("Debug Mode", "Paste broken code and tracebacks to get structured debugging help."),
        ("Explain Mode", "Get concept or code explanations."),
        ("Review Mode", "Run completion-gating code review for lessons and projects."),
        ("File Analyzer Mode", "Upload Python files and inspect imports, functions, classes, and issues."),
        ("Shared Memory Admin", "Inspect and manage shared AI memory entries."),
    ]

    col1, col2 = st.columns(2)
    columns = [col1, col2]

    for index, (mode_name, description) in enumerate(mode_descriptions):
        with columns[index % 2]:
            st.markdown(
                f"""
                <div class="pylot-card">
                    <h4 style="margin:0;">{mode_name}</h4>
                    <p style="margin:0.4rem 0 0 0; color: rgb(71, 85, 105);">
                        {description}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open {mode_name}", key=f"home_open_{mode_name}", use_container_width=True):
                navigate_to(mode_name)


def render_home(progress_data: Dict[str, Any]) -> None:
    _ = progress_data
    profile = get_learning_profile()

    render_home_hero(profile)
    render_home_metrics(profile)
    render_quick_start_actions(profile)

    left_col, right_col = st.columns([2, 1])
    with left_col:
        render_home_mode_cards()
    with right_col:
        render_focus_panel(profile)


def render_selected_mode(progress_data: Dict[str, Any]) -> None:
    selected_mode = st.session_state.get("selected_mode", "Home")

    if selected_mode == "Home":
        render_home(progress_data)
        return

    renderer = MODE_RENDERERS.get(selected_mode)
    if renderer is None:
        st.error(f"Unknown mode: {selected_mode}")
        return

    renderer(progress_data)


def main() -> None:
    configure_page()
    inject_global_styles()

    auth_message = init_auth_safely()
    progress_data = ensure_app_state()

    render_sidebar()
    render_shell_header(st.session_state.get("selected_mode", "Home"), auth_message)
    render_selected_mode(progress_data)


if __name__ == "__main__":
    main()