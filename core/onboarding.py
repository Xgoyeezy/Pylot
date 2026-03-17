from __future__ import annotations

from typing import Any, Dict, List, TypedDict

import streamlit as st

from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header


class OnboardingStep(TypedDict):
    id: str
    title: str
    description: str
    target_mode: str


ONBOARDING_STEPS: List[OnboardingStep] = [
    {
        "id": "open_course",
        "title": "Open Course Mode",
        "description": "Start with the structured lesson path.",
        "target_mode": "Course Mode",
    },
    {
        "id": "complete_first_lesson",
        "title": "Complete Your First Lesson",
        "description": "Finish one lesson to begin your Python journey.",
        "target_mode": "Course Mode",
    },
    {
        "id": "try_practice",
        "title": "Try Practice Mode",
        "description": "Strengthen a topic with a guided exercise.",
        "target_mode": "Practice Mode",
    },
    {
        "id": "open_ai",
        "title": "Meet the AI Tutor",
        "description": "Ask a Python question and get guided help.",
        "target_mode": "AI Mode",
    },
    {
        "id": "open_code_arena",
        "title": "Enter Code Arena",
        "description": "Try one competitive coding challenge.",
        "target_mode": "Code Arena",
    },
]


def _init_state() -> None:
    st.session_state.setdefault("onboarding_dismissed", False)
    st.session_state.setdefault("onboarding_completed_steps", [])


def _completed_step_ids() -> List[str]:
    stored = st.session_state.get("onboarding_completed_steps", [])
    return [str(step_id) for step_id in stored]


def _mark_step_complete(step_id: str) -> None:
    current = _completed_step_ids()
    if step_id not in current:
        current.append(step_id)
        st.session_state["onboarding_completed_steps"] = current


def _dismiss() -> None:
    st.session_state["onboarding_dismissed"] = True
    st.rerun()


def _reset() -> None:
    st.session_state["onboarding_dismissed"] = False
    st.session_state["onboarding_completed_steps"] = []
    st.rerun()


def _navigate_to(mode: str) -> None:
    st.session_state["selected_mode"] = mode
    st.rerun()


def _sync_with_profile(profile: Dict[str, Any]) -> None:
    completed_lessons = int(profile.get("completed_lessons", 0))
    badge_count = int(profile.get("badge_count", 0))
    arena_wins = int(profile.get("arena_wins", 0))

    if st.session_state.get("selected_mode") == "Course Mode":
        _mark_step_complete("open_course")

    if completed_lessons >= 1:
        _mark_step_complete("complete_first_lesson")

    if st.session_state.get("selected_mode") == "Practice Mode":
        _mark_step_complete("try_practice")

    if st.session_state.get("selected_mode") == "AI Mode":
        _mark_step_complete("open_ai")

    if st.session_state.get("selected_mode") == "Code Arena" or arena_wins >= 1:
        _mark_step_complete("open_code_arena")

    if badge_count >= 1 and completed_lessons >= 1:
        _mark_step_complete("open_course")


def is_onboarding_complete() -> bool:
    return len(_completed_step_ids()) >= len(ONBOARDING_STEPS)


def should_show_onboarding(profile: Dict[str, Any]) -> bool:
    _init_state()
    _sync_with_profile(profile)

    if st.session_state.get("onboarding_dismissed", False):
        return False

    if is_onboarding_complete():
        return False

    if int(profile.get("completed_lessons", 0)) >= 2 and int(profile.get("arena_wins", 0)) >= 1:
        return False

    return True


def _progress_ratio() -> float:
    total = max(1, len(ONBOARDING_STEPS))
    completed = len(_completed_step_ids())
    return min(1.0, completed / total)


def _next_step() -> OnboardingStep | None:
    completed = set(_completed_step_ids())
    for step in ONBOARDING_STEPS:
        if step["id"] not in completed:
            return step
    return None


def _render_step(step: OnboardingStep) -> None:
    completed = step["id"] in _completed_step_ids()
    status = "✅ Complete" if completed else "🟡 To do"

    content_card(
        title=f'{step["title"]} — {status}',
        body=step["description"],
        meta=f'Target mode: {step["target_mode"]}',
        badge="Start" if not completed else "Done",
        min_height=145,
    )

    if not completed:
        action_row(
            [
                make_button(
                    label=f'Open {step["target_mode"]}',
                    key=f'onboarding_open_{step["id"]}',
                    action=lambda mode=step["target_mode"]: _navigate_to(mode),
                )
            ]
        )


def render_home_checklist(profile: Dict[str, Any]) -> None:
    _init_state()
    _sync_with_profile(profile)

    if not should_show_onboarding(profile):
        return

    next_step = _next_step()

    mode_header(
        "Welcome to Pylix",
        "Start with this quick checklist to learn the platform and build momentum fast.",
        "🚀",
    )

    metric_row(
        [
            ("Checklist Done", f'{len(_completed_step_ids())}/{len(ONBOARDING_STEPS)}'),
            ("Badges", profile.get("badge_count", 0)),
            ("Level", profile.get("level", 1)),
            ("Arena Wins", profile.get("arena_wins", 0)),
        ]
    )

    st.progress(_progress_ratio())
    st.caption(f"Onboarding progress: {int(_progress_ratio() * 100)}%")

    if next_step is not None:
        st.info(f'Next best step: {next_step["title"]} in {next_step["target_mode"]}')

    bullet_list(
        [
            "Start with one lesson",
            "Try one practice exercise",
            "Ask the AI tutor one question",
            "Test yourself in Code Arena",
        ]
    )

    for step in ONBOARDING_STEPS:
        _render_step(step)

    action_row(
        [
            make_button(
                label="Dismiss Checklist",
                key="onboarding_dismiss",
                action=_dismiss,
            ),
            make_button(
                label="Reset Checklist",
                key="onboarding_reset",
                action=_reset,
            ),
        ]
    )


def render_progress_summary(profile: Dict[str, Any]) -> None:
    _init_state()
    _sync_with_profile(profile)

    st.markdown("### Welcome Checklist")
    completed = len(_completed_step_ids())
    total = len(ONBOARDING_STEPS)

    metric_row(
        [
            ("Completed", f"{completed}/{total}"),
            ("Progress", f"{int(_progress_ratio() * 100)}%"),
        ]
    )

    next_step = _next_step()

    if is_onboarding_complete():
        st.success("Welcome checklist completed.")
    elif st.session_state.get("onboarding_dismissed", False):
        st.info("Welcome checklist dismissed.")
    else:
        remaining = total - completed
        st.caption(f"{remaining} onboarding step(s) remaining.")
        if next_step is not None:
            st.caption(f'Next: {next_step["title"]}')


def render(progress_data: Dict[str, Any]) -> None:
    profile = progress_data

    mode_header(
        "Onboarding",
        "Get familiar with Pylix, complete the starter path, and unlock momentum quickly.",
        "🧭",
    )

    render_home_checklist(profile)

    st.markdown("### Why this matters")
    bullet_list(
        [
            "Lessons give you structure",
            "Practice strengthens weak topics",
            "AI Mode helps when you get stuck",
            "Code Arena builds speed and confidence",
        ]
    )
