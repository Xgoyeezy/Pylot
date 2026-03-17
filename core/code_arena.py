from __future__ import annotations

import contextlib
import io
import time
import traceback
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

import streamlit as st

from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header
from progress import (
    add_xp,
    can_claim_daily_arena_mission,
    get_learning_profile,
    mark_daily_arena_mission_claimed,
    record_arena_win,
)


@dataclass(frozen=True)
class ArenaChallenge:
    challenge_id: str
    title: str
    description: str
    starter_code: str
    tests: List[Dict[str, Any]]
    reward_xp: int
    rank_points: int
    ai_benchmark_seconds: float
    hint: str
    ai_style_notes: List[str]
    difficulty: str


CHALLENGES: List[ArenaChallenge] = [
    ArenaChallenge(
        challenge_id="reverse_string",
        title="Reverse a String",
        description="Write a function called reverse_string that returns a reversed string.",
        starter_code=(
            "def reverse_string(text):\n"
            "    # return the reversed text\n"
            "    pass\n"
        ),
        tests=[
            {"call": 'reverse_string("python")', "expected": "nohtyp"},
            {"call": 'reverse_string("abc")', "expected": "cba"},
            {"call": 'reverse_string("")', "expected": ""},
        ],
        reward_xp=40,
        rank_points=25,
        ai_benchmark_seconds=8.0,
        hint="String slicing can help.",
        ai_style_notes=[
            "The AI would likely use slicing for a compact solution.",
            "The AI benchmark favors short, correct, Pythonic code.",
        ],
        difficulty="Bronze",
    ),
    ArenaChallenge(
        challenge_id="sum_list",
        title="Sum a List",
        description="Write a function called sum_list that returns the sum of all numbers in a list.",
        starter_code=(
            "def sum_list(numbers):\n"
            "    # return the total\n"
            "    pass\n"
        ),
        tests=[
            {"call": "sum_list([1, 2, 3, 4])", "expected": 10},
            {"call": "sum_list([5, 5, 5])", "expected": 15},
            {"call": "sum_list([])", "expected": 0},
        ],
        reward_xp=40,
        rank_points=25,
        ai_benchmark_seconds=10.0,
        hint="You can loop or use a built-in.",
        ai_style_notes=[
            "The AI would likely use sum(numbers).",
            "A readable loop can still compete well if it is clean and correct.",
        ],
        difficulty="Bronze",
    ),
    ArenaChallenge(
        challenge_id="count_evens",
        title="Count Evens",
        description="Write a function called count_evens that returns how many even numbers are in a list.",
        starter_code=(
            "def count_evens(numbers):\n"
            "    # return the number of even values\n"
            "    pass\n"
        ),
        tests=[
            {"call": "count_evens([1, 2, 3, 4, 5, 6])", "expected": 3},
            {"call": "count_evens([1, 3, 5])", "expected": 0},
            {"call": "count_evens([2, 4, 6])", "expected": 3},
        ],
        reward_xp=50,
        rank_points=30,
        ai_benchmark_seconds=12.0,
        hint="Check each value with modulo `% 2`.",
        ai_style_notes=[
            "The AI would likely use a loop or generator expression.",
            "Clear naming and correct condition checks matter here.",
        ],
        difficulty="Silver",
    ),
]


