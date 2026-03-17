from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from core.openai_client import get_openai_client
from core.settings_page import get_personalization_profile
from core.ui import action_row, bullet_list, make_button, metric_row, mode_header
from progress import get_learning_profile


SYSTEM_PROMPT = """
You are the AI mentor inside Pylix, a Python learning platform.

Your job:
- teach Python clearly and patiently
- prefer short, practical explanations first
- use examples often
- ask a guiding question when useful
- adapt to beginners unless the user clearly shows stronger skill
- when the user pastes code, explain what it does and improve it if needed
- when the user is stuck, give a hint before giving the full answer
- keep the student moving with momentum
- prioritize learning by building

Style:
- direct
- encouraging
- structured
- practical

Response rules:
- do not overwhelm the learner
- break answers into steps when useful
- prefer simple Python first
- when giving an exercise, do not immediately give the solution unless asked
""".strip()


def _init_state() -> None:
    st.session_state.setdefault("ai_chat_history", [])
    st.session_state.setdefault("ai_input_prefill", "")
    st.session_state.setdefault("ai_last_focus_topic", "general")


def _clear_chat() -> None:
    st.session_state["ai_chat_history"] = []
    st.session_state["ai_input_prefill"] = ""
    st.rerun()


def _set_prefill(text: str) -> None:
    st.session_state["ai_input_prefill"] = text
    st.rerun()


def _append_message(role: str, content: str) -> None:
    history: List[Dict[str, str]] = st.session_state["ai_chat_history"]
    history.append({"role": role, "content": content})
    st.session_state["ai_chat_history"] = history


def _learning_style_instructions(style: str) -> str:
    mapping = {
        "builder": "Favor project-like explanations, mini-builds, and practical next steps.",
        "structured": "Favor ordered teaching, numbered steps, and clear sequence.",
        "explainer": "Spend more time on why concepts work before moving into exercises.",
        "competitive": "Frame help like missions, tests, score improvements, and short wins.",
    }
    return mapping.get(style, mapping["builder"])


def _difficulty_instructions(difficulty: str) -> str:
    mapping = {
        "easy": "Use a gentle pace with more hints and simpler examples.",
        "balanced": "Use a balanced pace with guidance first and challenge second.",
        "hard": "Use a stronger challenge level and prefer hints over full solutions.",
    }
    return mapping.get(difficulty, mapping["balanced"])


def _session_goal_instructions(session_goal: str) -> str:
    mapping = {
        "10": "Keep help concise and action-oriented.",
        "20": "Keep answers focused but complete.",
        "30": "It is okay to include more structure and examples.",
        "45+": "It is okay to include more detailed multi-step guidance.",
    }
    return mapping.get(session_goal, mapping["20"])


def _build_system_context() -> str:
    profile = get_learning_profile()
    personalization = get_personalization_profile()

    context_lines = [
        SYSTEM_PROMPT,
        "",
        "Current learner profile:",
        f"- completed lessons: {profile.get('completed_lessons', 0)}",
        f"- completed projects: {profile.get('completed_projects', 0)}",
        f"- xp: {profile.get('xp', 0)}",
        f"- level: {profile.get('level', 1)}",
        f"- current streak: {profile.get('current_streak', 0)}",
        f"- recommended topic: {profile.get('recommended_topic', 'general')}",
        f"- recommended mode: {profile.get('recommended_mode', 'Course Mode')}",
        "",
        "Personalization instructions:",
        _learning_style_instructions(personalization.get("learning_style", "builder")),
        _difficulty_instructions(personalization.get("difficulty", "balanced")),
        _session_goal_instructions(personalization.get("session_goal", "20")),
    ]

    top_weak_topics = profile.get("top_weak_topics", [])
    if top_weak_topics:
        formatted = ", ".join(f"{topic} ({score})" for topic, score in top_weak_topics)
        context_lines.append(f"- weak topics: {formatted}")

    return "\n".join(context_lines)


def _build_messages() -> List[ChatCompletionMessageParam]:
    messages: List[ChatCompletionMessageParam] = []

    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": _build_system_context(),
    }
    messages.append(system_message)

    history: List[Dict[str, str]] = st.session_state["ai_chat_history"]
    for item in history:
        if item["role"] == "user":
            user_message: ChatCompletionUserMessageParam = {
                "role": "user",
                "content": item["content"],
            }
            messages.append(user_message)
        elif item["role"] == "assistant":
            assistant_message: ChatCompletionAssistantMessageParam = {
                "role": "assistant",
                "content": item["content"],
            }
            messages.append(assistant_message)

    return messages


def _generate_response() -> str:
    client = get_openai_client()
    if client is None:
        return "OpenAI API key is not configured."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=_build_messages(),
            temperature=0.5,
        )
        return response.choices[0].message.content or ""
    except Exception as error:
        return f"AI error: {error}"


