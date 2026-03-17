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


EXPLAIN_WELCOME = (
    "Ask a Python concept question, paste code, or do both.\n\n"
    "Explain Mode breaks down what code does, how it works, and what each part means."
)

EXPLAIN_EXAMPLES: Dict[str, Dict[str, str]] = {
    "Function Example": {
        "question": "Explain how this function works step by step.",
        "code": """def greet(name):
    return f"Hello, {name}!"

print(greet("Marc"))""",
    },
    "Loop Example": {
        "question": "Explain what this loop does and why it works.",
        "code": """numbers = [1, 2, 3]
for number in numbers:
    print(number * 2)""",
    },
    "Conditional Example": {
        "question": "Explain this conditional and what output it produces.",
        "code": """number = 12

if number > 10:
    print("big")
else:
    print("small")""",
    },
    "List Example": {
        "question": "Explain how indexing works in this example.",
        "code": """scores = [90, 82, 100, 76]
print(scores[1])""",
    },
}


SYSTEM_PROMPT = """
You are a Python explanation assistant inside Pylix.

Goals:
- explain Python code clearly
- break concepts into simple steps
- focus on understanding, not just answers
- prefer beginner-friendly explanations

Rules:
- explain what the code does
- explain how it works step-by-step
- mention important Python concepts used
- use short examples if helpful
- if the user asks a question and provides code, answer both together
""".strip()


