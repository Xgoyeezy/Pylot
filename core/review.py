from __future__ import annotations

from typing import Any, Dict, Tuple

import streamlit as st

from core.ui import make_button, render_action_buttons, section_panel
from progress import (
    set_lesson_review_result,
    set_project_review_result,
)


def review_code_submission(code: str, target_type: str) -> Tuple[bool, int, str]:
    code = code.strip()

    if not code:
        return False, 0, "No code was submitted. Paste or write code before running review."

    score = 0
    feedback_parts: list[str] = []

    line_count = len([line for line in code.splitlines() if line.strip()])
    has_print = "print(" in code
    has_def = "def " in code
    has_if = "if " in code
    has_for = "for " in code
    has_while = "while " in code
    has_return = "return" in code
    has_input = "input(" in code

    if line_count >= 2:
        score += 15
    else:
        feedback_parts.append("Your code is very short. Add a more complete solution.")

    if has_print:
        score += 15
    else:
        feedback_parts.append("Consider printing output so the result is visible.")

    if has_def:
        score += 20

    if has_return:
        score += 10

    if has_if:
        score += 10

    if has_for or has_while:
        score += 10

    if has_input:
        score += 5

    if "pass" not in code:
        score += 10
    else:
        feedback_parts.append("Your code still contains `pass`, which usually means the task is unfinished.")

    if "=" in code:
        score += 5

    if target_type == "project":
        if line_count >= 6:
            score += 10
        else:
            feedback_parts.append("Projects should usually be a little more substantial than lesson submissions.")
    else:
        if line_count >= 3:
            score += 10
        else:
            feedback_parts.append("Try expanding the lesson solution a little more.")

    passed = score >= 70

    if passed:
        feedback = (
            f"Nice work. Your {target_type} submission passed review with a score of {score}%.\n\n"
            "Your code looks complete enough to unlock completion."
        )
    else:
        extra = (
            "\n".join(f"- {item}" for item in feedback_parts)
            if feedback_parts
            else "- Add a bit more detail and structure to your solution."
        )
        feedback = (
            f"Your {target_type} submission did not pass yet. Score: {score}%.\n\n"
            "What to improve:\n"
            f"{extra}"
        )

    return passed, score, feedback


def render_target_summary(target_type: str, target_id: str) -> None:
    label = "Lesson" if target_type == "lesson" else "Project"

    section_panel(
        title="Review Mode",
        description=f"Reviewing: {label} — {target_id}",
        icon="✅",
    )


def save_review_result(
    target_type: str,
    target_id: str,
    passed: bool,
    score: int,
    feedback: str,
) -> None:
    if target_type == "lesson":
        set_lesson_review_result(
            lesson_id=target_id,
            passed=passed,
            score=score,
            feedback=feedback,
        )
    elif target_type == "project":
        set_project_review_result(
            project_id=target_id,
            passed=passed,
            score=score,
            feedback=feedback,
        )


def render_empty_state() -> None:
    section_panel(
        title="Review Mode",
        description="No lesson or project has been sent to Review Mode yet.",
        icon="✅",
    )
    st.info("Open Course Mode or Project Mode, then use the button that sends code to Review Mode.")


def clear_review_target() -> None:
    st.session_state["review_target_type"] = None
    st.session_state["review_target_id"] = None
    st.session_state["review_target_code"] = ""
    st.session_state["review_result"] = None
    st.rerun()


def run_review(target_type: str, target_id: str, submitted_code: str) -> None:
    passed, score, feedback = review_code_submission(submitted_code, target_type)

    st.session_state["review_result"] = {
        "target_type": target_type,
        "target_id": target_id,
        "passed": passed,
        "score": score,
        "feedback": feedback,
    }

    save_review_result(
        target_type=target_type,
        target_id=target_id,
        passed=passed,
        score=score,
        feedback=feedback,
    )
    st.rerun()


def return_to_next_mode(target_type: str) -> None:
    st.session_state["selected_mode"] = "Course Mode" if target_type == "lesson" else "Project Mode"
    st.rerun()


def render_result(result: Dict[str, Any], target_type: str, target_id: str) -> None:
    if result.get("target_type") != target_type or result.get("target_id") != target_id:
        return

    st.markdown("### Review Result")

    if result["passed"]:
        st.success(result["feedback"])
    else:
        st.error(result["feedback"])

    st.metric("Score", f"{result['score']}%")

    next_mode = "Course Mode" if target_type == "lesson" else "Project Mode"
    render_action_buttons(
        [
            make_button(
                label=f"Return to {next_mode}",
                key=f"return_to_{next_mode}_{target_id}",
                action=lambda: return_to_next_mode(target_type),
            )
        ]
    )


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    target_type = st.session_state.get("review_target_type")
    target_id = st.session_state.get("review_target_id")
    initial_code = st.session_state.get("review_target_code", "")

    if not target_type or not target_id:
        render_empty_state()
        return

    render_target_summary(target_type, target_id)

    st.markdown("### Submission")
    submitted_code = st.text_area(
        "Code to review",
        value=initial_code,
        height=280,
        key=f"review_code_{target_type}_{target_id}",
    )

    render_action_buttons(
        [
            make_button(
                label="Run Review",
                key=f"run_review_{target_type}_{target_id}",
                action=lambda: run_review(target_type, target_id, submitted_code),
            ),
            make_button(
                label="Clear Review Target",
                key=f"clear_review_target_{target_type}_{target_id}",
                action=clear_review_target,
            ),
        ]
    )

    result = st.session_state.get("review_result")
    if result:
        render_result(result, target_type, target_id)