def _send_message(text: str) -> None:
    if not text.strip():
        return

    _append_message("user", text)
    reply = _generate_response().strip()

    if not reply:
        reply = "I could not generate a response. Try asking in a more specific way."

    _append_message("assistant", reply)
    st.session_state["ai_input_prefill"] = ""
    st.rerun()


def _render_history() -> None:
    history: List[Dict[str, str]] = st.session_state["ai_chat_history"]
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def _render_primary_actions() -> None:
    st.markdown("### Guided Starts")
    action_row(
        [
            make_button(
                label="Explain a Concept",
                key="ai_quick_explain_concept",
                action=lambda: _set_prefill(
                    "Explain this Python concept simply, give 2 examples, then ask me 1 short check question."
                ),
            ),
            make_button(
                label="Debug My Code",
                key="ai_quick_debug_code",
                action=lambda: _set_prefill(
                    "Help me debug this Python code. First explain the issue, then show the fix, then explain how to avoid it next time.\n\n```python\n# paste code here\n```"
                ),
            ),
            make_button(
                label="Give Me Practice",
                key="ai_quick_practice",
                action=lambda: _set_prefill(
                    "Give me one short Python practice challenge for my level. Do not give the solution yet."
                ),
            ),
            make_button(
                label="Build a Project",
                key="ai_quick_project_path",
                action=lambda: _set_prefill(
                    "Give me a Python project idea for my level with step-by-step milestones, what I will learn, and starter code."
                ),
            ),
        ]
    )


def _render_secondary_actions() -> None:
    st.markdown("### Learning Paths")
    action_row(
        [
            make_button(
                label="Teach Me by Building",
                key="ai_quick_building_path",
                action=lambda: _set_prefill(
                    "Teach me Python by building something small. Pick a beginner-friendly app, break it into steps, and guide me through step 1."
                ),
            ),
            make_button(
                label="Quiz Me",
                key="ai_quick_quiz",
                action=lambda: _set_prefill(
                    "Quiz me on Python based on my current level. Ask one question at a time and wait for my answer."
                ),
            ),
            make_button(
                label="Review My Thinking",
                key="ai_quick_reasoning",
                action=lambda: _set_prefill(
                    "I will explain my Python thinking. Check whether my reasoning is correct and improve it."
                ),
            ),
            make_button(
                label="Clear Chat",
                key="ai_clear_chat",
                action=_clear_chat,
            ),
        ]
    )


def _render_coach_panel() -> None:
    profile = get_learning_profile()
    personalization = get_personalization_profile()

    st.markdown("### Mentor Dashboard")
    metric_row(
        [
            ("XP", profile.get("xp", 0)),
            ("Level", profile.get("level", 1)),
            ("Streak", profile.get("current_streak", 0)),
            ("Weak Topics", len(profile.get("weak_topics", {}))),
        ]
    )

    st.caption(
        f"Recommended next step: {profile.get('recommended_mode', 'Course Mode')} • "
        f"Focus topic: {profile.get('recommended_topic', 'general')}"
    )
    st.caption(
        f"Style: {personalization.get('learning_style', 'builder').title()} • "
        f"Difficulty: {personalization.get('difficulty', 'balanced').title()} • "
        f"Goal: {personalization.get('session_goal', '20')} min"
    )

    weak_topics = profile.get("top_weak_topics", [])
    if weak_topics:
        bullet_list([f"{topic} ({score})" for topic, score in weak_topics])
    else:
        st.caption("No major weak topics detected right now.")


def _render_prompt_starters() -> None:
    st.markdown("### Prompt Ideas")
    bullet_list(
        [
            "Explain loops like I am a beginner.",
            "Help me understand this function.",
            "Why does this error happen?",
            "Give me a project idea based on what I know.",
            "Quiz me without telling me the answer right away.",
            "Turn this code into cleaner Python.",
        ]
    )


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    _init_state()

    mode_header(
        "AI Tutor",
        "Work with an adaptive Python mentor that teaches, quizzes, explains, and helps you build.",
        "🤖",
    )

    _render_coach_panel()
    _render_primary_actions()
    _render_secondary_actions()
    _render_prompt_starters()
    _render_history()

    prefill = st.session_state.get("ai_input_prefill", "")
    if prefill:
        st.text_area(
            "Prepared Prompt",
            value=prefill,
            height=120,
            key="ai_prefill_preview",
            disabled=True,
        )
        action_row(
            [
                make_button(
                    label="Send Prepared Prompt",
                    key="ai_send_prefill",
                    action=lambda: _send_message(prefill),
                )
            ]
        )

    user_input = st.chat_input("Ask your AI mentor a Python question")
    if user_input:
        _send_message(user_input)
