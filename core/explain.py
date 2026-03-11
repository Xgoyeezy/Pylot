from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.live_ai import get_live_ai_response
from core.ui import make_button, render_action_buttons, section_panel


EXPLAIN_WELCOME = (
    "Ask a Python concept question, paste code, or do both.\n\n"
    "Explain Mode will break down what the code does, how it works, and what each part means."
)


def ensure_explain_state() -> None:
    if "explain_code" not in st.session_state:
        st.session_state["explain_code"] = ""

    if "explain_question" not in st.session_state:
        st.session_state["explain_question"] = ""

    if "explain_result" not in st.session_state:
        st.session_state["explain_result"] = None


def build_explain_context(progress_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "completed_lessons": progress_data.get("completed_lessons", []),
        "completed_projects": progress_data.get("completed_projects", []),
        "review_passed": progress_data.get("review_passed", {}),
        "weak_topics": progress_data.get("weak_topics", {}),
    }


def explain_code_locally(code: str) -> str:
    if not code.strip():
        return "Paste some code first."

    lines = [line for line in code.splitlines() if line.strip()]
    output = ["Overall explanation:"]

    if any("def " in line for line in lines):
        output.append("- Your code defines one or more functions.")
    if any("for " in line for line in lines):
        output.append("- Your code uses a for loop to repeat actions.")
    if any("while " in line for line in lines):
        output.append("- Your code uses a while loop to keep running until a condition changes.")
    if any("if " in line for line in lines):
        output.append("- Your code uses conditional logic to choose between different paths.")
    if any("input(" in line for line in lines):
        output.append("- Your code gets input from the user.")
    if any("print(" in line for line in lines):
        output.append("- Your code prints output.")
    if any("[" in line and "]" in line for line in lines):
        output.append("- Your code appears to use a list.")
    if any("{" in line and "}" in line for line in lines):
        output.append("- Your code appears to use a dictionary.")

    output.append("\nLine-by-line notes:")
    for index, line in enumerate(lines[:12], start=1):
        stripped = line.strip()

        if stripped.startswith("def "):
            output.append(f"- Line {index}: defines a function.")
        elif stripped.startswith("for "):
            output.append(f"- Line {index}: starts a for loop.")
        elif stripped.startswith("while "):
            output.append(f"- Line {index}: starts a while loop.")
        elif stripped.startswith("if ") or stripped.startswith("elif ") or stripped.startswith("else"):
            output.append(f"- Line {index}: controls program flow with a condition.")
        elif stripped.startswith("print("):
            output.append(f"- Line {index}: prints output.")
        elif "=" in stripped and "==" not in stripped:
            output.append(f"- Line {index}: assigns a value to a variable.")
        else:
            output.append(f"- Line {index}: performs a step in the program.")

    return "\n".join(output)


def render_examples() -> None:
    with st.expander("Example explanation prompts", expanded=False):
        st.code(
            """def greet(name):
    return f"Hello, {name}!"

print(greet("Marcus"))""",
            language="python",
        )
        st.caption("Function example")

        st.code(
            """numbers = [1, 2, 3]
for number in numbers:
    print(number * 2)""",
            language="python",
        )
        st.caption("Loop example")


def run_explain_request(question: str, code: str, progress_data: Dict[str, Any]) -> None:
    if not question.strip() and not code.strip():
        st.warning("Add a question, some code, or both.")
        return

    try:
        lesson_context = build_explain_context(progress_data)

        system_prompt, built_user_prompt, reply = get_live_ai_response(
            role="tutor",
            question=question or "Explain this Python code clearly.",
            code=code,
            error_text="",
            lesson=lesson_context,
            weak_topics=progress_data.get("weak_topics", {}),
            model="gpt-4o-mini",
            use_shared_memory=True,
        )

        if not reply.strip() and code.strip():
            reply = explain_code_locally(code)

        st.session_state["explain_result"] = {
            "reply": reply,
            "system_prompt": system_prompt,
            "user_prompt": built_user_prompt,
        }
        st.rerun()

    except RuntimeError:
        fallback_reply = (
            explain_code_locally(code)
            if code.strip()
            else "AI explanation is not configured yet. Add an OpenAI API key to enable richer explanations."
        )

        st.session_state["explain_result"] = {
            "reply": fallback_reply,
            "system_prompt": "",
            "user_prompt": "",
        }
        st.rerun()

    except (ValueError, TypeError, AttributeError) as error:
        st.session_state["explain_result"] = {
            "reply": f"Explain Mode hit an error:\n\n`{error}`",
            "system_prompt": "",
            "user_prompt": "",
        }
        st.rerun()


def clear_explain_session() -> None:
    st.session_state["explain_code"] = ""
    st.session_state["explain_question"] = ""
    st.session_state["explain_result"] = None
    st.rerun()


def render(progress_data: Dict[str, Any]) -> None:
    ensure_explain_state()

    section_panel(
        title="Explain Mode",
        description="Ask about Python concepts or paste code to get a clearer explanation.",
        icon="🧠",
    )

    st.info(EXPLAIN_WELCOME)
    render_examples()

    question = st.text_area(
        "Concept question (optional)",
        value=st.session_state.get("explain_question", ""),
        height=120,
        key="explain_question_editor",
    )
    st.session_state["explain_question"] = question

    code = st.text_area(
        "Python code (optional)",
        value=st.session_state.get("explain_code", ""),
        height=260,
        key="explain_code_editor",
    )
    st.session_state["explain_code"] = code

    render_action_buttons(
        [
            make_button(
                label="Explain",
                key="explain_run_button",
                action=lambda: run_explain_request(question, code, progress_data),
            ),
            make_button(
                label="Clear Explain Session",
                key="explain_clear_button",
                action=clear_explain_session,
            ),
        ]
    )

    result = st.session_state.get("explain_result")
    if result:
        st.markdown("### Explanation")
        st.markdown(result["reply"])

        with st.expander("Explain Prompt Details", expanded=False):
            st.markdown("**System Prompt**")
            st.code(result.get("system_prompt", ""), language="text")
            st.markdown("**User Prompt**")
            st.code(result.get("user_prompt", ""), language="text")