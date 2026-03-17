from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.engagement import get_career_paths, get_daily_quest, get_skill_tree
from core.ui import bullet_list, content_card, metric_row, mode_header
from progress import get_learning_profile, has_passed_lesson_review, is_lesson_complete


def _xp_progress_ratio(profile: Dict[str, Any]) -> float:
    xp_to_next = max(1, int(profile.get("xp_to_next_level", 1)))
    current_xp = int(profile.get("xp", 0))

    thresholds = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500]
    current_level_floor = 0

    for threshold in thresholds:
        if current_xp >= threshold:
            current_level_floor = threshold
        else:
            break

    gained_this_level = current_xp - current_level_floor
    level_span = gained_this_level + xp_to_next
    if level_span <= 0:
        return 0.0

    return max(0.0, min(1.0, gained_this_level / level_span))


def _arena_rank_progress(profile: Dict[str, Any]) -> float:
    arena_score = int(profile.get("arena_score", 0))

    if arena_score >= 300:
        overflow = min(100, arena_score - 300)
        return min(1.0, overflow / 100)
    if arena_score >= 180:
        return (arena_score - 180) / 120
    if arena_score >= 80:
        return (arena_score - 80) / 100
    return arena_score / 80 if arena_score > 0 else 0.0


def _render_level_panel(profile: Dict[str, Any]) -> None:
    st.markdown("### Level Progress")

    metric_row(
        [
            ("XP", profile.get("xp", 0)),
            ("Level", profile.get("level", 1)),
            ("XP to Next", profile.get("xp_to_next_level", 0)),
            ("🔥 Streak", profile.get("current_streak", 0)),
        ]
    )

    progress_ratio = _xp_progress_ratio(profile)
    st.progress(progress_ratio)
    st.caption(f"Current progress toward next level: {int(progress_ratio * 100)}%")


def _render_arena_panel(profile: Dict[str, Any]) -> None:
    st.markdown("### Arena Progress")

    metric_row(
        [
            ("Arena Rank", profile.get("arena_rank", "Bronze")),
            ("Arena Score", profile.get("arena_score", 0)),
            ("Arena Wins", profile.get("arena_wins", 0)),
            ("Arena Streak", profile.get("arena_win_streak", 0)),
        ]
    )

    progress_ratio = _arena_rank_progress(profile)
    st.progress(progress_ratio)
    st.caption(
        f"Best arena streak: {profile.get('best_arena_win_streak', 0)} • "
        f"Rank progress: {int(progress_ratio * 100)}%"
    )

    bullet_list(
        [
            "Bronze: 0+",
            "Silver: 80+",
            "Gold: 180+",
            "Python Slayer: 300+",
        ]
    )


def _render_badges(profile: Dict[str, Any]) -> None:
    st.markdown("### Achievements")

    badges = profile.get("badges", [])
    if not badges:
        st.info("No badges unlocked yet.")
        return

    st.caption(f"Badges unlocked: {profile.get('badge_count', 0)}")

    for badge in badges:
        content_card(
            title=f'{badge["icon"]} {badge["title"]}',
            body=badge["description"],
            badge="Unlocked",
            min_height=120,
        )


def _render_completion_panel(profile: Dict[str, Any]) -> None:
    st.markdown("### Learning Completion")

    metric_row(
        [
            ("Lessons Done", profile.get("completed_lessons", 0)),
            ("Projects Done", profile.get("completed_projects", 0)),
            ("Review Passes", profile.get("review_passed_count", 0)),
            ("Weak Topics", len(profile.get("weak_topics", {}))),
        ]
    )

    st.caption(
        f"Recommended next step: {profile.get('recommended_mode', 'Course Mode')} • "
        f"Focus topic: {profile.get('recommended_topic', 'general')}"
    )


def _render_weak_topics(profile: Dict[str, Any]) -> None:
    st.markdown("### Weak Topic Tracker")

    top_weak_topics = profile.get("top_weak_topics", [])
    if not top_weak_topics:
        st.success("No major weak topics detected right now.")
        return

    for topic, score in top_weak_topics:
        content_card(
            title=topic,
            body=f"Weakness score: {score}",
            badge="Focus",
            min_height=120,
        )


def _render_skill_tree_status() -> None:
    st.markdown("### Skill Tree Status")

    for node in get_skill_tree():
        lesson_id = node["id"]

        if is_lesson_complete(lesson_id):
            status = "✅ Complete"
        elif has_passed_lesson_review(lesson_id):
            status = "🟢 Reviewed"
        else:
            status = "🟡 In Progress"

        unlock_text = ", ".join(node["unlocks"]) if node["unlocks"] else "Final node"

        content_card(
            title=f'{node["title"]} — {status}',
            body=node["description"],
            meta=f'Track: {node["track"]}<br>Unlocks: {unlock_text}',
            badge="Skill",
            min_height=150,
        )


def _render_daily_focus(profile: Dict[str, Any]) -> None:
    st.markdown("### Daily Focus")

    quest = get_daily_quest()
    content_card(
        title=quest["title"],
        body=quest["description"],
        meta=f'Best mode: {quest["mode"]}<br>Hint: {quest["hint"]}',
        badge=f'+{quest["reward_xp"]} XP',
        min_height=150,
    )

    bullet_list(
        [
            f"Main topic to focus on: {profile.get('recommended_topic', 'general')}",
            f"Best mode to open next: {profile.get('recommended_mode', 'Course Mode')}",
            "Try to maintain your streak by completing one meaningful action today.",
        ]
    )


def _render_daily_arena_mission(profile: Dict[str, Any]) -> None:
    st.markdown("### Daily Arena Mission")

    if bool(profile.get("can_claim_daily_arena_mission", False)):
        st.success("Arena mission reward is available today.")
    else:
        st.info("Arena mission reward already claimed today.")

    bullet_list(
        [
            "Open Code Arena and clear one challenge.",
            "Try to beat the AI benchmark time.",
            f"Current arena streak: {profile.get('arena_win_streak', 0)}",
            f"Best arena streak: {profile.get('best_arena_win_streak', 0)}",
        ]
    )


def _render_career_paths() -> None:
    st.markdown("### Career Paths")

    for path in get_career_paths():
        focus = ", ".join(path["focus"])
        content_card(
            title=path["title"],
            body=path["description"],
            meta=f"Focus: {focus}",
            badge="Path",
            min_height=150,
        )


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data
    profile = get_learning_profile()

    mode_header(
        "Progress Hub",
        "Track your level, arena rank, streaks, badges, lesson flow, weak topics, and daily momentum in one place.",
        "📈",
    )

    _render_level_panel(profile)
    _render_arena_panel(profile)

    left_col, right_col = st.columns([2, 1])
    with left_col:
        _render_completion_panel(profile)
        _render_skill_tree_status()
        _render_badges(profile)
        _render_career_paths()
    with right_col:
        _render_daily_focus(profile)
        _render_daily_arena_mission(profile)
        _render_weak_topics(profile)
