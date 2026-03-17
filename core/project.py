from __future__ import annotations

from typing import Dict, List, Optional, TypedDict

import streamlit as st

from core.engagement import get_daily_quest
from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header
from progress import (
    add_xp,
    can_claim_daily_quest,
    has_passed_project_review,
    is_lesson_complete,
    is_project_complete,
    mark_daily_quest_claimed,
    mark_project_complete,
)


class ProjectData(TypedDict):
    id: str
    title: str
    description: str
    difficulty: str
    starter_code: str
    requirements: List[str]
    reward_xp: int
    required_lessons: List[str]
    milestones: List[str]
    portfolio_value: List[str]


def build_project(
    project_id: str,
    title: str,
    description: str,
    difficulty: str,
    starter_code: str,
    requirements: List[str],
    reward_xp: int,
    required_lessons: List[str],
    milestones: List[str],
    portfolio_value: List[str],
) -> ProjectData:
    return {
        "id": project_id,
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "starter_code": starter_code,
        "requirements": requirements,
        "reward_xp": reward_xp,
        "required_lessons": required_lessons,
        "milestones": milestones,
        "portfolio_value": portfolio_value,
    }


PROJECTS: List[ProjectData] = [
    build_project(
        project_id="calculator-app",
        title="Calculator App",
        description="Build a simple calculator that adds, subtracts, multiplies, and divides two numbers.",
        difficulty="Beginner",
        starter_code=(
            "def add(a, b):\n"
            "    return a + b\n\n"
            "def subtract(a, b):\n"
            "    # return the difference\n"
            "    pass\n\n"
            "def multiply(a, b):\n"
            "    # return the product\n"
            "    pass\n\n"
            "def divide(a, b):\n"
            "    # return the quotient\n"
            "    pass\n\n"
            "print(add(2, 3))\n"
        ),
        requirements=[
            "Use at least one function",
            "Print at least one result",
            "Implement calculator logic",
            "Handle all four operations",
        ],
        reward_xp=60,
        required_lessons=["variables", "conditionals", "functions"],
        milestones=[
            "Create the math functions",
            "Make each function return a value",
            "Test the operations with print statements",
            "Clean up unfinished code before review",
        ],
        portfolio_value=[
            "Shows practical Python logic and reusable functions",
            "Demonstrates basic software structure",
            "Can be upgraded into a menu-based calculator app",
        ],
    ),
    build_project(
        project_id="task-tracker",
        title="Task Tracker",
        description="Build a basic task tracker using a list and loops.",
        difficulty="Beginner",
        starter_code=(
            "tasks = []\n\n"
            'tasks.append("Study Python")\n'
            'tasks.append("Build a project")\n\n'
            "for task in tasks:\n"
            "    print(task)\n"
        ),
        requirements=[
            "Use a list",
            "Add at least one task",
            "Print the stored tasks",
            "Use a loop",
        ],
        reward_xp=60,
        required_lessons=["variables", "loops"],
        milestones=[
            "Create the task list",
            "Add multiple tasks",
            "Loop through the tasks",
            "Print clear output for the user",
        ],
        portfolio_value=[
            "Shows how to store and display structured data",
            "Demonstrates loops and list usage",
            "Can be upgraded into a real terminal productivity app",
        ],
    ),
]


def get_project(project_id: str) -> Optional[ProjectData]:
    for project in PROJECTS:
        if project["id"] == project_id:
            return project
    return None


def is_project_unlocked(project: ProjectData) -> bool:
    required_lessons = project.get("required_lessons", [])
    if not required_lessons:
        return True
    return all(is_lesson_complete(lesson_id) for lesson_id in required_lessons)


def get_project_unlock_reason(project: ProjectData) -> str:
    missing_lessons = [
        lesson_id
        for lesson_id in project.get("required_lessons", [])
        if not is_lesson_complete(lesson_id)
    ]

    if not missing_lessons:
        return ""

    formatted = ", ".join(missing_lessons)
    return f"Complete these lessons first: {formatted}"


