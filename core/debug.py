from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.live_ai import get_live_ai_response
from core.ui import make_button, render_action_buttons, section_panel


DEBUG_WELCOME = (
    "Paste broken Python code and, if you have it, the error message or traceback.\n\n"
    "Debug Mode will help explain what is wrong, why it is happening, and how to fix it."
)


def ensure_debug_state() -> None:
    if "debug_code" not in st.session_state:
        st.session_state["debug_code"] = ""

    if "debug_error_text" not in st.session_state:
        st.session_state["debug_error_text"] = ""

    if "debug_result" not in st.session_state:
        st.session_state["debug_result"] = None


def build_debug_context(progress_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "completed_lessons": progress_data.get("completed_lessons", []),
        "completed_projects": progress_data.get("completed_projects", []),
        "review_passed": progress_data.get("review_passed", {}),
        "weak_topics": progress_data.get("weak_topics", {}),
    }


def render_examples() -> None:
    with st.expander("Example debugging prompts", expanded=False):
        st.code(
            """numbers = [1, 2, 3]
print(numbers[5])""",
            language="python",
        )
        st.caption("Typical result: IndexError")

        st.code(
            """name = "Marcus"
print(nam)""",
            language="python",
        )
        st.caption("Typical result: NameError")

        st.code(
            """def greet(name)
    print("Hello", name)""",
            language="python",
        )
        st.caption("Typical result: SyntaxError")


def run_debug_request(code: str, error_text: str, progress_data: Dict[str, Any]) -> None:
    if not code.strip():
        st.warning("Paste some Python code first.")
        return

    try:
        lesson_context = build_debug_context(progress_data)

        system_prompt, built_user_prompt, reply = get_live_ai_response(
            role="debugger",
            question="Help me debug this Python code.",
            code=code,
            error_text=error_text,
            lesson=lesson_context,
            weak_topics=progress_data.get("weak_topics", {}),
            model="gpt-4o-mini",
            use_shared_memory=True,
        )

        st.session_state["debug_result"] = {
            "reply": reply,
            "system_prompt": system_prompt,
            "user_prompt": built_user_prompt,
        }
        st.rerun()

    except RuntimeError as error:
        st.session_state["debug_result"] = {
            "reply": (
                "Debug Mode is not configured yet.\n\n"
                f"Details: `{error}`\n\n"
                "Make sure your OpenAI API key is set in `.streamlit/secrets.toml` "
                "or as an environment variable."
            ),
            "system_prompt": "",
            "user_prompt": "",
        }
        st.rerun()

    except (ValueError, TypeError, AttributeError) as error:
        st.session_state["debug_result"] = {
            "reply": f"Debug Mode hit an error:\n\n`{error}`",
            "system_prompt": "",
            "user_prompt": "",
        }
        st.rerun()


def clear_debug_session() -> None:
    st.session_state["debug_code"] = ""
    st.session_state["debug_error_text"] = ""
    st.session_state["debug_result"] = None
    st.rerun()


def render(progress_data: Dict[str, Any]) -> None:
    ensure_debug_state()

    section_panel(
        title="Debug Mode",
        description="Paste broken Python code and get structured debugging help.",
        icon="🐞",
    )

    st.info(DEBUG_WELCOME)
    render_examples()

    code = st.text_area(
        "Broken Python code",
        value=st.session_state.get("debug_code", ""),
        height=260,
        key="debug_code_editor",
    )
    st.session_state["debug_code"] = code

    error_text = st.text_area(
        "Error message or traceback (optional but helpful)",
        value=st.session_state.get("debug_error_text", ""),
        height=160,
        key="debug_error_editor",
    )
    st.session_state["debug_error_text"] = error_text

    render_action_buttons(
        [
            make_button(
                label="Debug This Code",
                key="debug_run_button",
                action=lambda: run_debug_request(code, error_text, progress_data),
            ),
            make_button(
                label="Clear Debug Session",
                key="debug_clear_button",
                action=clear_debug_session,
            ),
        ]
    )

    result = st.session_state.get("debug_result")
    if result:
        st.markdown("### Debugging Help")
        st.markdown(result["reply"])

        with st.expander("Debug Prompt Details", expanded=False):
            st.markdown("**System Prompt**")
            st.code(result.get("system_prompt", ""), language="text")
            st.markdown("**User Prompt**")
            st.code(result.get("user_prompt", ""), language="text")