from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.ui import (
    content_card,
    make_button,
    render_action_buttons,
    render_bullet_list,
    render_stats,
    section_panel,
)
from progress import (
    get_learning_profile,
    has_passed_lesson_review,
    is_lesson_complete,
    mark_lesson_complete,
)


CURRICULUM: Dict[str, List[Dict[str, Any]]] = {
    "Beginner Track": [
        {
            "id": "python-basics-1",
            "title": "Python Basics",
            "level": "Beginner",
            "duration": "15 min",
            "summary": "Learn what Python is, how code runs, and how to write your first simple statements.",
            "concepts": [
                "What Python is",
                "Running Python code",
                "Using print()",
                "Reading simple statements",
            ],
            "example_code": 'print("Hello, Pylot!")\nprint("Python is running.")',
            "task": "Write two print statements: one that prints your name, and one that prints your favorite hobby.",
            "starter_code": 'print("Your name here")\nprint("Your hobby here")',
        },
        {
            "id": "variables-1",
            "title": "Variables",
            "level": "Beginner",
            "duration": "20 min",
            "summary": "Store values in variables and use them later in your code.",
            "concepts": [
                "Creating variables",
                "String variables",
                "Number variables",
                "Printing variable values",
            ],
            "example_code": 'name = "Marcus"\nage = 21\n\nprint(name)\nprint(age)',
            "task": "Create variables called name and favorite_number, then print both of them.",
            "starter_code": 'name = ""\nfavorite_number = 0\n\nprint(name)\nprint(favorite_number)',
        },
        {
            "id": "conditionals-1",
            "title": "Conditionals",
            "level": "Beginner",
            "duration": "20 min",
            "summary": "Use if/else logic to make decisions in your programs.",
            "concepts": [
                "if statements",
                "else statements",
                "Boolean conditions",
                "Branching program flow",
            ],
            "example_code": 'number = 7\n\nif number > 0:\n    print("Positive")\nelse:\n    print("Not positive")',
            "task": "Create a variable called score. If score is 70 or higher, print Pass. Otherwise print Try again.",
            "starter_code": 'score = 0\n\n# write your if/else here',
        },
        {
            "id": "loops-1",
            "title": "Loops",
            "level": "Beginner",
            "duration": "25 min",
            "summary": "Repeat actions with for loops and start thinking in patterns.",
            "concepts": [
                "for loops",
                "Loop variables",
                "Repeating output",
                "Iterating over lists",
            ],
            "example_code": 'numbers = [1, 2, 3]\n\nfor number in numbers:\n    print(number)',
            "task": "Create a list of three foods and use a for loop to print each one.",
            "starter_code": 'foods = ["", "", ""]\n\nfor food in foods:\n    print(food)',
        },
    ],
    "Intermediate Track": [
        {
            "id": "functions-1",
            "title": "Functions",
            "level": "Intermediate",
            "duration": "25 min",
            "summary": "Create reusable blocks of logic with parameters and return values.",
            "concepts": [
                "def statements",
                "Parameters",
                "Return values",
                "Function calls",
            ],
            "example_code": 'def square(number):\n    return number * number\n\nprint(square(5))',
            "task": "Write a function called greet that takes a name and returns a greeting string.",
            "starter_code": 'def greet(name):\n    # return a greeting\n    pass\n\nprint(greet("Marcus"))',
        },
        {
            "id": "lists-dicts-1",
            "title": "Lists and Dictionaries",
            "level": "Intermediate",
            "duration": "30 min",
            "summary": "Work with grouped data using Python collections.",
            "concepts": [
                "Lists",
                "Dictionaries",
                "Indexing",
                "Key access",
            ],
            "example_code": 'student = {"name": "Marcus", "score": 95}\nprint(student["name"])',
            "task": "Create a dictionary with keys name and city, then print both values.",
            "starter_code": 'person = {"name": "", "city": ""}\n\nprint(person["name"])\nprint(person["city"])',
        },
    ],
    "Advanced Track": [
        {
            "id": "errors-testing-1",
            "title": "Errors and Testing",
            "level": "Advanced",
            "duration": "30 min",
            "summary": "Understand common errors and start thinking about validating behavior.",
            "concepts": [
                "Exceptions",
                "try/except",
                "Testing behavior",
                "Failure cases",
            ],
            "example_code": 'try:\n    number = int("abc")\nexcept ValueError:\n    print("That was not a valid number.")',
            "task": "Write code that catches a ValueError when converting bad input to int.",
            "starter_code": 'try:\n    value = int("abc")\nexcept ValueError:\n    print("Invalid number")',
        }
    ],
}


def get_all_lessons() -> List[Dict[str, Any]]:
    lessons: List[Dict[str, Any]] = []
    for track_name, track_lessons in CURRICULUM.items():
        for lesson in track_lessons:
            lesson_copy = dict(lesson)
            lesson_copy["track"] = track_name
            lessons.append(lesson_copy)
    return lessons


def get_lesson_by_id(lesson_id: str) -> Dict[str, Any] | None:
    for lesson in get_all_lessons():
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_lesson_progress_summary() -> Dict[str, int]:
    lessons = get_all_lessons()
    completed = 0
    passed_review = 0

    for lesson in lessons:
        if is_lesson_complete(lesson["id"]):
            completed += 1
        if has_passed_lesson_review(lesson["id"]):
            passed_review += 1

    return {
        "total": len(lessons),
        "completed": completed,
        "passed_review": passed_review,
    }