def get_project_summary() -> Dict[str, int]:
    completed = 0
    reviewed = 0
    unlocked = 0

    for project in PROJECTS:
        project_id = project["id"]
        if is_project_complete(project_id):
            completed += 1
        if has_passed_project_review(project_id):
            reviewed += 1
        if is_project_unlocked(project):
            unlocked += 1

    return {
        "total": len(PROJECTS),
        "completed": completed,
        "reviewed": reviewed,
        "unlocked": unlocked,
    }


def open_project(project_id: str) -> None:
    project = get_project(project_id)
    if project is None:
        st.error("Project not found.")
        return

    if not is_project_unlocked(project):
        st.warning(get_project_unlock_reason(project))
        return

    st.session_state["selected_project_id"] = project_id
    st.rerun()


def close_project() -> None:
    st.session_state["selected_project_id"] = None
    st.rerun()


def load_project_starter(project_id: str, starter_code: str) -> None:
    st.session_state[f"project_editor_{project_id}"] = starter_code
    st.rerun()


def send_project_to_review(project_id: str, code: str) -> None:
    st.session_state["review_target_type"] = "project"
    st.session_state["review_target_id"] = project_id
    st.session_state["review_target_code"] = code
    st.session_state["selected_mode"] = "Review Mode"
    st.rerun()


def complete_project(project_id: str) -> None:
    mark_project_complete(project_id)
    st.success("Project completed.")
    st.session_state["selected_project_id"] = None
    st.rerun()


def claim_project_daily_quest() -> None:
    quest = get_daily_quest()

    if quest["mode"] != "Project Mode":
        st.warning("Today's quest is tied to a different mode.")
        return

    if not can_claim_daily_quest():
        st.warning("Daily quest already claimed today.")
        return

    add_xp(int(quest["reward_xp"]))
    mark_daily_quest_claimed()
    st.success(f"Daily quest reward claimed: +{quest['reward_xp']} XP")
    st.rerun()


def project_status(project_id: str) -> tuple[bool, bool]:
    completed = is_project_complete(project_id)
    review_passed = has_passed_project_review(project_id)
    return completed, review_passed


def render_project_daily_quest_panel() -> None:
    quest = get_daily_quest()
    if quest["mode"] != "Project Mode":
        return

    st.markdown("### Today's Project Quest")
    content_card(
        title=quest["title"],
        body=quest["description"],
        meta=f"Hint: {quest['hint']}",
        badge=f"+{quest['reward_xp']} XP",
        min_height=130,
    )

    action_row(
        [
            make_button(
                label="Claim Daily Quest Reward",
                key="project_claim_daily_quest",
                action=claim_project_daily_quest,
                disabled=not can_claim_daily_quest(),
            )
        ]
    )


def render_project_card(project: ProjectData) -> None:
    project_id = project["id"]
    completed, review_passed = project_status(project_id)
    unlocked = is_project_unlocked(project)

    if completed:
        badge = "✅ Complete"
    elif review_passed:
        badge = "🟢 Review Passed"
    elif unlocked:
        badge = "🟡 Unlocked"
    else:
        badge = "🔒 Locked"

    meta_parts = [
        f"Difficulty: {project['difficulty']}",
        f"Reward: {project['reward_xp']} XP",
    ]

    if project["required_lessons"]:
        meta_parts.append("Required lessons: " + ", ".join(project["required_lessons"]))

    if not unlocked:
        meta_parts.append(get_project_unlock_reason(project))

    content_card(
        title=project["title"],
        body=project["description"],
        meta="<br>".join(meta_parts),
        badge=badge,
        min_height=230,
    )

    action_row(
        [
            make_button(
                label=f"Open {project['title']}",
                key=f"open_project_{project_id}",
                action=lambda selected_id=project_id: open_project(selected_id),
                disabled=not unlocked,
            )
        ]
    )


