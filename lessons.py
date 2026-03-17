from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

import streamlit as st

from core.engagement import get_skill_tree
from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header
from progress import has_passed_lesson_review, is_lesson_complete, mark_lesson_complete


class LessonData(TypedDict):
    id: str
    title: str
    concept: str
    example: str
    task: str
    starter_code: str
    summary: str
    duration: str
    xp_reward: int
    track: str


def build_lesson(
    lesson_id: str,
    title: str,
    concept: str,
    example: str,
    task: str,
    starter_code: str,
    summary: str,
    duration: str,
    xp_reward: int,
    track: str,
) -> LessonData:
    return {
        "id": lesson_id,
        "title": title,
        "concept": concept,
        "example": example,
        "task": task,
        "starter_code": starter_code,
        "summary": summary,
        "duration": duration,
        "xp_reward": xp_reward,
        "track": track,
    }


LESSONS: Dict[str, List[LessonData]] = {
    "Beginner": [
        build_lesson(
            lesson_id="variables",
            title="Variables",
            concept="Variables store values that can be reused later in your program.",
            example="x = 5\nprint(x)",
            task="Create a variable named number and print it.",
            starter_code="number = 0\nprint(number)",
            summary="Store and reuse values with variables.",
            duration="10 min",
            xp_reward=20,
            track="Beginner",
        ),
        build_lesson(
            lesson_id="conditionals",
            title="Conditionals",
            concept="Conditionals allow your program to make decisions.",
            example="x = 5\nif x > 3:\n    print('big')",
            task="Check if number is greater than 10 and print the result.",
            starter_code="number = 15\n\nif number > 10:\n    print('big')\nelse:\n    print('small')",
            summary="Use if statements to control program flow.",
            duration="12 min",
            xp_reward=20,
            track="Beginner",
        ),
        build_lesson(
            lesson_id="loops",
            title="Loops",
            concept="Loops repeat actions without rewriting the same code many times.",
            example='for item in ["a", "b", "c"]:\n    print(item)',
            task="Use a loop to print the numbers 1 through 5.",
            starter_code="for number in range(1, 6):\n    print(number)",
            summary="Repeat actions efficiently with for loops.",
            duration="14 min",
            xp_reward=25,
            track="Beginner",
        ),
        build_lesson(
            lesson_id="functions",
            title="Functions",
            concept="Functions let you group reusable logic into named blocks of code.",
            example="def greet(name):\n    return f'Hello, {name}'\n\nprint(greet('Marc'))",
            task="Write a function called add_numbers that returns the sum of two numbers.",
            starter_code=(
                "def add_numbers(a, b):\n"
                "    # return the sum\n"
                "    pass\n\n"
                "print(add_numbers(2, 3))"
            ),
            summary="Write reusable code with functions.",
            duration="16 min",
            xp_reward=30,
            track="Beginner",
        ),
    ],
    "Intermediate": [],
    "Advanced": [],
}


def get_all_lessons() -> List[LessonData]:
    all_lessons: List[LessonData] = []
    for lesson_group in LESSONS.values():
        all_lessons.extend(lesson_group)
    return all_lessons


def find_lesson(lesson_id: str) -> Optional[LessonData]:
    for lesson in get_all_lessons():
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_skill_order() -> List[str]:
    return [str(node["id"]) for node in get_skill_tree()]


def is_lesson_unlocked(lesson_id: str) -> bool:
    skill_order = get_skill_order()

    if lesson_id not in skill_order:
        return True

    index = skill_order.index(lesson_id)
    if index == 0:
        return True

    previous_lesson_id = skill_order[index - 1]
    return is_lesson_complete(previous_lesson_id)


def get_locked_reason(lesson_id: str) -> str:
    skill_order = get_skill_order()

    if lesson_id not in skill_order:
        return ""

    index = skill_order.index(lesson_id)
    if index == 0:
        return ""

    previous_lesson_id = skill_order[index - 1]
    previous_lesson = find_lesson(previous_lesson_id)

    if previous_lesson is None:
        return "Complete the previous lesson first."

    return f"Complete {previous_lesson['title']} first."


