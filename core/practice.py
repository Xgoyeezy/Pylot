from __future__ import annotations

from typing import Any, Dict, List, Tuple, TypedDict

import streamlit as st

from core.engagement import get_daily_quest
from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header
from progress import add_xp, can_claim_daily_quest, mark_daily_quest_claimed, update_weak_topics


class PracticeExercise(TypedDict):
    topic: str
    title: str
    prompt: str
    starter_code: str
    checks: List[str]
    reward_xp: int
    hint: str


PRACTICE_LIBRARY: Dict[str, PracticeExercise] = {
    "functions": {
        "topic": "functions",
        "title": "Function Practice",
        "prompt": "Write a function called `double_number` that takes a number and returns double it.",
        "starter_code": (
            "def double_number(number):\n"
            "    # return double the number\n"
            "    pass\n\n"
            "print(double_number(4))"
        ),
        "checks": ["def ", "return"],
        "reward_xp": 15,
        "hint": "A function usually needs both `def` and `return` here.",
    },
    "loops": {
        "topic": "loops",
        "title": "Loop Practice",
        "prompt": "Use a loop to print each item in a list of three fruits.",
        "starter_code": (
            'fruits = ["apple", "banana", "orange"]\n\n'
            "# write your loop here"
        ),
        "checks": ["for ", "print("],
        "reward_xp": 15,
        "hint": "Loop through the list, then print each item inside the loop.",
    },
    "conditionals": {
        "topic": "conditionals",
        "title": "Conditional Practice",
        "prompt": "Write code that prints `big` if `number` is greater than 10, otherwise prints `small`.",
        "starter_code": (
            "number = 12\n\n"
            "# write your conditional here"
        ),
        "checks": ["if ", "print("],
        "reward_xp": 15,
        "hint": "Use `if` for the condition and `else` for the other case.",
    },
    "lists": {
        "topic": "lists",
        "title": "List Practice",
        "prompt": "Create a list of three numbers and print the second item.",
        "starter_code": (
            "# create your list here\n"
            "# print the second item"
        ),
        "checks": ["[", "]", "print("],
        "reward_xp": 15,
        "hint": "Lists use square brackets, and the second item is usually index 1.",
    },
    "general": {
        "topic": "general",
        "title": "General Python Practice",
        "prompt": "Create a variable called `name` and print a greeting using it.",
        "starter_code": (
            'name = "Marc"\n'
            'print(f"Hello, {name}")'
        ),
        "checks": ["print("],
        "reward_xp": 10,
        "hint": "Start simple. Make one variable and print something useful.",
    },
}


def get_top_weak_topic(weak_topics: Dict[str, int]) -> str:
    if not weak_topics:
        return "general"

    sorted_topics = sorted(
        weak_topics.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    return sorted_topics[0][0]


def get_practice_exercise(weak_topics: Dict[str, int]) -> PracticeExercise:
    top_topic = get_top_weak_topic(weak_topics)
    return PRACTICE_LIBRARY.get(top_topic, PRACTICE_LIBRARY["general"])


def review_practice_submission(user_code: str, exercise: PracticeExercise) -> Tuple[bool, str, List[str]]:
    if not user_code.strip():
        return False, "Write some code before submitting.", [exercise["topic"]]

    missing_tokens: List[str] = []
    for token in exercise.get("checks", []):
        if token not in user_code:
            missing_tokens.append(token)

    if not missing_tokens:
        return True, "Nice work. Your solution includes the main required pieces.", []

    token_map = {
        "def ": "a function definition",
        "return": "a return statement",
        "for ": "a loop",
        "if ": "a conditional",
        "print(": "printed output",
        "[": "a list",
        "]": "a list value",
    }

    readable_missing = [token_map.get(token, token) for token in missing_tokens]
    return (
        False,
        "Your solution is missing some expected parts: " + ", ".join(readable_missing),
        [exercise["topic"]],
    )


def clear_practice_feedback() -> None:
    st.session_state["practice_feedback"] = ""
    st.session_state["practice_passed"] = None


def _set_editor_for_exercise(exercise: PracticeExercise) -> None:
    st.session_state["practice_current_topic"] = exercise["topic"]
    st.session_state["practice_editor_value"] = exercise["starter_code"]


def load_starter_code(starter_code: str) -> None:
    st.session_state["practice_editor_value"] = starter_code
    clear_practice_feedback()
    st.rerun()


def submit_practice(progress_data: Dict[str, Any], exercise: PracticeExercise, user_code: str) -> None:
    passed, feedback, missed_topics = review_practice_submission(user_code, exercise)

    if passed:
        update_weak_topics([exercise["topic"]], success=True)
        add_xp(exercise["reward_xp"])
    else:
        update_weak_topics(missed_topics, success=False)

    st.session_state["practice_feedback"] = feedback
    st.session_state["practice_passed"] = passed
    st.session_state["progress_data"] = progress_data
    st.rerun()


def claim_practice_daily_quest() -> None:
    quest = get_daily_quest()

    if quest["mode"] != "Practice Mode":
        st.warning("Today's quest is tied to a different mode.")
        return

    if not can_claim_daily_quest():
        st.warning("Daily quest already claimed today.")
        return

    add_xp(int(quest["reward_xp"]))
    mark_daily_quest_claimed()
    st.success(f"Daily quest reward claimed: +{quest['reward_xp']} XP")
    st.rerun()


def render_feedback() -> None:
    feedback = st.session_state.get("practice_feedback", "")
    passed = st.session_state.get("practice_passed")

    if not feedback:
        return

    st.markdown("### Feedback")
    if passed is True:
        st.success(feedback)
    elif passed is False:
        st.warning(feedback)


def render_daily_quest_panel() -> None:
    quest = get_daily_quest()
    if quest["mode"] != "Practice Mode":
        return

    st.markdown("### Today's Practice Quest")
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
                key="practice_claim_daily_quest",
                action=claim_practice_daily_quest,
                disabled=not can_claim_daily_quest(),
            )
        ]
    )


