from __future__ import annotations

from typing import Any, Dict, List, Optional

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
    has_passed_project_review,
    is_project_complete,
    mark_project_complete,
)


PROJECT_MILESTONES: List[Dict[str, Any]] = [
    {
        "id": "project-1",
        "title": "Greeting App",
        "level": "Beginner",
        "duration": "20 min",
        "summary": "Build a simple Python program that greets a user by name.",
        "goal": "Practice variables, input, print, and simple function structure.",
        "requirements": [
            "Ask the user for their name",
            "Store the name in a variable",
            "Print a greeting using that name",
        ],
        "starter_code": (
            'name = input("What is your name? ")\n'
            '# print a greeting here\n'
        ),
        "example_output": "Hello, Marcus!",
    },
    {
        "id": "project-2",
        "title": "Number Checker",
        "level": "Beginner",
        "duration": "25 min",
        "summary": "Build a small program that checks whether a number is positive, negative, or zero.",
        "goal": "Practice conditionals and clean branching logic.",
        "requirements": [
            "Ask the user for a number",
            "Convert the value to an integer",
            "Use if/elif/else",
            "Print the correct classification",
        ],
        "starter_code": (
            'number = int(input("Enter a number: "))\n'
            '# write your conditional logic here\n'
        ),
        "example_output": "Positive",
    },
    {
        "id": "project-3",
        "title": "Task List Printer",
        "level": "Beginner",
        "duration": "25 min",
        "summary": "Create a list of tasks and print each one with a loop.",
        "goal": "Practice lists, loops, and clean output formatting.",
        "requirements": [
            "Create a list of at least three tasks",
            "Use a loop",
            "Print each task clearly",
        ],
        "starter_code": (
            'tasks = ["Homework", "Laundry", "Study"]\n'
            '# loop through the tasks and print each one\n'
        ),
        "example_output": "Homework\nLaundry\nStudy",
    },
    {
        "id": "project-4",
        "title": "Mini Function Project",
        "level": "Beginner",
        "duration": "30 min",
        "summary": "Write a function that calculates and returns a result, then print it.",
        "goal": "Practice function definition, return values, and calling functions.",
        "requirements": [
            "Define a function",
            "Accept at least one parameter",
            "Return a value",
            "Call the function and print the result",
        ],
        "starter_code": (
            "def double_number(number):\n"
            "    # return double the input\n"
            "    pass\n\n"
            "print(double_number(4))\n"
        ),
        "example_output": "8",
    },
]


def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    for project in PROJECT_MILESTONES:
        if project["id"] == project_id:
            return project
    return None


def get_project_summary() -> Dict[str, int]:
    completed = 0
    review_passed = 0

    for project in PROJECT_MILESTONES:
        if is_project_complete(project["id"]):
            completed += 1
        if has_passed_project_review(project["id"]):
            review_passed += 1

    return {
        "total": len(PROJECT_MILESTONES),
        "completed": completed,
        "passed_review": review_passed,
    }


def project_status_label(project_id: str) -> str:
    if is_project_complete(project_id):
        return "✅ Complete"
    if has_passed_project_review(project_id):
        return "🟢 Review Passed"
    return "🟡 In Progress"


def open_project(project_id: str) -> None:
    st.session_state["selected_project_id"] = project_id
    st.rerun()


def back_to_all_projects() -> None:
    st.session_state["selected_project_id"] = None
    st.rerun()


def send_project_to_review(project_id: str, code: str) -> None:
    st.session_state["selected_mode"] = "Review Mode"
    st.session_state["review_target_type"] = "project"
    st.session_state["review_target_id"] = project_id
    st.session_state["review_target_code"] = code
    st.rerun()


def reset_project_code(project_id: str, starter_code: str) -> None:
    st.session_state[f"project_code_{project_id}"] = starter_code
    st.rerun()


def complete_project(project_id: str) -> None:
    if mark_project_complete(project_id):
        st.success("Project marked complete.")
        st.rerun()
    else:
        st.error("Project cannot be completed until review is passed.")


def render_project_card(project: Dict[str, Any]) -> None:
    project_id = project["id"]
    status = project_status_label(project_id)

    meta_text = (
        f"<strong>Level:</strong> {project['level']} &nbsp;&nbsp; "
        f"<strong>Duration:</strong> {project['duration']}<br>"
        f"<strong>Goal:</strong> {project['goal']}"
    )

    content_card(
        title=project["title"],
        body=project["summary"],
        badge=status,
        subbadge="",
        meta_text=meta_text,
        min_height=220,
    )

    render_action_buttons(
        [
            make_button(
                label=f"Open {project['title']}",
                key=f"open_project_{project_id}",
                action=lambda: open_project(project_id),
            )
        ]
    )


def render_project_detail(project: Dict[str, Any]) -> None:
    project_id = project["id"]
    completed = is_project_complete(project_id)
    review_passed = has_passed_project_review(project_id)

    section_panel(
        title=project["title"],
        description=project["summary"],
        icon="🛠️",
    )

    render_stats(
        [
            ("Level", project["level"]),
            ("Duration", project["duration"]),
            ("Status", "Complete" if completed else "Active"),
        ]
    )

    st.markdown("### Project Goal")
    st.write(project["goal"])

    st.markdown("### Requirements")
    render_bullet_list(project["requirements"])

    st.markdown("### Example Output")
    st.code(project["example_output"], language="text")

    current_code = st.session_state.get(
        f"project_code_{project_id}",
        project["starter_code"],
    )

    updated_code = st.text_area(
        "Build your project here",
        value=current_code,
        height=320,
        key=f"project_editor_{project_id}",
    )
    st.session_state[f"project_code_{project_id}"] = updated_code

    render_action_buttons(
        [
            make_button(
                label="Load Starter Code",
                key=f"load_project_starter_{project_id}",
                action=lambda: reset_project_code(project_id, project["starter_code"]),
            ),
            make_button(
                label="Send to Review Mode",
                key=f"send_project_review_{project_id}",
                action=lambda: send_project_to_review(project_id, updated_code),
            ),
        ]
    )

    st.markdown("### Completion")

    if review_passed:
        st.success("Project review passed. You can now mark this project complete.")
    else:
        st.warning("You must pass review before completing this project.")

    render_action_buttons(
        [
            make_button(
                label="Mark Project Complete",
                key=f"mark_project_complete_{project_id}",
                action=lambda: complete_project(project_id),
                disabled=(not review_passed) or completed,
            )
        ]
    )

    if completed:
        st.caption("This project is already complete.")

    render_action_buttons(
        [
            make_button(
                label="Back to All Projects",
                key=f"back_to_projects_{project_id}",
                action=back_to_all_projects,
            )
        ]
    )


def render_catalog() -> None:
    st.subheader("All Projects")

    col1, col2 = st.columns(2)
    project_columns = [col1, col2]

    for index, project in enumerate(PROJECT_MILESTONES):
        with project_columns[index % 2]:
            render_project_card(project)
            st.markdown("")


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    summary = get_project_summary()

    section_panel(
        title="Project Mode",
        description="Build milestone-based Python projects, send them to review, and unlock completion by passing.",
        icon="🛠️",
    )

    render_stats(
        [
            ("Projects", summary["total"]),
            ("Review Passed", summary["passed_review"]),
            ("Completed", summary["completed"]),
        ]
    )

    selected_project_id = st.session_state.get("selected_project_id")
    selected_project = get_project_by_id(selected_project_id) if selected_project_id else None

    if selected_project:
        render_project_detail(selected_project)
        return

    render_catalog()