from __future__ import annotations

import io
import traceback
from contextlib import redirect_stdout
from typing import Any, Dict

import streamlit as st

from core.ui import (
    make_button,
    render_action_buttons,
    render_stats,
    section_panel,
)


def execute_user_code(code: str) -> Dict[str, Any]:
    if not code.strip():
        return {
            "success": False,
            "output": "",
            "error": "No code to run.",
        }

    output_buffer = io.StringIO()

    try:
        with redirect_stdout(output_buffer):
            exec_globals: Dict[str, Any] = {}
            exec(code, exec_globals)

        return {
            "success": True,
            "output": output_buffer.getvalue(),
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
            "output": output_buffer.getvalue(),
            "error": traceback.format_exc(),
        }


def run_code(code: str) -> None:
    result = execute_user_code(code)
    st.session_state["run_test_result"] = result
    st.rerun()


def load_example_code() -> None:
    example = (
        "numbers = [1, 2, 3, 4]\n\n"
        "for n in numbers:\n"
        "    print(n * 2)"
    )
    st.session_state["run_test_code"] = example
    st.rerun()


def clear_code() -> None:
    st.session_state["run_test_code"] = ""
    st.session_state["run_test_result"] = None
    st.rerun()


def render_execution_result() -> None:
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
    else:
        if result["output"]:
            st.code(result["output"], language="text")

        st.error("An error occurred during execution.")
        st.code(result["error"], language="text")


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    section_panel(
        title="Run / Test Mode",
        description="Execute Python code directly and inspect the output or errors.",
        icon="▶️",
    )

    render_stats(
        [
            ("Runner", "Local Python"),
            ("Execution Mode", "exec() sandbox"),
            ("Status", "Active"),
        ]
    )

    code_value = st.session_state.get("run_test_code", "")

    updated_code = st.text_area(
        "Python Code",
        value=code_value,
        height=300,
        key="run_test_editor",
    )

    st.session_state["run_test_code"] = updated_code

    render_action_buttons(
        [
            make_button(
                label="Run Code",
                key="run_test_run_code",
                action=lambda: run_code(updated_code),
            ),
            make_button(
                label="Load Example",
                key="run_test_load_example",
                action=load_example_code,
            ),
            make_button(
                label="Clear",
                key="run_test_clear_code",
                action=clear_code,
            ),
        ]
    )

    render_execution_result()