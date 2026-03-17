from __future__ import annotations

from typing import Any, Dict, List, Tuple, TypedDict

import streamlit as st

from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header
from progress import set_lesson_review_result, set_project_review_result


PASSING_SCORE = 70


class ReviewBreakdown(TypedDict):
    length: int
    output: int
    structure: int
    completion: int
    total: int


def review_code_submission(code: str, target_type: str) -> Tuple[bool, int, str, ReviewBreakdown]:
    normalized_code = code.strip()

    if not normalized_code:
        empty_breakdown: ReviewBreakdown = {
            "length": 0,
            "output": 0,
            "structure": 0,
            "completion": 0,
            "total": 0,
        }
        return (
            False,
            0,
            "No code was submitted. Paste or write code before running review.",
            empty_breakdown,
        )

    feedback: List[str] = []

    non_empty_lines = [line for line in normalized_code.splitlines() if line.strip()]
    line_count = len(non_empty_lines)

    checks = {
        "print": "print(" in normalized_code,
        "function": "def " in normalized_code,
        "return": "return" in normalized_code,
        "conditional": "if " in normalized_code,
        "loop": ("for " in normalized_code) or ("while " in normalized_code),
        "input": "input(" in normalized_code,
        "assignment": "=" in normalized_code,
        "unfinished": "pass" in normalized_code,
    }

    length_score = _score_for_length(line_count, target_type, feedback)
    output_score = _score_for_output(checks["print"], feedback)
    structure_score = _score_for_structure(checks, feedback)
    completion_score = _score_for_completion(checks["unfinished"], feedback)

    score = length_score + output_score + structure_score + completion_score
    passed = score >= PASSING_SCORE

    breakdown: ReviewBreakdown = {
        "length": length_score,
        "output": output_score,
        "structure": structure_score,
        "completion": completion_score,
        "total": score,
    }

    summary = build_review_feedback(target_type, passed, score, feedback, breakdown)
    return passed, score, summary, breakdown


def _score_for_length(line_count: int, target_type: str, feedback: List[str]) -> int:
    if target_type == "project":
        if line_count >= 10:
            return 25
        if line_count >= 6:
            feedback.append("Project length is decent, but it could still be a little more developed.")
            return 18
        feedback.append("Projects should usually be more substantial.")
        return 8 if line_count >= 3 else 0

    if line_count >= 5:
        return 20
    if line_count >= 3:
        feedback.append("Your lesson solution works as a start, but a little more development would help.")
        return 15

    feedback.append("Try expanding the lesson solution a little more.")
    return 8 if line_count >= 2 else 0


def _score_for_output(has_print: bool, feedback: List[str]) -> int:
    if has_print:
        return 15

    feedback.append("Consider printing output so the result is visible and easier to verify.")
    return 0


def _score_for_structure(checks: Dict[str, bool], feedback: List[str]) -> int:
    score = 0

    if checks["function"]:
        score += 15
    if checks["return"]:
        score += 10
    if checks["conditional"]:
        score += 10
    if checks["loop"]:
        score += 10
    if checks["input"]:
        score += 5
    if checks["assignment"]:
        score += 5

    if not any(
        [
            checks["function"],
            checks["conditional"],
            checks["loop"],
            checks["assignment"],
        ]
    ):
        feedback.append("Add more Python structure such as variables, logic, loops, or functions.")

    return score


def _score_for_completion(has_unfinished_code: bool, feedback: List[str]) -> int:
    if has_unfinished_code:
        feedback.append("Your code still contains `pass`, which usually means the task is unfinished.")
        return 0
    return 15


def build_review_feedback(
    target_type: str,
    passed: bool,
    score: int,
    feedback_items: List[str],
    breakdown: ReviewBreakdown,
) -> str:
    if passed:
        strengths = [
            f"- Length score: {breakdown['length']}",
            f"- Output score: {breakdown['output']}",
            f"- Structure score: {breakdown['structure']}",
            f"- Completion score: {breakdown['completion']}",
        ]
        return (
            f"Nice work. Your {target_type} submission passed review with a score of {score}%.\n\n"
            "Why it passed:\n"
            + "\n".join(strengths)
            + "\n\nYour code looks complete enough to unlock completion."
        )

    bullet_lines = (
        "\n".join(f"- {item}" for item in feedback_items)
        if feedback_items
        else "- Add a bit more detail and structure to your solution."
    )

    return (
        f"Your {target_type} submission did not pass yet. Score: {score}%.\n\n"
        f"Passing score: {PASSING_SCORE}%.\n\n"
        "What to improve:\n"
        f"{bullet_lines}"
    )


