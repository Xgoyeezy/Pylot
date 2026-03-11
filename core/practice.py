from __future__ import annotations

from typing import Any, Dict, List, Tuple

import streamlit as st

from core.ui import (
    make_button,
    render_action_buttons,
    render_bullet_list,
    render_stats,
    section_panel,
)
from progress import get_learning_profile, update_weak_topics


def get_top_weak_topic(weak_topics: Dict[str, int]) -> str:
    if not weak_topics:
        return "general-python"

    sorted_topics = sorted(
        weak_topics.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    return sorted_topics[0][0]


def get_practice_exercise(weak_topics: Dict[str, int]) -> Dict[str, Any]:
    topic = get_top_weak_topic(weak_topics)

    exercises = {
        "functions": {
            "title": "Practice: Writing Functions",
            "topic": "functions",
            "prompt": "Write a function called `double_number` that takes one number and returns double its value.",
            "starter_code": (
                "def double_number(number):\n"
                "    # your code here\n"
                "    pass\n\n"
                "print(double_number(4))"
            ),
            "required_patterns": ["def ", "return"],
        },
        "append": {
            "title": "Practice: Using append()",
            "topic": "append",
            "prompt": "Create an empty list called `items`, add three strings to it using `.append()`, then print the list.",
            "starter_code": (
                "items = []\n"
                "# add three items here\n"
                "print(items)"
            ),
            "required_patterns": [".append(", "print("],
        },
        "enumerate": {
            "title": "Practice: Using enumerate()",
            "topic": "enumerate",
            "prompt": "Loop through the `tasks` list and print each task with a number starting at 1 using `enumerate()`.",
            "starter_code": (
                'tasks = ["Homework", "Laundry", "Study"]\n'
                "# write your loop here"
            ),
            "required_patterns": ["enumerate(", "for ", "print("],
        },
        "while-loops": {
            "title": "Practice: While Loops",
            "topic": "while-loops",
            "prompt": "Use a `while` loop to print the numbers 1 through 5.",
            "starter_code": (
                "count = 1\n"
                "# write your while loop here"
            ),
            "required_patterns": ["while ", "print("],
        },
        "conditionals": {
            "title": "Practice: Conditionals",
            "topic": "conditionals",
            "prompt": "Ask the user for a number. If the number is positive, print `Positive`. Otherwise print `Not positive`.",
            "starter_code": (
                'number = int(input("Enter a number: "))\n'
                "# write your conditional here"
            ),
            "required_patterns": ["if ", "print("],
        },
        "print": {
            "title": "Practice: Printing Output",
            "topic": "print",
            "prompt": "Create a variable called `message` with the value `Hello, Pylot!` and print it.",
            "starter_code": (
                'message = "Hello, Pylot!"\n'
                "# print the message"
            ),
            "required_patterns": ["print("],
        },
        "input": {
            "title": "Practice: User Input",
            "topic": "input",
            "prompt": "Ask the user for their favorite color and print a sentence using their answer.",
            "starter_code": (
                'color = input("What is your favorite color? ")\n'
                "# print a sentence using color"
            ),
            "required_patterns": ["input(", "print("],
        },
        "f-strings": {
            "title": "Practice: f-Strings",
            "topic": "f-strings",
            "prompt": "Create a variable called `name`, set it to your name, and print a greeting using an f-string.",
            "starter_code": (
                'name = "Marcus"\n'
                "# print a greeting using an f-string"
            ),
            "required_patterns": ['f"', "print("],
        },
        "general-python": {
            "title": "Practice: General Python",
            "topic": "general-python",
            "prompt": "Create a list of three numbers and use a loop to print each one.",
            "starter_code": (
                "numbers = [1, 2, 3]\n"
                "# write your loop here"
            ),
            "required_patterns": ["for ", "print("],
        },
    }

    return exercises.get(topic, exercises["general-python"])


def review_practice_submission(user_code: str, exercise: Dict[str, Any]) -> Tuple[str, List[str], bool]:
    if not user_code.strip():
        return (
            "Write some code first, then submit it for review.",
            [exercise.get("topic", "general-python")],
            False,
        )

    feedback: List[str] = []
    missed_topics: List[str] = []

    for pattern in exercise.get("required_patterns", []):
        if pattern not in user_code:
            if pattern == "def ":
                feedback.append("Your solution should define a function.")
                missed_topics.append("functions")
            elif pattern == "return":
                feedback.append("Your function should return a value.")
                missed_topics.append("functions")
            elif pattern == ".append(":
                feedback.append("Use `.append()` to add items to the list.")
                missed_topics.append("append")
            elif pattern == "enumerate(":
                feedback.append("Use `enumerate()` for this exercise.")
                missed_topics.append("enumerate")
            elif pattern == "while ":
                feedback.append("This exercise should use a `while` loop.")
                missed_topics.append("while-loops")
            elif pattern == "if ":
                feedback.append("This exercise needs an `if` statement.")
                missed_topics.append("conditionals")
            elif pattern == "print(":
                feedback.append("Your solution should print output.")
                missed_topics.append("print")
            elif pattern == "input(":
                feedback.append("This exercise expects you to use `input()`.")
                missed_topics.append("input")
            elif pattern == 'f"':
                feedback.append("Try using an f-string.")
                missed_topics.append("f-strings")
            elif pattern == "for ":
                feedback.append("This exercise should use a `for` loop.")
                missed_topics.append("loops")

    passed = len(feedback) == 0

    if passed:
        feedback.append("Nice work. Your practice solution uses the target technique.")
        feedback.append("Try modifying the code to test different inputs.")

    feedback_text = "\n".join(f"- {item}" for item in feedback)
    unique_topics = list(dict.fromkeys(missed_topics))
    return feedback_text, unique_topics, passed


def render_learning_profile() -> None:
    profile = get_learning_profile()

    section_panel(
        title="Personalized Practice",
        description="Practice adapts based on your weak topics and recent review results.",
        icon="🧠",
    )

    render_stats(
        [
            ("Completed Lessons", profile["completed_lessons"]),
            ("Completed Projects", profile["completed_projects"]),
            ("Recommended Mode", profile["recommended_mode"]),
        ]
    )

    if profile["top_weak_topics"]:
        st.markdown("### Current Focus Areas")
        focus_lines = [
            f"{topic} — weakness score {score}"
            for topic, score in profile["top_weak_topics"]
        ]
        render_bullet_list(focus_lines)
    else:
        st.success("No major weak topics detected yet. Great start.")


def load_practice_starter(starter_code: str) -> None:
    st.session_state["practice_code"] = starter_code
    st.rerun()


def submit_practice_review(user_code: str, exercise: Dict[str, Any]) -> None:
    feedback_text, missed_topics, passed = review_practice_submission(user_code, exercise)

    if passed:
        update_weak_topics([exercise["topic"]], success=True)
    else:
        update_weak_topics(missed_topics or [exercise["topic"]], success=False)

    st.session_state["practice_feedback"] = feedback_text
    st.session_state["practice_missed_topics"] = missed_topics
    st.session_state["practice_passed"] = passed
    st.rerun()


def render_feedback() -> None:
    if "practice_feedback" in st.session_state:
        st.markdown("### Feedback")
        if st.session_state.get("practice_passed"):
            st.success(st.session_state["practice_feedback"])
        else:
            st.warning(st.session_state["practice_feedback"])

    missed = st.session_state.get("practice_missed_topics", [])
    if missed:
        st.caption("Topics to reinforce: " + ", ".join(missed))


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    render_learning_profile()

    weak_topics = get_learning_profile()["weak_topics"]
    exercise = get_practice_exercise(weak_topics)

    section_panel(
        title=exercise["title"],
        description=exercise["prompt"],
        icon="📝",
    )

    default_code = st.session_state.get(
        "practice_code",
        exercise["starter_code"],
    )

    user_code = st.text_area(
        "Write your code here",
        value=default_code,
        height=260,
        key="practice_code_editor",
    )
    st.session_state["practice_code"] = user_code

    render_action_buttons(
        [
            make_button(
                label="Load Starter Code",
                key="practice_load_starter",
                action=lambda: load_practice_starter(exercise["starter_code"]),
            ),
            make_button(
                label="Review Submission",
                key="practice_review_submission",
                action=lambda: submit_practice_review(user_code, exercise),
            ),
        ]
    )

    render_feedback()