def _init_state() -> None:
    defaults = {
        "arena_selected": None,
        "arena_code": "",
        "arena_feedback": None,
        "arena_start_time": None,
        "arena_rewarded_ids": [],
        "arena_rank_rewarded_ids": [],
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _get_challenge(challenge_id: str) -> Optional[ArenaChallenge]:
    for challenge in CHALLENGES:
        if challenge.challenge_id == challenge_id:
            return challenge
    return None


def _get_daily_arena_mission() -> Dict[str, Any]:
    mission_types = [
        {
            "title": "Arena Sprint",
            "description": "Clear one arena challenge today.",
            "reward_xp": 20,
            "hint": "Any completed arena win counts.",
        },
        {
            "title": "Speed Duel",
            "description": "Beat the AI benchmark on one challenge.",
            "reward_xp": 30,
            "hint": "Compact solutions tend to help.",
        },
        {
            "title": "Clean Win",
            "description": "Clear a challenge with no runtime errors.",
            "reward_xp": 20,
            "hint": "Start with correctness first.",
        },
    ]
    index = date.today().toordinal() % len(mission_types)
    return mission_types[index]


def _open_challenge(challenge: ArenaChallenge) -> None:
    st.session_state["arena_selected"] = challenge.challenge_id
    st.session_state["arena_code"] = challenge.starter_code
    st.session_state["arena_feedback"] = None
    st.session_state["arena_start_time"] = time.time()
    st.rerun()


def _close_challenge() -> None:
    st.session_state["arena_selected"] = None
    st.session_state["arena_feedback"] = None
    st.session_state["arena_start_time"] = None
    st.rerun()


def _reset_code(challenge: ArenaChallenge) -> None:
    st.session_state["arena_code"] = challenge.starter_code
    st.session_state["arena_feedback"] = None
    st.session_state["arena_start_time"] = time.time()
    st.rerun()


def _count_non_empty_lines(code: str) -> int:
    return len([line for line in code.splitlines() if line.strip()])


def _build_battle_summary(
    challenge: ArenaChallenge,
    user_code: str,
    passed_all: bool,
    elapsed_seconds: float | None,
) -> Dict[str, str]:
    user_lines = _count_non_empty_lines(user_code)
    ai_time = challenge.ai_benchmark_seconds

    if not passed_all:
        return {
            "winner": "AI",
            "correctness": "AI wins correctness because your solution did not pass all tests yet.",
            "speed": "Speed comparison is secondary until correctness is achieved.",
            "style": "Focus on making the solution complete and readable first.",
        }

    if elapsed_seconds is None:
        elapsed_seconds = ai_time + 1.0

    if elapsed_seconds <= ai_time:
        speed_text = f"You beat the AI benchmark on time ({elapsed_seconds:.1f}s vs {ai_time:.1f}s)."
        speed_winner = "You"
    else:
        speed_text = f"The AI benchmark was faster ({ai_time:.1f}s vs {elapsed_seconds:.1f}s)."
        speed_winner = "AI"

    if user_lines <= 4:
        style_text = "Your solution is compact and competitive on simplicity."
        style_winner = "You"
    elif user_lines <= 8:
        style_text = "Your solution has a balanced level of detail and readability."
        style_winner = "Tie"
    else:
        style_text = "Your solution works, but the AI would likely produce a shorter version."
        style_winner = "AI"

    if speed_winner == "You" and style_winner in {"You", "Tie"}:
        winner = "You"
    elif speed_winner == "AI" and style_winner == "AI":
        winner = "AI"
    else:
        winner = "Tie"

    return {
        "winner": winner,
        "correctness": "You matched the AI on correctness by passing all arena tests.",
        "speed": speed_text,
        "style": style_text,
    }


def _claim_daily_arena_mission() -> None:
    if not can_claim_daily_arena_mission():
        st.warning("Daily arena mission already claimed today.")
        return

    mission = _get_daily_arena_mission()
    add_xp(int(mission["reward_xp"]))
    mark_daily_arena_mission_claimed()
    st.success(f"Daily arena mission reward claimed: +{mission['reward_xp']} XP")
    st.rerun()


def _run_and_check(challenge: ArenaChallenge) -> None:
    user_code = st.session_state.get("arena_code", "")
    namespace: Dict[str, Any] = {}

    stdout_buffer = io.StringIO()
    elapsed_seconds = None
    if st.session_state.get("arena_start_time") is not None:
        elapsed_seconds = max(0.0, time.time() - float(st.session_state["arena_start_time"]))

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(user_code, namespace, namespace)

        test_results: List[Dict[str, Any]] = []
        passed_all = True

        for test in challenge.tests:
            result = eval(test["call"], namespace, namespace)
            passed = result == test["expected"]
            test_results.append(
                {
                    "call": test["call"],
                    "expected": test["expected"],
                    "actual": result,
                    "passed": passed,
                }
            )
            if not passed:
                passed_all = False

        reward_given = False
        rewarded_ids = list(st.session_state.get("arena_rewarded_ids", []))
        if passed_all and challenge.challenge_id not in rewarded_ids:
            add_xp(challenge.reward_xp)
            rewarded_ids.append(challenge.challenge_id)
            st.session_state["arena_rewarded_ids"] = rewarded_ids
            reward_given = True

        rank_points_given = False
        rank_rewarded_ids = list(st.session_state.get("arena_rank_rewarded_ids", []))
        if passed_all and challenge.challenge_id not in rank_rewarded_ids:
            record_arena_win(challenge.rank_points)
            rank_rewarded_ids.append(challenge.challenge_id)
            st.session_state["arena_rank_rewarded_ids"] = rank_rewarded_ids
            rank_points_given = True

        battle_summary = _build_battle_summary(
            challenge=challenge,
            user_code=user_code,
            passed_all=passed_all,
            elapsed_seconds=elapsed_seconds,
        )

        st.session_state["arena_feedback"] = {
            "passed_all": passed_all,
            "tests": test_results,
            "stdout": stdout_buffer.getvalue(),
            "error": "",
            "elapsed_seconds": elapsed_seconds,
            "reward_given": reward_given,
            "rank_points_given": rank_points_given,
            "battle_summary": battle_summary,
            "user_line_count": _count_non_empty_lines(user_code),
            "beat_ai_time": (
                passed_all
                and elapsed_seconds is not None
                and elapsed_seconds <= challenge.ai_benchmark_seconds
            ),
        }

    except Exception:
        st.session_state["arena_feedback"] = {
            "passed_all": False,
            "tests": [],
            "stdout": stdout_buffer.getvalue(),
            "error": traceback.format_exc(),
            "elapsed_seconds": elapsed_seconds,
            "reward_given": False,
            "rank_points_given": False,
            "battle_summary": {
                "winner": "AI",
                "correctness": "Your code raised an error before passing the arena tests.",
                "speed": "The AI wins by default until your code runs cleanly.",
                "style": "Fix the runtime issue first, then refine the solution.",
            },
            "user_line_count": _count_non_empty_lines(user_code),
            "beat_ai_time": False,
        }

    st.rerun()


def _render_rank_panel() -> None:
    profile = get_learning_profile()

    st.markdown("### Arena Rank")
    metric_row(
        [
            ("Rank", profile.get("arena_rank", "Bronze")),
            ("Arena Score", profile.get("arena_score", 0)),
            ("Arena Wins", profile.get("arena_wins", 0)),
            ("Win Streak", profile.get("arena_win_streak", 0)),
        ]
    )

    st.caption(f"Best arena streak: {profile.get('best_arena_win_streak', 0)}")

    bullet_list(
        [
            "Bronze: 0+",
            "Silver: 80+",
            "Gold: 180+",
            "Python Slayer: 300+",
        ]
    )


def _render_daily_mission_panel() -> None:
    mission = _get_daily_arena_mission()

    st.markdown("### Daily Arena Mission")
    content_card(
        title=mission["title"],
        body=mission["description"],
        meta=f"Hint: {mission['hint']}",
        badge=f"+{mission['reward_xp']} XP",
        min_height=140,
    )

    action_row(
        [
            make_button(
                label="Claim Arena Mission Reward",
                key="arena_claim_daily_mission",
                action=_claim_daily_arena_mission,
                disabled=not can_claim_daily_arena_mission(),
            )
        ]
    )


def _render_catalog() -> None:
    mode_header(
        "Code Arena",
        "Solve timed coding challenges, compare yourself against an AI benchmark, and climb the ranks.",
        "⚔️",
    )

    metric_row(
        [
            ("Challenges", len(CHALLENGES)),
            ("Mode", "Timed"),
            ("Rewards", "XP + Rank"),
            ("Style", "AI Battle"),
        ]
    )

    _render_rank_panel()
    _render_daily_mission_panel()

    bullet_list(
        [
            "Pick a challenge",
            "Write a working solution",
            "Run the arena tests",
            "Win rank points and move up the ladder",
        ]
    )

    for challenge in CHALLENGES:
        content_card(
            title=challenge.title,
            body=challenge.description,
            meta=(
                f"Difficulty: {challenge.difficulty}<br>"
                f"Reward: {challenge.reward_xp} XP<br>"
                f"Rank points: {challenge.rank_points}<br>"
                f"AI benchmark: {challenge.ai_benchmark_seconds:.1f}s"
            ),
            badge="⚔️",
            min_height=220,
        )
        st.caption(f"Hint: {challenge.hint}")

        action_row(
            [
                make_button(
                    label="Start Challenge",
                    key=f"arena_start_{challenge.challenge_id}",
                    action=lambda c=challenge: _open_challenge(c),
                )
            ]
        )


def _render_test_results(feedback: Dict[str, Any]) -> None:
    tests = feedback.get("tests", [])
    if tests:
        st.markdown("### Test Results")
        for test in tests:
            if test["passed"]:
                st.success(f'{test["call"]} -> {test["actual"]}')
            else:
                st.error(
                    f'{test["call"]} -> got {test["actual"]}, expected {test["expected"]}'
                )

    if feedback.get("stdout"):
        st.markdown("### Program Output")
        st.code(feedback["stdout"], language="text")

    if feedback.get("error"):
        st.markdown("### Error")
        st.code(feedback["error"], language="text")


def _render_battle_summary(challenge: ArenaChallenge, feedback: Dict[str, Any]) -> None:
    summary = feedback.get("battle_summary")
    if not summary:
        return

    st.markdown("### AI Battle Result")

    winner = summary.get("winner", "Tie")
    if winner == "You":
        st.success("Winner: You")
    elif winner == "AI":
        st.warning("Winner: AI")
    else:
        st.info("Winner: Tie")

    metric_row(
        [
            ("Your Lines", feedback.get("user_line_count", 0)),
            ("AI Benchmark", f"{challenge.ai_benchmark_seconds:.1f}s"),
            (
                "Your Time",
                f'{feedback["elapsed_seconds"]:.1f}s'
                if feedback.get("elapsed_seconds") is not None
                else "n/a",
            ),
        ]
    )

    bullet_list(
        [
            summary.get("correctness", ""),
            summary.get("speed", ""),
            summary.get("style", ""),
        ]
    )

    st.markdown("### AI Style Notes")
    bullet_list(challenge.ai_style_notes)


def _render_challenge(challenge: ArenaChallenge) -> None:
    profile = get_learning_profile()

    mode_header(
        challenge.title,
        challenge.description,
        "⚔️",
    )

    elapsed = 0
    if st.session_state.get("arena_start_time") is not None:
        elapsed = int(time.time() - float(st.session_state["arena_start_time"]))

    metric_row(
        [
            ("Reward", f"{challenge.reward_xp} XP"),
            ("AI Benchmark", f"{challenge.ai_benchmark_seconds:.1f}s"),
            ("Your Time", f"{elapsed}s"),
            ("Rank", profile.get("arena_rank", "Bronze")),
        ]
    )

    st.caption(f"Hint: {challenge.hint}")
    st.caption(
        f"Arena streak: {profile.get('arena_win_streak', 0)} • "
        f"Best streak: {profile.get('best_arena_win_streak', 0)}"
    )

    with st.expander("Show test targets", expanded=False):
        for test in challenge.tests:
            st.code(f'{test["call"]}  # expected -> {test["expected"]}', language="python")

    st.session_state["arena_code"] = st.text_area(
        "Your Code",
        value=st.session_state.get("arena_code", ""),
        height=320,
        key="arena_code_editor",
    )

    action_row(
        [
            make_button(
                label="Run Arena Tests",
                key="arena_run_tests",
                action=lambda: _run_and_check(challenge),
            ),
            make_button(
                label="Reset Code",
                key="arena_reset_code",
                action=lambda: _reset_code(challenge),
            ),
            make_button(
                label="Back",
                key="arena_back",
                action=_close_challenge,
            ),
        ]
    )

    feedback = st.session_state.get("arena_feedback")
    if not feedback:
        return

    if feedback.get("passed_all"):
        elapsed_seconds = feedback.get("elapsed_seconds")
        elapsed_text = "time unavailable" if elapsed_seconds is None else f"{elapsed_seconds:.1f}s"

        if feedback.get("reward_given"):
            st.success(
                f"Challenge cleared. You finished in {elapsed_text} and earned {challenge.reward_xp} XP."
            )
        else:
            st.success(f"Challenge cleared. You finished in {elapsed_text}.")

        if feedback.get("rank_points_given"):
            st.success(f"Arena rank points earned: +{challenge.rank_points}")

        if feedback.get("beat_ai_time"):
            st.success("You beat the AI benchmark time.")
    else:
        st.warning("Challenge not cleared yet. Review the failed tests or error output.")

    _render_battle_summary(challenge, feedback)
    _render_test_results(feedback)


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data
    _init_state()

    selected_id = st.session_state.get("arena_selected")
    if selected_id:
        challenge = _get_challenge(selected_id)
        if challenge is not None:
            _render_challenge(challenge)
            return

    _render_catalog()