def render_focus_guidance(focus_topic: str) -> None:
    st.markdown("### Focus Guidance")

    guidance_map = {
        "functions": [
            "Use `def` to create the function",
            "Return a value instead of only printing",
            "Call the function to test it",
        ],
        "loops": [
            "Use a `for` loop for repeating over items",
            "Print inside the loop body",
            "Keep indentation consistent",
        ],
        "conditionals": [
            "Use `if` to test the condition",
            "Add `else` when two outcomes are needed",
            "Print the result clearly",
        ],
        "lists": [
            "Create the list with square brackets",
            "Use an index like `[1]` for the second item",
            "Print the selected value",
        ],
        "general": [
            "Write a small working solution first",
            "Prefer clear variable names",
            "Print the result so you can verify it",
        ],
    }

    bullet_list(guidance_map.get(focus_topic, guidance_map["general"]))


def render(progress_data: Dict[str, Any]) -> None:
    weak_topics = progress_data.get("weak_topics", {})
    exercise = get_practice_exercise(weak_topics)
    focus_topic = exercise["topic"]

    mode_header(
        "Practice Mode",
        "Strengthen weak topics with targeted exercises and quick feedback.",
        "🎯",
    )

    metric_row(
        [
            ("Focus Topic", focus_topic),
            ("Weak Topics", len(weak_topics)),
            ("Reward", f"{exercise['reward_xp']} XP"),
            ("Checks", len(exercise["checks"])),
        ]
    )

    render_daily_quest_panel()

    content_card(
        title=exercise["title"],
        body=exercise["prompt"],
        meta=f"Hint: {exercise['hint']}",
        badge="Practice",
        min_height=150,
    )

    left_col, right_col = st.columns([2, 1])
    with left_col:
        bullet_list(
            [
                "Read the target prompt",
                "Write the shortest working solution you can",
                "Submit to get instant feedback",
                "Use practice to lower your weak-topic score",
            ]
        )
    with right_col:
        render_focus_guidance(focus_topic)

    current_topic = st.session_state.get("practice_current_topic")
    if current_topic != exercise["topic"] or "practice_editor_value" not in st.session_state:
        _set_editor_for_exercise(exercise)

    current_value = st.session_state.get("practice_editor_value", exercise["starter_code"])

    user_code = st.text_area(
        "Practice Code",
        value=current_value,
        height=240,
        key="practice_code_editor",
    )

    st.session_state["practice_editor_value"] = user_code

    action_row(
        [
            make_button(
                label="Load Starter Code",
                key="practice_load_starter",
                action=lambda: load_starter_code(exercise["starter_code"]),
            ),
            make_button(
                label="Submit Practice",
                key="practice_submit",
                action=lambda: submit_practice(progress_data, exercise, user_code),
            ),
        ]
    )

    render_feedback()
    st.caption(f"Current practice focus: {focus_topic}")
