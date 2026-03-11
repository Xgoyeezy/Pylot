from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.live_ai import get_live_ai_response
from core.ui import make_button, render_action_buttons, section_panel


WELCOME_MESSAGE = (
    "Hey — I’m your Python tutor inside Pylot.\n\n"
    "Ask me anything about Python:\n"
    "- concepts\n"
    "- debugging\n"
    "- reviewing your code\n"
    "- building projects\n"
    "- preparing exercises\n\n"
    "You do not need to choose a topic first. Just type naturally."
)


def ensure_ai_state() -> None:
    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = [
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
            }
        ]

    if "ai_input_prefill" not in st.session_state:
        st.session_state["ai_input_prefill"] = ""

    if "ai_last_system_prompt" not in st.session_state:
        st.session_state["ai_last_system_prompt"] = ""

    if "ai_last_user_prompt" not in st.session_state:
        st.session_state["ai_last_user_prompt"] = ""


def reset_ai_chat() -> None:
    st.session_state["ai_chat_history"] = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
        }
    ]
    st.session_state["ai_input_prefill"] = ""
    st.session_state["ai_last_system_prompt"] = ""
    st.session_state["ai_last_user_prompt"] = ""


def add_chat_message(role: str, content: str) -> None:
    st.session_state["ai_chat_history"].append(
        {
            "role": role,
            "content": content,
        }
    )


def detect_role_from_prompt(prompt: str) -> str:
    lowered = prompt.lower()

    debug_keywords = [
        "error",
        "traceback",
        "bug",
        "fix this",
        "why does this fail",
        "debug",
        "exception",
    ]

    review_keywords = [
        "review my code",
        "code review",
        "is this good",
        "improve this code",
        "make this more pythonic",
        "refactor",
    ]

    if any(keyword in lowered for keyword in debug_keywords):
        return "debugger"

    if any(keyword in lowered for keyword in review_keywords):
        return "reviewer"

    return "tutor"


def set_ai_prefill(value: str) -> None:
    st.session_state["ai_input_prefill"] = value
    st.rerun()


def render_quick_actions() -> None:
    st.markdown("### Quick Starts")

    render_action_buttons(
        [
            make_button(
                label="Explain loops",
                key="ai_quick_explain_loops",
                action=lambda: set_ai_prefill("Explain Python loops simply with examples."),
            ),
            make_button(
                label="Debug code",
                key="ai_quick_debug_code",
                action=lambda: set_ai_prefill(
                    "Help me debug this Python code:\n\n```python\n# paste code here\n```"
                ),
            ),
            make_button(
                label="Practice exercise",
                key="ai_quick_practice_exercise",
                action=lambda: set_ai_prefill(
                    "Give me a Python practice exercise at my level, but do not show the solution yet."
                ),
            ),
            make_button(
                label="Project idea",
                key="ai_quick_project_idea",
                action=lambda: set_ai_prefill(
                    "Give me a beginner-friendly Python project idea and a step-by-step build plan."
                ),
            ),
        ]
    )


def render_chat_history() -> None:
    for message in st.session_state["ai_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def build_context_payload(progress_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "completed_lessons": progress_data.get("completed_lessons", []),
        "completed_projects": progress_data.get("completed_projects", []),
        "review_passed": progress_data.get("review_passed", {}),
        "weak_topics": progress_data.get("weak_topics", {}),
    }


def render_debug_panel() -> None:
    with st.expander("AI Debug Panel", expanded=False):
        st.caption("Useful while wiring prompts and memory.")
        st.markdown("**Last System Prompt**")
        st.code(st.session_state.get("ai_last_system_prompt", ""), language="text")

        st.markdown("**Last User Prompt**")
        st.code(st.session_state.get("ai_last_user_prompt", ""), language="text")


def send_ai_prompt(user_prompt: str, progress_data: Dict[str, Any]) -> None:
    add_chat_message("user", user_prompt)

    role = detect_role_from_prompt(user_prompt)
    lesson_context = build_context_payload(progress_data)

    try:
        system_prompt, built_user_prompt, reply = get_live_ai_response(
            role=role,
            question=user_prompt,
            code="",
            error_text="",
            lesson=lesson_context,
            weak_topics=progress_data.get("weak_topics", {}),
            model="gpt-4o-mini",
            use_shared_memory=True,
        )

        st.session_state["ai_last_system_prompt"] = system_prompt
        st.session_state["ai_last_user_prompt"] = built_user_prompt

        if not reply.strip():
            reply = (
                "I did not get a complete response back. Try asking again, "
                "or make the question a little more specific."
            )

    except RuntimeError as error:
        reply = (
            "AI Mode is not configured yet.\n\n"
            f"Details: `{error}`\n\n"
            "Make sure your OpenAI API key is set in `.streamlit/secrets.toml` "
            "or as an environment variable."
        )

    except (ValueError, TypeError, AttributeError) as error:
        reply = f"AI Mode hit an error:\n\n`{error}`"

    add_chat_message("assistant", reply)
    st.session_state["ai_input_prefill"] = ""
    st.rerun()


def render(progress_data: Dict[str, Any]) -> None:
    ensure_ai_state()

    section_panel(
        title="AI Tutor",
        description=(
            "Chat naturally about Python. Ask questions, paste code, debug errors, "
            "get explanations, or request practice."
        ),
        icon="🤖",
    )

    top_left, top_right = st.columns([5, 1])

    with top_left:
        render_quick_actions()

    with top_right:
        st.markdown("### ")
        render_action_buttons(
            [
                make_button(
                    label="Clear Chat",
                    key="ai_clear_chat",
                    action=reset_ai_chat,
                )
            ]
        )

    render_chat_history()

    prefill = st.session_state.get("ai_input_prefill", "")
    if prefill:
        st.text_area(
            "Prepared prompt",
            value=prefill,
            height=120,
            key="ai_prefill_preview",
            disabled=True,
        )

        render_action_buttons(
            [
                make_button(
                    label="Send Prepared Prompt",
                    key="ai_send_prefill",
                    action=lambda: send_ai_prompt(prefill, progress_data),
                )
            ]
        )

    user_prompt = st.chat_input("Ask anything about Python...")

    if user_prompt:
        send_ai_prompt(user_prompt, progress_data)

    render_debug_panel()