def render_target_summary(target_type: str, target_id: str) -> None:
    label = "Lesson" if target_type == "lesson" else "Project"

    mode_header(
        "Review Mode",
        f"Reviewing: {label} — {target_id}",
        "✅",
    )
    st.caption(f"Passing threshold: {PASSING_SCORE}%")


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
        return

    set_project_review_result(
        project_id=target_id,
        passed=passed,
        score=score,
        feedback=feedback,
    )


def clear_review_target() -> None:
    st.session_state["review_target_type"] = None
    st.session_state["review_target_id"] = None
    st.session_state["review_target_code"] = ""
    st.session_state["review_result"] = None
    st.rerun()


def return_to_origin_mode(target_type: str) -> None:
    st.session_state["selected_mode"] = "Course Mode" if target_type == "lesson" else "Project Mode"
    st.rerun()


def run_review(target_type: str, target_id: str, submitted_code: str) -> None:
    passed, score, feedback, breakdown = review_code_submission(submitted_code, target_type)

    st.session_state["review_result"] = {
        "target_type": target_type,
        "target_id": target_id,
        "passed": passed,
        "score": score,
        "feedback": feedback,
        "breakdown": breakdown,
    }

    save_review_result(
        target_type=target_type,
        target_id=target_id,
        passed=passed,
        score=score,
        feedback=feedback,
    )
    st.rerun()


def render_empty_state() -> None:
    mode_header(
        "Review Mode",
        "No lesson or project has been sent to Review Mode yet.",
        "✅",
    )
    st.info("Open Course Mode or Project Mode, then send code to Review Mode.")


def render_breakdown(breakdown: ReviewBreakdown) -> None:
    st.markdown("### Score Breakdown")
    metric_row(
        [
            ("Length", breakdown["length"]),
            ("Output", breakdown["output"]),
            ("Structure", breakdown["structure"]),
            ("Completion", breakdown["completion"]),
        ]
    )


def render_result(result: Dict[str, Any], target_type: str, target_id: str) -> None:
    if result.get("target_type") != target_type or result.get("target_id") != target_id:
        return

    st.markdown("### Review Result")

    if result["passed"]:
        st.success(result["feedback"])
    else:
        st.error(result["feedback"])

    metric_row(
        [
            ("Score", f"{result['score']}%"),
            ("Passing Score", f"{PASSING_SCORE}%"),
            ("Status", "Pass" if result["passed"] else "Not Yet"),
        ]
    )

    breakdown = result.get("breakdown")
    if breakdown:
        render_breakdown(breakdown)

    next_mode = "Course Mode" if target_type == "lesson" else "Project Mode"
    action_row(
        [
            make_button(
                label=f"Return to {next_mode}",
                key=f"return_to_{target_type}_{target_id}",
                action=lambda: return_to_origin_mode(target_type),
            ),
            make_button(
                label="Clear Review Target",
                key=f"clear_review_result_{target_type}_{target_id}",
                action=clear_review_target,
            ),
        ]
    )


def render_guidance(target_type: str) -> None:
    st.markdown("### Review Checklist")

    common_items = [
        "Make sure your code is not empty",
        "Print output when it helps verify results",
        "Remove unfinished `pass` lines",
        "Use clear Python structure such as variables, loops, conditionals, or functions",
    ]

    if target_type == "project":
        common_items.append("Projects should be more developed than small lesson answers")
    else:
        common_items.append("Lesson solutions should still show enough structure to demonstrate understanding")

    bullet_list(common_items)


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    target_type = st.session_state.get("review_target_type")
    target_id = st.session_state.get("review_target_id")
    initial_code = st.session_state.get("review_target_code", "")

    if not target_type or not target_id:
        render_empty_state()
        return

    render_target_summary(target_type, target_id)

    top_col, side_col = st.columns([2, 1])

    with top_col:
        submitted_code = st.text_area(
            "Code to Review",
            value=initial_code,
            height=300,
            key=f"review_code_{target_type}_{target_id}",
        )

        action_row(
            [
                make_button(
                    label="Run Review",
                    key=f"run_review_{target_type}_{target_id}",
                    action=lambda: run_review(target_type, target_id, submitted_code),
                ),
                make_button(
                    label="Clear Review Target",
                    key=f"clear_review_{target_type}_{target_id}",
                    action=clear_review_target,
                ),
            ]
        )

        result = st.session_state.get("review_result")
        if result:
            render_result(result, target_type, target_id)

    with side_col:
        render_guidance(target_type)
        content_card(
            title="Review Goal",
            body="Use review to prove your code is complete enough before marking lessons or projects finished.",
            meta="Passing score: 70%",
            badge="Quality Gate",
            min_height=160,
        )