def _init_state() -> None:
    defaults = {
        "explain_code": "",
        "explain_question": "",
        "explain_result": None,
        "explain_last_example": "None",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _local_explanation(code: str) -> str:
    if not code.strip():
        return "Paste some code first."

    lines: List[str] = [line for line in code.splitlines() if line.strip()]
    notes: List[str] = ["## Overall explanation"]

    feature_map = [
        ("def ", "Your code defines one or more functions."),
        ("for ", "Your code uses a for loop to repeat actions."),
        ("while ", "Your code uses a while loop to repeat until a condition changes."),
        ("if ", "Your code uses conditional logic."),
        ("input(", "Your code reads input from the user."),
        ("print(", "Your code prints output."),
    ]

    for token, message in feature_map:
        if any(token in line for line in lines):
            notes.append(f"- {message}")

    if any("[" in line and "]" in line for line in lines):
        notes.append("- Your code appears to use a list.")
    if any("{" in line and "}" in line for line in lines):
        notes.append("- Your code appears to use a dictionary.")

    notes.append("\n## Line-by-line notes")
    for index, line in enumerate(lines[:12], start=1):
        stripped = line.strip()

        if stripped.startswith("def "):
            notes.append(f"- Line {index}: defines a function.")
        elif stripped.startswith("for "):
            notes.append(f"- Line {index}: starts a for loop.")
        elif stripped.startswith("while "):
            notes.append(f"- Line {index}: starts a while loop.")
        elif stripped.startswith(("if ", "elif ", "else")):
            notes.append(f"- Line {index}: controls program flow with a condition.")
        elif stripped.startswith("print("):
            notes.append(f"- Line {index}: prints output.")
        elif "=" in stripped and "==" not in stripped:
            notes.append(f"- Line {index}: assigns a value to a variable.")
        else:
            notes.append(f"- Line {index}: performs a program step.")

    notes.append("\n## Self-check")
    notes.append("- What value changes as the code runs?")
    notes.append("- What output should appear?")
    notes.append("- Which line controls the behavior most?")

    return "\n".join(notes)


def _save_result(reply: str, system_prompt: str = "", user_prompt: str = "") -> None:
    st.session_state["explain_result"] = {
        "reply": reply,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }
    st.rerun()


def _clear() -> None:
    st.session_state["explain_code"] = ""
    st.session_state["explain_question"] = ""
    st.session_state["explain_result"] = None
    st.session_state["explain_last_example"] = "None"
    st.rerun()


def _load_example(example_name: str) -> None:
    example = EXPLAIN_EXAMPLES[example_name]
    st.session_state["explain_question"] = example["question"]
    st.session_state["explain_code"] = example["code"]
    st.session_state["explain_result"] = None
    st.session_state["explain_last_example"] = example_name
    st.rerun()


def _build_default_question(question: str, code: str) -> str:
    if question.strip():
        return question

    if code.strip():
        return (
            "Explain this Python code clearly. "
            "Describe what it does, how it works, and what a beginner should notice."
        )

    return "Explain this Python topic clearly."


def _build_user_prompt(progress_data: Dict[str, Any]) -> str:
    question = st.session_state.get("explain_question", "")
    code = st.session_state.get("explain_code", "")

    completed_lessons = progress_data.get("completed_lessons", [])
    completed_projects = progress_data.get("completed_projects", [])
    weak_topics = progress_data.get("weak_topics", {})

    lesson_count = completed_lessons if isinstance(completed_lessons, int) else len(completed_lessons)
    project_count = completed_projects if isinstance(completed_projects, int) else len(completed_projects)

    weak_topics_text = ", ".join(f"{topic} ({score})" for topic, score in weak_topics.items())
    if not weak_topics_text:
        weak_topics_text = "none"

    return (
        f"Learner context:\n"
        f"- completed lessons: {lesson_count}\n"
        f"- completed projects: {project_count}\n"
        f"- weak topics: {weak_topics_text}\n\n"
        f"Question:\n{_build_default_question(question, code)}\n\n"
        f"Code:\n```python\n{code or '# no code provided'}\n```"
    )


def _request_explanation(progress_data: Dict[str, Any]) -> None:
    question = st.session_state.get("explain_question", "")
    code = st.session_state.get("explain_code", "")

    if not question.strip() and not code.strip():
        st.warning("Add a question, some code, or both.")
        return

    client = get_openai_client()
    user_prompt = _build_user_prompt(progress_data)

    if client is None:
        fallback = (
            _local_explanation(code)
            if code.strip()
            else "AI explanation is not configured yet. Add an OpenAI API key to enable richer explanations."
        )
        _save_result(fallback, SYSTEM_PROMPT, user_prompt)
        return

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

        reply = response.choices[0].message.content or ""
        final_reply = reply.strip() or _local_explanation(code)
        _save_result(final_reply, SYSTEM_PROMPT, user_prompt)

    except Exception as error:
        fallback = (
            _local_explanation(code)
            if code.strip()
            else f"Explain Mode hit an error:\n\n`{error}`"
        )
        _save_result(fallback, SYSTEM_PROMPT, user_prompt)


def _render_result() -> None:
    result = st.session_state.get("explain_result")
    if not result:
        return

    st.markdown("### Explanation")
    st.markdown(result["reply"])

    with st.expander("Explain Prompt Details", expanded=False):
        st.markdown("**System Prompt**")
        st.code(result.get("system_prompt", ""), language="text")
        st.markdown("**User Prompt**")
        st.code(result.get("user_prompt", ""), language="text")


def _render_guidance() -> None:
    st.markdown("### How to Use Explain Mode")
    bullet_list(
        [
            "Ask a concept question when you want understanding.",
            "Paste code when you want a walkthrough.",
            "Use both when you want a focused explanation of a specific snippet.",
            "Try answering the self-check questions after reading the explanation.",
        ]
    )


def _render_learning_paths() -> None:
    st.markdown("### Quick Explanation Paths")
    action_row(
        [
            make_button(
                label="Explain a Concept",
                key="explain_path_concept",
                action=lambda: st.session_state.update(
                    {"explain_question": "Explain Python loops simply with examples.", "explain_code": ""}
                ) or st.rerun(),
            ),
            make_button(
                label="Explain Code",
                key="explain_path_code",
                action=lambda: st.session_state.update(
                    {"explain_question": "Explain this code step by step.", "explain_code": "# paste code here"}
                ) or st.rerun(),
            ),
            make_button(
                label="Explain + Quiz Me",
                key="explain_path_quiz",
                action=lambda: st.session_state.update(
                    {"explain_question": "Explain this clearly, then ask me 2 short check questions.", "explain_code": ""}
                ) or st.rerun(),
            ),
        ]
    )


def _render_example_loader() -> None:
    st.markdown("### Quick Examples")

    selected_example = st.selectbox(
        "Load an explanation example",
        options=list(EXPLAIN_EXAMPLES.keys()),
        key="explain_example_select",
    )

    action_row(
        [
            make_button(
                label="Load Example",
                key="explain_load_example",
                action=lambda: _load_example(selected_example),
            )
        ]
    )


def render(progress_data: Dict[str, Any]) -> None:
    _init_state()

    mode_header(
        "Explain Mode",
        "Ask about Python concepts or paste code to get a clearer explanation.",
        "🧠",
    )

    completed_lessons = progress_data.get("completed_lessons", [])
    completed_projects = progress_data.get("completed_projects", [])

    metric_row(
        [
            ("Weak Topics", len(progress_data.get("weak_topics", {}))),
            ("Completed Lessons", completed_lessons if isinstance(completed_lessons, int) else len(completed_lessons)),
            ("Completed Projects", completed_projects if isinstance(completed_projects, int) else len(completed_projects)),
            ("Last Example", st.session_state.get("explain_last_example", "None")),
        ]
    )

    st.info(EXPLAIN_WELCOME)

    left_col, right_col = st.columns([2, 1])

    with left_col:
        _render_learning_paths()

        st.session_state["explain_question"] = st.text_area(
            "Concept Question (optional)",
            value=st.session_state.get("explain_question", ""),
            height=120,
            key="explain_question_editor",
        )

        st.session_state["explain_code"] = st.text_area(
            "Python Code (optional)",
            value=st.session_state.get("explain_code", ""),
            height=260,
            key="explain_code_editor",
        )

        action_row(
            [
                make_button(
                    label="Explain",
                    key="explain_run_button",
                    action=lambda: _request_explanation(progress_data),
                ),
                make_button(
                    label="Clear Explain Session",
                    key="explain_clear_button",
                    action=_clear,
                ),
            ]
        )

        _render_result()

    with right_col:
        _render_guidance()
        _render_example_loader()