def get_summary(progress_data: Dict[str, Any]) -> Dict[str, int]:
    all_lessons = get_all_lessons()
    completed = 0
    reviewed = 0
    unlocked = 0

    for lesson in all_lessons:
        lesson_id = lesson["id"]
        if is_lesson_complete(lesson_id):
            completed += 1
        if has_passed_lesson_review(lesson_id):
            reviewed += 1
        if is_lesson_unlocked(lesson_id):
            unlocked += 1

    return {
        "total": len(all_lessons),
        "completed": completed,
        "reviewed": reviewed,
        "unlocked": unlocked,
        "weak_topics": len(progress_data.get("weak_topics", {})),
    }


def get_next_recommended_lesson() -> Optional[LessonData]:
    for lesson in get_all_lessons():
        if is_lesson_unlocked(lesson["id"]) and not is_lesson_complete(lesson["id"]):
            return lesson
    return None


def open_lesson(lesson_id: str) -> None:
    if not is_lesson_unlocked(lesson_id):
        st.warning(get_locked_reason(lesson_id))
        return

    st.session_state["selected_lesson_id"] = lesson_id
    st.rerun()


def close_lesson() -> None:
    st.session_state["selected_lesson_id"] = None
    st.rerun()


def load_starter_code(lesson_id: str, starter_code: str) -> None:
    st.session_state[f"lesson_editor_{lesson_id}"] = starter_code
    st.rerun()


def send_to_review(lesson_id: str, code: str) -> None:
    st.session_state["review_target_type"] = "lesson"
    st.session_state["review_target_id"] = lesson_id
    st.session_state["review_target_code"] = code
    st.session_state["selected_mode"] = "Review Mode"
    st.rerun()


def complete_lesson(lesson_id: str) -> None:
    mark_lesson_complete(lesson_id)
    st.success("Lesson completed.")
    st.session_state["selected_lesson_id"] = None
    st.rerun()


