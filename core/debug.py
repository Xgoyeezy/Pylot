from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from core.openai_client import get_openai_client
from core.ui import action_row, bullet_list, make_button, metric_row, mode_header


DEBUG_WELCOME = (
    "Paste broken Python code and, if possible, the error message or traceback.\n\n"
    "Debug Mode explains what is wrong, why it happened, and how to fix it."
)

BUG_EXAMPLES: Dict[str, Dict[str, str]] = {
    "IndexError Example": {
        "code": 'numbers = [1, 2, 3]\nprint(numbers[5])',
        "error": "IndexError: list index out of range",
    },
    "NameError Example": {
        "code": 'name = "Marc"\nprint(nam)',
        "error": "NameError: name 'nam' is not defined",
    },
    "SyntaxError Example": {
        "code": 'def greet(name)\n    print("Hello", name)',
        "error": "SyntaxError: expected ':'",
    },
    "ZeroDivisionError Example": {
        "code": "value = 10 / 0\nprint(value)",
        "error": "ZeroDivisionError: division by zero",
    },
}


SYSTEM_PROMPT = """
You are a Python debugging assistant inside Pylix.

Goals:
- identify the bug clearly
- explain why it happened
- show corrected code
- suggest how to avoid the issue next time

Rules:
- keep explanations practical
- prefer short step-by-step guidance
- include corrected code when useful
- assume the learner may be a beginner
""".strip()


def _init_state() -> None:
    defaults = {
        "debug_code": "",
        "debug_error_text": "",
        "debug_result": None,
        "debug_last_example": "None",
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _clear_session() -> None:
    st.session_state["debug_code"] = ""
    st.session_state["debug_error_text"] = ""
    st.session_state["debug_result"] = None
    st.session_state["debug_last_example"] = "None"
    st.rerun()


def _load_bug_example(example_name: str) -> None:
    example = BUG_EXAMPLES[example_name]
    st.session_state["debug_code"] = example["code"]
    st.session_state["debug_error_text"] = example["error"]
    st.session_state["debug_result"] = None
    st.session_state["debug_last_example"] = example_name
    st.rerun()


def _build_user_prompt(progress_data: Dict[str, Any]) -> str:
    completed_lessons = progress_data.get("completed_lessons", [])
    completed_projects = progress_data.get("completed_projects", [])
    weak_topics = progress_data.get("weak_topics", {})

    lesson_count = completed_lessons if isinstance(completed_lessons, int) else len(completed_lessons)
    project_count = completed_projects if isinstance(completed_projects, int) else len(completed_projects)

    code = st.session_state.get("debug_code", "")
    error_text = st.session_state.get("debug_error_text", "")

    weak_topics_text = ", ".join(f"{topic} ({score})" for topic, score in weak_topics.items())
    if not weak_topics_text:
        weak_topics_text = "none"

    return (
        f"Learner context:\n"
        f"- completed lessons: {lesson_count}\n"
        f"- completed projects: {project_count}\n"
        f"- weak topics: {weak_topics_text}\n\n"
        f"Broken code:\n```python\n{code}\n```\n\n"
        f"Error or traceback:\n{error_text or 'No error text provided.'}\n\n"
        f"Please explain the bug, the cause, the fix, and how to avoid it next time."
    )


def _run_debug(progress_data: Dict[str, Any]) -> None:
    code = st.session_state.get("debug_code", "")
    if not code.strip():
        st.warning("Paste some Python code first.")
        return

    client = get_openai_client()
    user_prompt = _build_user_prompt(progress_data)

    if client is None:
        st.session_state["debug_result"] = {
            "reply": (
                "Debug Mode is not configured yet.\n\n"
                "Make sure your OpenAI API key is set in `.streamlit/secrets.toml` "
                "or as an environment variable."
            ),
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt,
        }
        st.rerun()

    try:
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
        user_message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": user_prompt,
        }
        messages: List[ChatCompletionMessageParam] = [system_message, user_message]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=messages,
        )

        reply = response.choices[0].message.content or "No response returned."

        st.session_state["debug_result"] = {
            "reply": reply,
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt,
        }
        st.rerun()

    except Exception as error:
        st.session_state["debug_result"] = {
            "reply": f"Debug Mode hit an error:\n\n`{error}`",
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt,
        }
        st.rerun()


def _render_result() -> None:
    result = st.session_state.get("debug_result")
    if not result:
        return

    st.markdown("### Debugging Help")
    st.markdown(result["reply"])

    with st.expander("Debug Prompt Details", expanded=False):
        st.markdown("**System Prompt**")
        st.code(result.get("system_prompt", ""), language="text")
        st.markdown("**User Prompt**")
        st.code(result.get("user_prompt", ""), language="text")


def _render_guidance() -> None:
    st.markdown("### Debug Workflow")
    bullet_list(
        [
            "Paste the broken code exactly as it appears.",
            "Add the full traceback if you have it.",
            "Run the debugger to get an explanation and fix path.",
            "Use the explanation to rewrite the code yourself if possible.",
        ]
    )


def _render_error_triage() -> None:
    st.markdown("### Common Causes")
    bullet_list(
        [
            "NameError: a variable name is misspelled or missing.",
            "SyntaxError: punctuation, indentation, or structure is invalid.",
            "IndexError: you tried to access a list position that does not exist.",
            "TypeError: an operation used incompatible types.",
            "ZeroDivisionError: division by zero happened.",
        ]
    )


def _render_example_loader() -> None:
    st.markdown("### Quick Bug Examples")

    selected_example = st.selectbox(
        "Load a bug example",
        options=list(BUG_EXAMPLES.keys()),
        key="debug_example_select",
    )

    action_row(
        [
            make_button(
                label="Load Example",
                key="debug_load_example",
                action=lambda: _load_bug_example(selected_example),
            )
        ]
    )


def render(progress_data: Dict[str, Any]) -> None:
    _init_state()

    mode_header(
        "Debug Mode",
        "Paste broken Python code and get structured debugging help.",
        "🐞",
    )

    metric_row(
        [
            (
                "Completed Lessons",
                progress_data.get("completed_lessons", 0)
                if isinstance(progress_data.get("completed_lessons"), int)
                else len(progress_data.get("completed_lessons", [])),
            ),
            (
                "Completed Projects",
                progress_data.get("completed_projects", 0)
                if isinstance(progress_data.get("completed_projects"), int)
                else len(progress_data.get("completed_projects", [])),
            ),
            ("Weak Topics", len(progress_data.get("weak_topics", {}))),
            ("Last Example", st.session_state.get("debug_last_example", "None")),
        ]
    )

    st.info(DEBUG_WELCOME)

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.session_state["debug_code"] = st.text_area(
            "Broken Python Code",
            value=st.session_state.get("debug_code", ""),
            height=260,
            key="debug_code_editor",
        )

        st.session_state["debug_error_text"] = st.text_area(
            "Error Message or Traceback (optional but helpful)",
            value=st.session_state.get("debug_error_text", ""),
            height=160,
            key="debug_error_editor",
        )

        action_row(
            [
                make_button(
                    label="Debug This Code",
                    key="debug_run_button",
                    action=lambda: _run_debug(progress_data),
                ),
                make_button(
                    label="Clear Debug Session",
                    key="debug_clear_button",
                    action=_clear_session,
                ),
            ]
        )

        _render_result()

    with right_col:
        _render_guidance()
        _render_error_triage()
        _render_example_loader()
