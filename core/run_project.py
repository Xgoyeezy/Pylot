from __future__ import annotations

import io
import traceback
from contextlib import redirect_stdout
from typing import Any, Dict

import streamlit as st

from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header
from progress import add_xp


RUNNER_TITLE = "Run / Test Mode"
RUNNER_DESCRIPTION = "Run Python code, test ideas quickly, and practice with built-in templates."


EXAMPLE_SNIPPETS: Dict[str, str] = {
    "Loop Example": (
        "numbers = [1, 2, 3, 4]\n\n"
        "for item in numbers:\n"
        "    print(item * 2)"
    ),
    "Function Example": (
        "def greet(name):\n"
        "    return f\"Hello, {name}!\"\n\n"
        "print(greet(\"Marc\"))"
    ),
    "List Example": (
        "scores = [90, 82, 100, 76]\n"
        "print(scores[1])\n"
        "print(max(scores))"
    ),
}

CHALLENGE_SNIPPETS: Dict[str, str] = {
    "Reverse Text": (
        "def reverse_text(text):\n"
        "    # return the reversed string\n"
        "    pass\n\n"
        'print(reverse_text("pylix"))'
    ),
    "Largest Number": (
        "def largest_number(numbers):\n"
        "    # return the largest number in the list\n"
        "    pass\n\n"
        "print(largest_number([3, 8, 1, 12, 5]))"
    ),
    "Even Counter": (
        "def count_evens(numbers):\n"
        "    # return how many even numbers are in the list\n"
        "    pass\n\n"
        "print(count_evens([1, 2, 3, 4, 5, 6]))"
    ),
}


def _blank_result() -> Dict[str, Any]:
    return {
        "success": False,
        "output": "",
        "error": "",
    }


def _init_state() -> None:
    defaults = {
        "run_test_code": "",
        "run_test_result": None,
        "run_test_runs": 0,
        "run_test_last_template": "None",
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _safe_exec(code: str) -> Dict[str, Any]:
    if not code.strip():
        return {
            "success": False,
            "output": "",
            "error": "No code to run.",
        }

    stdout_capture = io.StringIO()

    try:
        with redirect_stdout(stdout_capture):
            namespace: Dict[str, Any] = {"__name__": "__main__"}
            exec(code, namespace)

        return {
            "success": True,
            "output": stdout_capture.getvalue(),
            "error": "",
        }

    except (
        SyntaxError,
        NameError,
        TypeError,
        ValueError,
        ZeroDivisionError,
        IndexError,
        KeyError,
        AttributeError,
        ImportError,
        ModuleNotFoundError,
        RuntimeError,
    ):
        return {
            "success": False,
            "output": stdout_capture.getvalue(),
            "error": traceback.format_exc(),
        }


def _set_result(result: Dict[str, Any]) -> None:
    st.session_state["run_test_result"] = result
    st.rerun()


def _handle_run() -> None:
    current_code = st.session_state.get("run_test_code", "")
    result = _safe_exec(current_code)
    st.session_state["run_test_runs"] = int(st.session_state.get("run_test_runs", 0)) + 1

    if result["success"]:
        add_xp(5)

    _set_result(result)


def _load_template(template_name: str, code: str) -> None:
    st.session_state["run_test_code"] = code
    st.session_state["run_test_result"] = _blank_result()
    st.session_state["run_test_last_template"] = template_name
    st.rerun()


def _handle_clear() -> None:
    st.session_state["run_test_code"] = ""
    st.session_state["run_test_result"] = None
    st.session_state["run_test_last_template"] = "None"
    st.rerun()


def _render_result_view() -> None:
    result = st.session_state.get("run_test_result")
    if not result:
        return

    st.markdown("### Execution Result")

    if result["success"]:
        if result["output"].strip():
            st.success("Code executed successfully.")
            st.code(result["output"], language="text")
        else:
            st.success("Code executed successfully (no output).")
        return

    if result["output"].strip():
        st.markdown("#### Partial Output")
        st.code(result["output"], language="text")

    if result["error"].strip():
        st.markdown("#### Error")
        st.code(result["error"], language="text")


def _render_template_loaders() -> None:
    st.markdown("### Quick Templates")

    example_name = st.selectbox(
        "Example Snippets",
        options=list(EXAMPLE_SNIPPETS.keys()),
        key="run_test_example_select",
    )

    challenge_name = st.selectbox(
        "Challenge Snippets",
        options=list(CHALLENGE_SNIPPETS.keys()),
        key="run_test_challenge_select",
    )

    action_row(
        [
            make_button(
                label="Load Example",
                key="run_test_load_example",
                action=lambda: _load_template(example_name, EXAMPLE_SNIPPETS[example_name]),
            ),
            make_button(
                label="Load Challenge",
                key="run_test_load_challenge",
                action=lambda: _load_template(challenge_name, CHALLENGE_SNIPPETS[challenge_name]),
            ),
        ]
    )


def _render_runner_guidance() -> None:
    st.markdown("### Playground Tips")
    bullet_list(
        [
            "Use this mode to test small Python ideas quickly.",
            "Run examples to see how code behaves.",
            "Load a challenge template and complete the missing logic.",
            "Every successful run gives a small XP reward.",
        ]
    )


def _render_value_panel() -> None:
    st.markdown("### Why This Mode Matters")
    content_card(
        title="Fast Skill Builder",
        body="This mode turns the app into a real Python playground instead of just a lesson viewer.",
        meta="Good for experiments, debugging, interview-style tests, and project prototyping.",
        badge="Value Upgrade",
        min_height=160,
    )


def render(progress_data: Dict[str, Any]) -> None:
    _init_state()

    mode_header(
        RUNNER_TITLE,
        RUNNER_DESCRIPTION,
        "▶️",
    )

    metric_row(
        [
            ("Runs This Session", st.session_state.get("run_test_runs", 0)),
            ("Weak Topics", len(progress_data.get("weak_topics", {}))),
            ("Reward", "5 XP"),
            ("Last Template", st.session_state.get("run_test_last_template", "None")),
        ]
    )

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.session_state["run_test_code"] = st.text_area(
            "Python Code",
            value=st.session_state.get("run_test_code", ""),
            height=340,
            key="runner_editor_widget",
        )

        action_row(
            [
                make_button(
                    label="Run Code",
                    key="runner_run",
                    action=_handle_run,
                ),
                make_button(
                    label="Clear",
                    key="runner_clear",
                    action=_handle_clear,
                ),
            ]
        )

        _render_result_view()

    with right_col:
        _render_template_loaders()
        _render_runner_guidance()
        _render_value_panel()
