from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.ui import bullet_list, content_card, metric_row, mode_header


DEMO_PROJECT: Dict[str, Any] = {
    "id": "number_guess",
    "title": "Number Guessing Game",
    "description": "Build a simple number guessing game using Python.",
    "difficulty": "Beginner",
    "estimated_time": "20–30 min",
    "skills": [
        "variables",
        "conditionals",
        "loops",
        "random module",
        "user input",
    ],
    "requirements": [
        "Generate a random number",
        "Ask the user to guess the number",
        "Tell the user if the guess is too high or too low",
        "Stop when the correct number is guessed",
    ],
    "milestones": [
        "Import random and generate the secret number",
        "Collect a guess from the user",
        "Compare the guess to the secret number",
        "Give too high / too low feedback",
        "Repeat until the user gets it right",
    ],
    "portfolio_value": [
        "Shows basic Python logic and flow control",
        "Demonstrates user interaction",
        "Can be upgraded into a replayable mini game",
    ],
    "starter_code": """import random

secret_number = random.randint(1, 10)

while True:
    guess = int(input("Guess the number: "))

    # compare the guess to the secret number
    # print whether it is too high, too low, or correct
    # stop the loop when the user guesses correctly
""",
    "upgrade_ideas": [
        "Add a guess counter",
        "Let the user choose the difficulty range",
        "Show the best score",
        "Ask if the user wants to play again",
    ],
}


def _render_overview() -> None:
    content_card(
        title=DEMO_PROJECT["title"],
        body=DEMO_PROJECT["description"],
        meta=(
            f"Difficulty: {DEMO_PROJECT['difficulty']}<br>"
            f"Estimated time: {DEMO_PROJECT['estimated_time']}"
        ),
        badge="Demo",
        min_height=160,
    )

    metric_row(
        [
            ("Difficulty", DEMO_PROJECT["difficulty"]),
            ("Time", DEMO_PROJECT["estimated_time"]),
            ("Skills", len(DEMO_PROJECT["skills"])),
            ("Milestones", len(DEMO_PROJECT["milestones"])),
        ]
    )


def _render_skills() -> None:
    st.markdown("### Skills You Practice")
    bullet_list(DEMO_PROJECT["skills"])


def _render_requirements() -> None:
    st.markdown("### Requirements")
    bullet_list(DEMO_PROJECT["requirements"])


def _render_milestones() -> None:
    st.markdown("### Build Milestones")
    bullet_list(DEMO_PROJECT["milestones"])


def _render_starter_code() -> None:
    st.markdown("### Starter Code")
    st.code(DEMO_PROJECT["starter_code"], language="python")

    st.info(
        "Copy this into Run/Test Mode or your local editor, then finish the game step by step."
    )


def _render_portfolio_value() -> None:
    st.markdown("### Why This Project Matters")
    bullet_list(DEMO_PROJECT["portfolio_value"])


def _render_upgrade_ideas() -> None:
    st.markdown("### Upgrade Ideas")
    bullet_list(DEMO_PROJECT["upgrade_ideas"])


def render(_: Dict[str, Any]) -> None:
    mode_header(
        "Demo Project",
        "Use this guided project to learn by building something real.",
        "🧪",
    )

    _render_overview()

    left_col, right_col = st.columns([2, 1])

    with left_col:
        _render_requirements()
        _render_milestones()
        _render_starter_code()

    with right_col:
        _render_skills()
        _render_portfolio_value()
        _render_upgrade_ideas()
