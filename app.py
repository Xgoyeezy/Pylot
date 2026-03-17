from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

import streamlit as st

import lessons
from core import (
    ai,
    code_arena,
    debug,
    explain,
    file_analyzer,
    memory,
    onboarding,
    practice,
    progress_hub,
    project,
    review,
    run_project,
    settings_page,
)
from core.engagement import (
    get_code_arena_preview,
    get_daily_quest,
    get_shock_feature_cards,
    get_skill_tree,
)
from core.ui import inject_ui_theme
from progress import (
    add_xp,
    get_learning_profile,
    has_passed_lesson_review,
    init_progress_db,
    is_lesson_complete,
    load_progress,
    mark_daily_quest_claimed,
    touch_daily_activity,
)

try:
    from core.auth import account_badge, auth_sidebar, init_auth
except ImportError:
    account_badge = None
    auth_sidebar = None
    init_auth = None


APP_TITLE = "Pylix — Learn Python by Building"
APP_ICON = "🐍"

MODE_RENDERERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "Home": lambda progress_data: render_home(progress_data),
    "Progress Hub": progress_hub.render,
    "Course Mode": lessons.render,
    "Practice Mode": practice.render,
    "Project Mode": project.render,
    "Run/Test Mode": run_project.render,
    "AI Mode": ai.render,
    "Debug Mode": debug.render,
    "Explain Mode": explain.render,
    "Review Mode": review.render,
    "File Analyzer Mode": file_analyzer.render,
    "Code Arena": code_arena.render,
    "Settings": settings_page.render,
    "Shared Memory Admin": memory.render,
}

MODE_OPTIONS: List[str] = [
    "Home",
    "Progress Hub",
    "Course Mode",
    "Practice Mode",
    "Project Mode",
    "Run/Test Mode",
    "AI Mode",
    "Debug Mode",
    "Explain Mode",
    "Review Mode",
    "File Analyzer Mode",
    "Code Arena",
    "Settings",
    "Shared Memory Admin",
]

MODE_ICONS: Dict[str, str] = {
    "Home": "🏠",
    "Progress Hub": "📈",
    "Course Mode": "📘",
    "Practice Mode": "🎯",
    "Project Mode": "🛠️",
    "Run/Test Mode": "▶️",
    "AI Mode": "🤖",
    "Debug Mode": "🐞",
    "Explain Mode": "🧠",
    "Review Mode": "✅",
    "File Analyzer Mode": "📂",
    "Code Arena": "⚔️",
    "Settings": "⚙️",
    "Shared Memory Admin": "🧠",
}