def render_project_catalog(_: Dict[str, object]) -> None:
    summary = get_project_summary()

    mode_header(
        "Project Mode",
        "Build milestone projects and unlock them by completing lesson prerequisites.",
        "🛠️",
    )

    metric_row(
        [
            ("Projects", summary["total"]),
            ("Unlocked", summary["unlocked"]),
            ("Reviewed", summary["reviewed"]),
            ("Completed", summary["completed"]),
        ]
    )

    render_project_daily_quest_panel()

    col1, col2 = st.columns(2)
    columns = [col1, col2]

    for index, project in enumerate(PROJECTS):
        with columns[index % 2]:
            render_project_card(project)


def render_project_requirements(project: ProjectData) -> None:
    st.markdown("### Requirements")
    bullet_list(project["requirements"])


def render_project_milestones(project: ProjectData) -> None:
    st.markdown("### Build Milestones")
    bullet_list(project["milestones"])


def render_project_portfolio_value(project: ProjectData) -> None:
    st.markdown("### Why This Project Has Value")
    bullet_list(project["portfolio_value"])


def render_project_editor(project: ProjectData) -> str:
    editor_key = f"project_editor_{project['id']}"

    if editor_key not in st.session_state:
        st.session_state[editor_key] = project["starter_code"]

    user_code = st.text_area(
        "Project Code",
        value=st.session_state[editor_key],
        height=320,
        key=f"{editor_key}_widget",
    )

    st.session_state[editor_key] = user_code
    return user_code


def render_project_editor_actions(project: ProjectData, user_code: str) -> None:
    project_id = project["id"]

    action_row(
        [
            make_button(
                label="Load Starter Code",
                key=f"starter_{project_id}",
                action=lambda selected_id=project_id, starter=project["starter_code"]: load_project_starter(selected_id, starter),
            ),
            make_button(
                label="Send to Review",
                key=f"review_{project_id}",
                action=lambda selected_id=project_id, code=user_code: send_project_to_review(selected_id, code),
            ),
        ]
    )


def render_completion_section(project: ProjectData) -> None:
    project_id = project["id"]
    completed, review_passed = project_status(project_id)

    st.markdown("### Completion")

    if review_passed:
        st.success(f"Review passed. Completing this project awards {project['reward_xp']} XP.")
    else:
        st.info("Pass review before completing this project.")

    action_row(
        [
            make_button(
                label="Mark Complete",
                key=f"complete_{project_id}",
                action=lambda selected_id=project_id: complete_project(selected_id),
                disabled=(not review_passed) or completed,
            ),
            make_button(
                label="Back to Projects",
                key=f"back_{project_id}",
                action=close_project,
            ),
        ]
    )


def render_project_detail(progress_data: Dict[str, object], project_id: str) -> None:
    _ = progress_data

    project = get_project(project_id)
    if project is None:
        st.error("Project not found.")
        return

    if not is_project_unlocked(project):
        st.warning(get_project_unlock_reason(project))
        close_project()
        return

    mode_header(
        project["title"],
        project["description"],
        "🚀",
    )

    completed, review_passed = project_status(project_id)

    metric_row(
        [
            ("Difficulty", project["difficulty"]),
            ("Reward", f"{project['reward_xp']} XP"),
            ("Reviewed", "Yes" if review_passed else "No"),
            ("Completed", "Yes" if completed else "No"),
        ]
    )

    if project["required_lessons"]:
        st.caption("Required lessons: " + ", ".join(project["required_lessons"]))

    left_col, right_col = st.columns([2, 1])

    with left_col:
        render_project_requirements(project)
        user_code = render_project_editor(project)
        render_project_editor_actions(project, user_code)
        render_completion_section(project)

    with right_col:
        render_project_milestones(project)
        render_project_portfolio_value(project)
        render_project_daily_quest_panel()


def render(progress_data: Dict[str, object]) -> None:
    selected_project_id = st.session_state.get("selected_project_id")

    if selected_project_id:
        render_project_detail(progress_data, selected_project_id)
        return

    render_project_catalog(progress_data)