def render_learning_recommendation() -> None:
    profile = get_learning_profile()

    section_panel(
        title="Curriculum",
        description="Follow a structured path from beginner to advanced Python topics.",
        icon="📚",
    )

    st.info(
        f"Recommended next step: {profile['recommended_mode']} • "
        f"Focus topic: {profile['recommended_topic']}"
    )


def open_lesson(lesson_id: str) -> None:
    st.session_state["selected_lesson_id"] = lesson_id
    st.rerun()


def go_to_review(lesson_id: str, code: str) -> None:
    st.session_state["selected_mode"] = "Review Mode"
    st.session_state["review_target_type"] = "lesson"
    st.session_state["review_target_id"] = lesson_id
    st.session_state["review_target_code"] = code
    st.rerun()


def reset_lesson_code(lesson_id: str, starter_code: str) -> None:
    st.session_state[f"lesson_code_{lesson_id}"] = starter_code
    st.rerun()


def back_to_all_lessons() -> None:
    st.session_state["selected_lesson_id"] = None
    st.rerun()


def complete_lesson(lesson_id: str) -> None:
    if mark_lesson_complete(lesson_id):
        st.success("Lesson marked complete.")
        st.rerun()
    else:
        st.error("Lesson cannot be completed until review is passed.")


def render_lesson_card(lesson: Dict[str, Any]) -> None:
    lesson_id = lesson["id"]
    completed = is_lesson_complete(lesson_id)
    review_passed = has_passed_lesson_review(lesson_id)

    badge = "✅ Complete" if completed else "🟡 In Progress"
    review_badge = "Review passed" if review_passed else "Review not passed"
    meta_text = (
        f"<strong>Level:</strong> {lesson['level']} &nbsp;&nbsp; "
        f"<strong>Duration:</strong> {lesson['duration']}"
    )

    content_card(
        title=lesson["title"],
        body=lesson["summary"],
        badge=badge,
        subbadge=review_badge,
        meta_text=meta_text,
        eyebrow=lesson["track"],
    )

    render_action_buttons(
        [
            make_button(
                label=f"Open {lesson['title']}",
                key=f"open_lesson_{lesson_id}",
                action=lambda: open_lesson(lesson_id),
            )
        ]
    )


def render_lesson_detail(lesson: Dict[str, Any]) -> None:
    lesson_id = lesson["id"]
    completed = is_lesson_complete(lesson_id)
    review_passed = has_passed_lesson_review(lesson_id)

    section_panel(
        title=lesson["title"],
        description=lesson["summary"],
        icon="📘",
        track=lesson["track"],
    )

    render_stats(
        [
            ("Level", lesson["level"]),
            ("Duration", lesson["duration"]),
            ("Status", "Complete" if completed else "Active"),
        ]
    )

    st.markdown("### Concepts")
    render_bullet_list(lesson["concepts"])

    st.markdown("### Worked Example")
    st.code(lesson["example_code"], language="python")

    st.markdown("### Your Task")
    st.info(lesson["task"])

    current_code = st.session_state.get(
        f"lesson_code_{lesson_id}",
        lesson["starter_code"],
    )

    updated_code = st.text_area(
        "Write your code here",
        value=current_code,
        height=260,
        key=f"lesson_editor_{lesson_id}",
    )
    st.session_state[f"lesson_code_{lesson_id}"] = updated_code

    render_action_buttons(
        [
            make_button(
                label="Load Starter Code",
                key=f"load_starter_{lesson_id}",
                action=lambda: reset_lesson_code(lesson_id, lesson["starter_code"]),
            ),
            make_button(
                label="Go to Review Mode",
                key=f"go_review_{lesson_id}",
                action=lambda: go_to_review(lesson_id, updated_code),
            ),
        ]
    )

    st.markdown("### Completion")

    if review_passed:
        st.success("Review passed. You can now mark this lesson complete.")
    else:
        st.warning("You must pass review before completing this lesson.")

    render_action_buttons(
        [
            make_button(
                label="Mark Lesson Complete",
                key=f"mark_complete_{lesson_id}",
                action=lambda: complete_lesson(lesson_id),
                disabled=(not review_passed) or completed,
            )
        ]
    )

    if completed:
        st.caption("This lesson is already complete.")

    render_action_buttons(
        [
            make_button(
                label="Back to All Lessons",
                key=f"back_to_lessons_{lesson_id}",
                action=back_to_all_lessons,
            )
        ]
    )


def render_track(track_name: str, track_lessons: List[Dict[str, Any]]) -> None:
    st.subheader(track_name)

    col1, col2 = st.columns(2)
    lesson_columns = [col1, col2]

    for index, lesson in enumerate(track_lessons):
        lesson_with_track = dict(lesson)
        lesson_with_track["track"] = track_name
        with lesson_columns[index % 2]:
            render_lesson_card(lesson_with_track)
            st.markdown("")


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    summary = get_lesson_progress_summary()
    render_learning_recommendation()

    render_stats(
        [
            ("Lessons", summary["total"]),
            ("Review Passed", summary["passed_review"]),
            ("Completed", summary["completed"]),
        ]
    )

    selected_lesson_id = st.session_state.get("selected_lesson_id")
    selected_lesson = get_lesson_by_id(selected_lesson_id) if selected_lesson_id else None

    if selected_lesson:
        render_lesson_detail(selected_lesson)
        return

    for track_name, track_lessons in CURRICULUM.items():
        render_track(track_name, track_lessons)