def configure_page() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_global_styles() -> None:
    inject_ui_theme()

    st.markdown(
        """
        <style>
        div[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28%),
                linear-gradient(180deg, #0F172A 0%, #111827 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }

        div[data-testid="stSidebar"] * {
            color: #E5EEF9;
        }

        div[data-testid="stSidebar"] .stMetric {
            background: rgba(255,255,255,0.05) !important;
            border-color: rgba(255,255,255,0.06) !important;
            box-shadow: none !important;
        }

        div[data-testid="stSidebar"] div[data-testid="stMetricLabel"] {
            color: rgba(226, 232, 240, 0.72) !important;
        }

        div[data-testid="stSidebar"] div[data-testid="stMetricValue"] {
            color: white !important;
        }

        .pylix-shell-card {
            position: relative;
            overflow: hidden;
            padding: 1.1rem 1.2rem;
            border-radius: 24px;
            background:
                radial-gradient(circle at top right, rgba(96, 165, 250, 0.14), transparent 26%),
                linear-gradient(180deg, rgba(255,255,255,0.88) 0%, rgba(255,255,255,0.78) 100%);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-bottom: 1rem;
            box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }

        .pylix-shell-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.32rem 0.68rem;
            border-radius: 999px;
            background: rgba(37, 99, 235, 0.10);
            border: 1px solid rgba(37, 99, 235, 0.12);
            color: #1D4ED8;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .pylix-home-highlight {
            border: 1px solid rgba(37, 99, 235, 0.16);
            border-radius: 22px;
            padding: 1rem 1.05rem;
            background:
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.10), transparent 28%),
                linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.96) 100%);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }

        .pylix-skill-node {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            padding: 0.9rem;
            background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
            margin-bottom: 0.7rem;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        }

        .pylix-badge-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 18px;
            padding: 0.9rem;
            background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
            margin-bottom: 0.7rem;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
        }

        .pylix-soft-text {
            color: #64748B;
        }

        .pylix-sidebar-section-title {
            color: rgba(255,255,255,0.94);
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_app_state() -> Dict[str, Any]:
    init_progress_db()
    touch_daily_activity()

    st.session_state.setdefault("selected_mode", "Home")
    st.session_state.setdefault("selected_lesson_id", None)
    st.session_state.setdefault("selected_project_id", None)
    st.session_state.setdefault("review_target_type", None)
    st.session_state.setdefault("review_target_id", None)
    st.session_state.setdefault("review_target_code", "")
    st.session_state.setdefault("arena_preview_claimed", False)

    progress_data = load_progress()
    st.session_state["progress_data"] = progress_data
    return progress_data


def init_auth_safely() -> str:
    if init_auth is None:
        return "Authentication module unavailable. Running in guest mode."

    try:
        init_auth()
        return ""
    except Exception:
        return "Authentication is not configured. Running in guest mode."


def render_auth_block() -> None:
    if auth_sidebar is not None:
        try:
            auth_sidebar()
            if account_badge is not None:
                account_badge()
            return
        except Exception:
            pass

    st.markdown('<div class="pylix-sidebar-section-title">Account</div>', unsafe_allow_html=True)
    st.info("Guest mode is active.")
    st.caption("Authentication is unavailable or not configured.")


def clear_detail_navigation() -> None:
    st.session_state["selected_lesson_id"] = None
    st.session_state["selected_project_id"] = None


def navigate_to(mode: str) -> None:
    clear_detail_navigation()
    st.session_state["selected_mode"] = mode
    st.rerun()


def claim_daily_quest() -> None:
    profile = get_learning_profile()
    if not profile.get("can_claim_daily_quest", False):
        st.warning("Daily quest already claimed today.")
        return

    quest = get_daily_quest()
    add_xp(int(quest["reward_xp"]))
    mark_daily_quest_claimed()
    st.success(f"Daily quest reward claimed: +{quest['reward_xp']} XP")
    st.rerun()


def claim_arena_preview_reward() -> None:
    if st.session_state.get("arena_preview_claimed", False):
        st.warning("Arena preview reward already claimed this session.")
        return

    add_xp(50)
    st.session_state["arena_preview_claimed"] = True
    st.success("Code Arena preview completed: +50 XP")
    st.rerun()


def _build_personalized_home_plan(
    profile: Dict[str, Any],
    personalization: Dict[str, str],
) -> Dict[str, Any]:
    style = personalization.get("learning_style", "builder")
    difficulty = personalization.get("difficulty", "balanced")
    session_goal = personalization.get("session_goal", "20")

    recommended_mode = profile.get("recommended_mode", "Course Mode")
    recommended_topic = profile.get("recommended_topic", "general")

    primary_mode = recommended_mode
    secondary_mode = "Practice Mode"
    headline = "Build momentum with your next best step."
    subtext = (
        f"Focus on {recommended_topic} and keep progressing through "
        f"{recommended_mode.lower()}."
    )

    if style == "builder":
        primary_mode = "Project Mode" if profile.get("completed_lessons", 0) >= 1 else "Course Mode"
        secondary_mode = "Run/Test Mode"
        headline = "Build something small, then improve it."
        subtext = "Project-first learning fits you best. Use lessons to support building, not replace it."
    elif style == "structured":
        primary_mode = "Course Mode"
        secondary_mode = "Practice Mode"
        headline = "Follow the path in order."
        subtext = "Structured learning fits you best. Clear the next lesson, then reinforce it with practice."
    elif style == "explainer":
        primary_mode = "AI Mode"
        secondary_mode = "Explain Mode"
        headline = "Understand first, then apply."
        subtext = "You learn best when concepts are clear. Use the tutor and explanation tools before pushing harder."
    elif style == "competitive":
        primary_mode = "Code Arena"
        secondary_mode = "Practice Mode"
        headline = "Turn learning into wins."
        subtext = "Challenge-driven learning fits you best. Use arena runs and short practice sprints to stay sharp."

    if difficulty == "easy":
        difficulty_text = "Keep this session light: one clear win is enough."
    elif difficulty == "hard":
        difficulty_text = "Push harder this session: aim for a cleaner, faster, more complete result."
    else:
        difficulty_text = "Use a balanced pace: one focused step, then one reinforcement step."

    if session_goal == "10":
        session_text = "Recommended session plan: one short action only."
    elif session_goal == "20":
        session_text = "Recommended session plan: one main task plus one quick follow-up."
    elif session_goal == "30":
        session_text = "Recommended session plan: one main task, one reinforcement task, and one review."
    else:
        session_text = "Recommended session plan: deep work block with build, refine, and review."

    actions: List[Tuple[str, str]] = [
        ("Open Primary Path", primary_mode),
        ("Open Secondary Path", secondary_mode),
        ("Open Progress Hub", "Progress Hub"),
        ("Open Settings", "Settings"),
    ]

    return {
        "headline": headline,
        "subtext": subtext,
        "difficulty_text": difficulty_text,
        "session_text": session_text,
        "actions": actions,
    }


def _mode_label(mode: str) -> str:
    return f"{MODE_ICONS.get(mode, '📘')} {mode}"


def render_sidebar() -> None:
    profile = get_learning_profile()
    personalization = settings_page.get_personalization_profile()
    current_mode = st.session_state.get("selected_mode", "Home")
    current_index = MODE_OPTIONS.index(current_mode) if current_mode in MODE_OPTIONS else 0

    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:0.2rem 0 0.9rem 0;">
                <div style="font-size:1.2rem; font-weight:800; color:white;">{APP_ICON} Pylix</div>
                <div style="color:rgba(226,232,240,0.72); font-size:0.92rem; margin-top:0.25rem;">
                    Learn Python through lessons, projects, and live challenge systems.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="pylix-sidebar-section-title">Navigation</div>', unsafe_allow_html=True)
        selected_mode = st.radio(
            "Choose a mode",
            options=MODE_OPTIONS,
            index=current_index,
            format_func=_mode_label,
            key="mode_selector",
            label_visibility="collapsed",
        )
        st.session_state["selected_mode"] = selected_mode

        st.markdown("---")
        st.markdown('<div class="pylix-sidebar-section-title">Learning Profile</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Lessons", profile.get("completed_lessons", 0))
        with col2:
            st.metric("Projects", profile.get("completed_projects", 0))

        col3, col4 = st.columns(2)
        with col3:
            st.metric("XP", profile.get("xp", 0))
        with col4:
            st.metric("Level", profile.get("level", 1))

        st.metric("🔥 Streak", profile.get("current_streak", 0))
        st.caption(f"XP to next level: {profile.get('xp_to_next_level', 0)}")

        st.markdown('<div class="pylix-sidebar-section-title">Arena</div>', unsafe_allow_html=True)
        col5, col6 = st.columns(2)
        with col5:
            st.metric("Rank", profile.get("arena_rank", "Bronze"))
        with col6:
            st.metric("Wins", profile.get("arena_wins", 0))

        st.metric("Arena Score", profile.get("arena_score", 0))
        st.caption(f"Best streak: {profile.get('best_arena_win_streak', 0)}")

        st.markdown('<div class="pylix-sidebar-section-title">Personalization</div>', unsafe_allow_html=True)
        st.caption(f"Style: {personalization.get('learning_style', 'builder').title()}")
        st.caption(f"Difficulty: {personalization.get('difficulty', 'balanced').title()}")
        st.caption(f"Session goal: {personalization.get('session_goal', '20')} min")

        if profile.get("can_claim_daily_arena_mission", False):
            st.success("Arena mission ready today")
        else:
            st.caption("Arena mission already claimed today")

        st.caption(f"Recommended mode: {profile.get('recommended_mode', 'Course Mode')}")
        st.caption(f"Focus topic: {profile.get('recommended_topic', 'general')}")

        if hasattr(onboarding, "render_progress_summary"):
            onboarding.render_progress_summary(profile)

        top_weak_topics = profile.get("top_weak_topics", [])
        if top_weak_topics:
            st.markdown('<div class="pylix-sidebar-section-title">Weak Topics</div>', unsafe_allow_html=True)
            for topic, score in top_weak_topics:
                st.write(f"- {topic} ({score})")
        else:
            st.caption("No major weak topics detected yet.")

        st.markdown("---")
        render_auth_block()

        st.markdown("---")
        if st.button("🏠 Return to Home", use_container_width=True, type="primary"):
            navigate_to("Home")


def render_shell_header(mode: str, auth_message: str) -> None:
    current_mode_icon = MODE_ICONS.get(mode, "📘")

    st.markdown(
        f"""
        <div class="pylix-shell-card">
            <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; flex-wrap:wrap;">
                <div>
                    <div class="pylix-shell-chip">Interactive Python Product</div>
                    <h2 style="margin:0.7rem 0 0 0; letter-spacing:-0.02em;">
                        {APP_ICON} {APP_TITLE}
                    </h2>
                    <p style="margin:0.42rem 0 0 0; color:#475569; line-height:1.65; max-width: 900px;">
                        Interactive Python learning with lessons, practice, projects, AI tutoring,
                        debugging tools, code review, progress tracking, and challenge systems.
                    </p>
                </div>
                <div style="min-width: 210px;">
                    <div style="font-size:0.84rem; color:#64748B; font-weight:700; text-transform:uppercase; letter-spacing:0.03em;">
                        Current mode
                    </div>
                    <div style="margin-top:0.32rem; font-size:1.05rem; font-weight:800; color:#0F172A;">
                        {current_mode_icon} {mode}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if auth_message:
        st.caption(auth_message)


def render_home_hero(profile: Dict[str, Any], plan: Dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="pylix-hero">
            <div style="display:flex; gap:0.45rem; flex-wrap:wrap; margin-bottom:0.75rem;">
                <span class="pylix-pill">Level {profile.get("level", 1)}</span>
                <span class="pylix-pill">🔥 {profile.get("current_streak", 0)} day streak</span>
                <span class="pylix-pill">⚔ {profile.get("arena_rank", "Bronze")}</span>
                <span class="pylix-pill">🏅 {profile.get("badge_count", 0)} badges</span>
            </div>
            <h2 style="margin:0; font-size:1.7rem; letter-spacing:-0.03em;">{plan["headline"]}</h2>
            <p style="margin:0.52rem 0 0 0; color:rgba(255,255,255,0.86); line-height:1.68; max-width:900px;">
                {plan["subtext"]}
            </p>
            <p style="margin:0.85rem 0 0 0; color:rgba(255,255,255,0.82); line-height:1.65;">
                Recommended next step: <strong>{profile.get("recommended_mode", "Course Mode")}</strong>
                &nbsp;•&nbsp;
                Focus topic: <strong>{profile.get("recommended_topic", "general")}</strong>
                &nbsp;•&nbsp;
                XP: <strong>{profile.get("xp", 0)}</strong>
            </p>
            <p style="margin:0.45rem 0 0 0; color:rgba(255,255,255,0.78); line-height:1.6;">
                {plan["difficulty_text"]} &nbsp;•&nbsp; {plan["session_text"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_metrics(profile: Dict[str, Any]) -> None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Completed Lessons", profile.get("completed_lessons", 0))
    with col2:
        st.metric("Completed Projects", profile.get("completed_projects", 0))
    with col3:
        st.metric("Review Passes", profile.get("review_passed_count", 0))
    with col4:
        st.metric("XP", profile.get("xp", 0))

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Level", profile.get("level", 1))
    with col6:
        st.metric("🔥 Current Streak", profile.get("current_streak", 0))
    with col7:
        st.metric("Arena Rank", profile.get("arena_rank", "Bronze"))
    with col8:
        st.metric("Badges", profile.get("badge_count", 0))


def render_daily_quest(profile: Dict[str, Any]) -> None:
    quest = get_daily_quest()

    st.markdown("### Daily Quest")
    st.markdown(
        f"""
        <div class="pylix-home-highlight">
            <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; flex-wrap:wrap;">
                <div>
                    <h4 style="margin:0;">{quest["title"]}</h4>
                    <p style="margin:0.45rem 0 0 0; color:#475569; line-height:1.6;">
                        {quest["description"]}
                    </p>
                    <p style="margin:0.6rem 0 0 0; color:#64748B;">
                        Best mode: <strong>{quest["mode"]}</strong> • Hint: {quest["hint"]}
                    </p>
                </div>
                <div style="padding:0.34rem 0.7rem; border-radius:999px; background:rgba(37,99,235,0.10); color:#1D4ED8; font-weight:800;">
                    +{quest["reward_xp"]} XP
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Quest Mode", use_container_width=True, type="primary"):
            navigate_to(quest["mode"])
    with col2:
        if st.button(
            "Claim Quest Reward",
            use_container_width=True,
            disabled=not profile.get("can_claim_daily_quest", False),
        ):
            claim_daily_quest()


def render_quick_start_actions(plan: Dict[str, Any]) -> None:
    st.markdown("### Personalized Quick Start")

    actions = plan.get("actions", [])
    columns = st.columns(len(actions))

    for index, (label, mode) in enumerate(actions):
        with columns[index]:
            if st.button(
                label,
                use_container_width=True,
                key=f"home_personalized_{mode}_{index}",
                type="primary" if index == 0 else "secondary",
            ):
                navigate_to(mode)


def render_focus_panel(profile: Dict[str, Any], plan: Dict[str, Any]) -> None:
    st.markdown("### Focus Areas")

    st.markdown(
        f"""
        <div class="pylix-home-highlight">
            <h4 style="margin:0;">Current Session Strategy</h4>
            <p class="pylix-soft-text" style="margin:0.45rem 0 0 0; line-height:1.6;">
                {plan["difficulty_text"]}
            </p>
            <p class="pylix-soft-text" style="margin:0.35rem 0 0 0; line-height:1.6;">
                {plan["session_text"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_weak_topics = profile.get("top_weak_topics", [])
    if not top_weak_topics:
        st.success("No major weak topics detected yet.")
        return

    for topic, score in top_weak_topics:
        st.markdown(
            f"""
            <div class="pylix-skill-node">
                <strong>{topic}</strong><br>
                <span class="pylix-soft-text">Weakness score: <strong>{score}</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_skill_tree_preview() -> None:
    st.markdown("### Skill Tree")

    for node in get_skill_tree():
        lesson_id = node["id"]

        if is_lesson_complete(lesson_id):
            status = "✅ Complete"
        elif has_passed_lesson_review(lesson_id):
            status = "🟢 Reviewed"
        else:
            status = "🟡 In Progress"

        unlock_text = ", ".join(node["unlocks"]) if node["unlocks"] else "Final node"

        st.markdown(
            f"""
            <div class="pylix-skill-node">
                <strong>{node["title"]}</strong> — {status}<br>
                <span class="pylix-soft-text">{node["description"]}</span><br>
                <span class="pylix-soft-text">Unlocks: {unlock_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_code_arena_preview() -> None:
    arena = get_code_arena_preview()

    st.markdown("### Code Arena Preview")
    st.markdown(
        f"""
        <div class="pylix-home-highlight">
            <h4 style="margin:0;">{arena["title"]}</h4>
            <p style="margin:0.48rem 0 0 0; color:#475569; line-height:1.6;">
                <strong>Challenge:</strong> {arena["challenge"]}
            </p>
            <p class="pylix-soft-text" style="margin:0.52rem 0 0 0;">
                Your goal: {arena["user_goal"]}
            </p>
            <p class="pylix-soft-text" style="margin:0.36rem 0 0 0;">
                AI opponent style: {arena["ai_style"]}
            </p>
            <p class="pylix-soft-text" style="margin:0.36rem 0 0 0;">
                Preview reward: {arena["reward"]} XP
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Code Arena", key="arena_open_mode", use_container_width=True, type="primary"):
            navigate_to("Code Arena")
    with col2:
        if st.button(
            "Claim Arena Preview Reward",
            key="arena_claim_preview",
            use_container_width=True,
            disabled=st.session_state.get("arena_preview_claimed", False),
        ):
            claim_arena_preview_reward()


def render_achievements_preview(profile: Dict[str, Any]) -> None:
    st.markdown("### Achievements Preview")

    badges = profile.get("badges", [])
    if not badges:
        st.info("No badges unlocked yet.")
        return

    preview_badges = badges[:4]
    for badge in preview_badges:
        st.markdown(
            f"""
            <div class="pylix-badge-card">
                <strong>{badge["icon"]} {badge["title"]}</strong><br>
                <span class="pylix-soft-text">{badge["description"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    remaining = max(0, len(badges) - len(preview_badges))
    if remaining > 0:
        st.caption(f"+ {remaining} more badge(s) in Progress Hub")


def render_shock_feature_preview() -> None:
    st.markdown("### Coming Soon")

    cards = get_shock_feature_cards()
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]

    for index, card in enumerate(cards):
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="pylix-skill-node" style="min-height:190px;">
                    <h4 style="margin:0;">{card["title"]}</h4>
                    <p style="margin:0.45rem 0 0 0; color:#475569; line-height:1.6;">
                        {card["body"]}
                    </p>
                    <p class="pylix-soft-text" style="margin:0.72rem 0 0 0; font-weight:700;">
                        {card["badge"]}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_mode_cards(personalization: Dict[str, str]) -> None:
    st.markdown("### Explore Modes")

    style = personalization.get("learning_style", "builder")

    mode_descriptions = [
        ("Progress Hub", "View level progress, streaks, weak topics, arena rank, and learning momentum in one place."),
        ("Course Mode", "Follow structured lessons and unlock the next skill."),
        ("Practice Mode", "Target weak topics with guided exercises."),
        ("Project Mode", "Build milestone-based Python projects."),
        ("Run/Test Mode", "Run Python code directly in the app."),
        ("AI Mode", "Ask questions and get interactive tutoring."),
        ("Debug Mode", "Paste broken code and get debugging help."),
        ("Explain Mode", "Understand code and concepts more deeply."),
        ("Review Mode", "Check whether lesson and project solutions pass."),
        ("File Analyzer Mode", "Inspect Python files for structure and issues."),
        ("Code Arena", "Solve timed coding challenges and compete for XP and rank."),
        ("Settings", "Personalize learning style, difficulty feel, session goal, and layout."),
        ("Shared Memory Admin", "Manage memory entries used by the AI tools."),
    ]

    if style == "competitive":
        mode_descriptions.sort(key=lambda item: 0 if item[0] == "Code Arena" else 1)
    elif style == "builder":
        mode_descriptions.sort(key=lambda item: 0 if item[0] == "Project Mode" else 1)
    elif style == "explainer":
        mode_descriptions.sort(key=lambda item: 0 if item[0] in {"AI Mode", "Explain Mode"} else 1)
    elif style == "structured":
        mode_descriptions.sort(key=lambda item: 0 if item[0] == "Course Mode" else 1)

    col1, col2 = st.columns(2)
    columns = [col1, col2]

    for index, (mode_name, description) in enumerate(mode_descriptions):
        with columns[index % 2]:
            mode_icon = MODE_ICONS.get(mode_name, "📘")
            st.markdown(
                f"""
                <div class="pylix-skill-node" style="min-height:188px;">
                    <h4 style="margin:0;">{mode_icon} {mode_name}</h4>
                    <p style="margin:0.42rem 0 0 0; color:#475569; line-height:1.6;">
                        {description}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Open {mode_name}",
                key=f"home_open_{mode_name}",
                use_container_width=True,
                type="primary" if index < 2 else "secondary",
            ):
                navigate_to(mode_name)


def render_home(progress_data: Dict[str, Any]) -> None:
    _ = progress_data
    profile = get_learning_profile()
    personalization = settings_page.get_personalization_profile()
    plan = _build_personalized_home_plan(profile, personalization)

    if hasattr(onboarding, "render_home_checklist"):
        onboarding.render_home_checklist(profile)

    render_home_hero(profile, plan)
    render_home_metrics(profile)
    render_daily_quest(profile)
    render_quick_start_actions(plan)

    top_left, top_right = st.columns([2, 1])
    with top_left:
        render_mode_cards(personalization)
    with top_right:
        render_focus_panel(profile, plan)

    middle_left, middle_right = st.columns([1, 1])
    with middle_left:
        render_skill_tree_preview()
    with middle_right:
        render_code_arena_preview()

    render_achievements_preview(profile)
    render_shock_feature_preview()


def render_selected_mode(progress_data: Dict[str, Any]) -> None:
    selected_mode = st.session_state.get("selected_mode", "Home")
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