def render_skill_path() -> None:
    st.markdown("### Skill Path")

    for node in get_skill_tree():
        lesson_id = str(node["id"])

        if is_lesson_complete(lesson_id):
            status = "✅ Complete"
        elif has_passed_lesson_review(lesson_id):
            status = "🟢 Reviewed"
        elif is_lesson_unlocked(lesson_id):
            status = "🟡 Unlocked"
        else:
            status = "🔒 Locked"

        unlocks = node.get("unlocks", [])
        unlock_text = ", ".join(str(item) for item in unlocks) if unlocks else "Final node"

        st.markdown(
            f"""
            <div style="
                border: 1px solid rgba(148, 163, 184, 0.20);
                border-radius: 14px;
                padding: 0.8rem;
                background: white;
                margin-bottom: 0.6rem;
            ">
                <strong>{node["title"]}</strong> — {status}<br>
                <span style="color: rgb(71, 85, 105);">{node["description"]}</span><br>
                <span style="color: rgb(71, 85, 105);">Unlocks: {unlock_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_catalog_card(lesson: LessonData) -> None:
    lesson_id = lesson["id"]
    completed = is_lesson_complete(lesson_id)
    review_passed = has_passed_lesson_review(lesson_id)
    unlocked = is_lesson_unlocked(lesson_id)

    if completed:
        badge = "✅ Complete"
    elif review_passed:
        badge = "🟢 Review Passed"
    elif unlocked:
        badge = "🟡 Unlocked"
    else:
        badge = "🔒 Locked"

    meta_parts = [
        f"Track: {lesson['track']}",
        f"Duration: {lesson['duration']}",
        f"Reward: {lesson['xp_reward']} XP",
    ]

    if not unlocked:
        meta_parts.append(get_locked_reason(lesson_id))

    content_card(
        title=lesson["title"],
        body=lesson["summary"],
        meta="<br>".join(meta_parts),
        badge=badge,
        min_height=210,
    )

    action_row(
        [
            make_button(
                label=f"Open {lesson['title']}",
                key=f"lesson_open_{lesson_id}",
                action=lambda selected_id=lesson_id: open_lesson(selected_id),
                disabled=not unlocked,
            )
        ]
    )


def render_catalog(progress_data: Dict[str, Any]) -> None:
    summary = get_summary(progress_data)
    next_lesson = get_next_recommended_lesson()

    mode_header(
        "Course Mode",
        "Work through structured Python lessons and unlock the next lesson by completing the previous one.",
        "📘",
    )

    metric_row(
        [
            ("Lessons", summary["total"]),
            ("Unlocked", summary["unlocked"]),
            ("Reviewed", summary["reviewed"]),
            ("Completed", summary["completed"]),
        ]
    )

    if next_lesson is not None:
        st.info(f"Recommended next lesson: {next_lesson['title']}")

    left_col, right_col = st.columns([2, 1])

    with left_col:
        for track_name, track_lessons in LESSONS.items():
            st.markdown(f"### {track_name}")

            col1, col2 = st.columns(2)
            for index, lesson in enumerate(track_lessons):
                target_col = col1 if index % 2 == 0 else col2
                with target_col:
                    render_catalog_card(lesson)

    with right_col:
        render_skill_path()


def render_lesson_content(lesson: LessonData) -> str:
    st.markdown("### What You’ll Learn")
    st.write(lesson["concept"])

    st.markdown("### Example")
    st.code(lesson["example"], language="python")

    st.markdown("### Your Task")
    st.write(lesson["task"])

    st.markdown("### Success Checklist")
    bullet_list(
        [
            "Read the example carefully",
            "Write a working solution",
            "Send it to review",
            "Pass review before completing the lesson",
        ]
    )

    editor_key = f"lesson_editor_{lesson['id']}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = lesson["starter_code"]

    user_code = st.text_area(
        "Your Code",
        value=st.session_state[editor_key],
        height=240,
        key=f"{editor_key}_widget",
    )
    st.session_state[editor_key] = user_code
    return user_code


def render_lesson_actions(lesson: LessonData, user_code: str) -> None:
    action_row(
        [
            make_button(
                label="Load Starter Code",
                key=f"lesson_starter_{lesson['id']}",
                action=lambda lesson_id=lesson["id"], starter=lesson["starter_code"]: load_starter_code(lesson_id, starter),
            ),
            make_button(
                label="Send to Review",
                key=f"lesson_review_{lesson['id']}",
                action=lambda lesson_id=lesson["id"], code=user_code: send_to_review(lesson_id, code),
            ),
        ]
    )


def render_completion_section(lesson: LessonData) -> None:
    lesson_id = lesson["id"]
    completed = is_lesson_complete(lesson_id)
    review_passed = has_passed_lesson_review(lesson_id)

    st.markdown("### Completion")

    if review_passed:
        st.success(f"Review passed. Completing this lesson awards {lesson['xp_reward']} XP.")
    else:
        st.info("Pass review to complete this lesson.")

    action_row(
        [
            make_button(
                label="Mark Complete",
                key=f"lesson_complete_{lesson_id}",
                action=lambda selected_id=lesson_id: complete_lesson(selected_id),
                disabled=(not review_passed) or completed,
            ),
            make_button(
                label="Back to Lessons",
                key=f"lesson_back_{lesson_id}",
                action=close_lesson,
            ),
        ]
    )


def render_lesson_detail(_: Dict[str, Any], lesson_id: str) -> None:
    lesson = find_lesson(lesson_id)

    if lesson is None:
        st.error("Lesson not found.")
        return

    if not is_lesson_unlocked(lesson_id):
        st.warning(get_locked_reason(lesson_id))
        close_lesson()
        return

    mode_header(
        lesson["title"],
        lesson["summary"],
        "📚",
    )

    metric_row(
        [
            ("Track", lesson["track"]),
            ("Duration", lesson["duration"]),
            ("Reward", f"{lesson['xp_reward']} XP"),
            ("Reviewed", "Yes" if has_passed_lesson_review(lesson_id) else "No"),
        ]
    )

    user_code = render_lesson_content(lesson)
    render_lesson_actions(lesson, user_code)
    render_completion_section(lesson)


def render(progress_data: Dict[str, Any]) -> None:
    selected_lesson = st.session_state.get("selected_lesson_id")

    if selected_lesson:
        render_lesson_detail(progress_data, str(selected_lesson))
        return

    render_catalog(progress_data)
