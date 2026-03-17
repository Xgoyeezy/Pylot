from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, TypedDict


class DailyQuest(TypedDict):
    id: str
    title: str
    description: str
    mode: str
    reward_xp: int
    hint: str


class SkillNode(TypedDict):
    id: str
    title: str
    track: str
    description: str
    unlocks: List[str]


QUEST_LIBRARY: List[DailyQuest] = [
    {
        "id": "quest-variables",
        "title": "Foundation Step",
        "description": "Complete a short lesson or exercise about variables.",
        "mode": "Course Mode",
        "reward_xp": 25,
        "hint": "Start with the first lesson if you are early in the course.",
    },
    {
        "id": "quest-practice",
        "title": "Practice Push",
        "description": "Answer one practice question and review why the answer works.",
        "mode": "Practice Mode",
        "reward_xp": 25,
        "hint": "Use Practice Mode to strengthen one weak topic.",
    },
    {
        "id": "quest-project",
        "title": "Builder Move",
        "description": "Open a project and make one meaningful improvement.",
        "mode": "Project Mode",
        "reward_xp": 35,
        "hint": "Focus on functions, cleaner output, or more complete logic.",
    },
    {
        "id": "quest-debug",
        "title": "Bug Hunt",
        "description": "Paste broken code into Debug Mode and identify the main issue.",
        "mode": "Debug Mode",
        "reward_xp": 30,
        "hint": "Include the traceback if you have it.",
    },
    {
        "id": "quest-explain",
        "title": "Explain It Back",
        "description": "Use Explain Mode to understand a concept or code sample more clearly.",
        "mode": "Explain Mode",
        "reward_xp": 20,
        "hint": "Ask what each line does and why it matters.",
    },
    {
        "id": "quest-ai",
        "title": "Mentor Check-In",
        "description": "Ask the AI tutor one focused Python question.",
        "mode": "AI Mode",
        "reward_xp": 20,
        "hint": "Use a specific question for stronger help.",
    },
    {
        "id": "quest-arena",
        "title": "Arena Pulse",
        "description": "Enter Code Arena and clear one challenge.",
        "mode": "Code Arena",
        "reward_xp": 30,
        "hint": "Fast, correct solutions help you climb the ladder.",
    },
]


SKILL_TREE: List[SkillNode] = [
    {
        "id": "variables",
        "title": "Variables",
        "track": "Python Foundations",
        "description": "Store values and reuse them in code.",
        "unlocks": ["conditionals"],
    },
    {
        "id": "conditionals",
        "title": "Conditionals",
        "track": "Python Foundations",
        "description": "Make decisions with if, elif, and else.",
        "unlocks": ["loops"],
    },
    {
        "id": "loops",
        "title": "Loops",
        "track": "Python Foundations",
        "description": "Repeat actions efficiently with iteration.",
        "unlocks": ["functions"],
    },
    {
        "id": "functions",
        "title": "Functions",
        "track": "Python Foundations",
        "description": "Organize reusable logic into callable blocks.",
        "unlocks": ["projects"],
    },
    {
        "id": "projects",
        "title": "Projects",
        "track": "Build by Doing",
        "description": "Apply core concepts in larger real tasks.",
        "unlocks": ["debugging", "arena"],
    },
    {
        "id": "debugging",
        "title": "Debugging",
        "track": "Developer Skills",
        "description": "Find, understand, and fix Python errors.",
        "unlocks": ["review"],
    },
    {
        "id": "arena",
        "title": "Code Arena",
        "track": "Competitive Learning",
        "description": "Solve timed challenges and improve under pressure.",
        "unlocks": ["review"],
    },
    {
        "id": "review",
        "title": "Code Review",
        "track": "Developer Skills",
        "description": "Refine code quality, clarity, and correctness.",
        "unlocks": [],
    },
]


def get_daily_quest() -> DailyQuest:
    index = date.today().toordinal() % len(QUEST_LIBRARY)
    return QUEST_LIBRARY[index]


def get_skill_tree() -> List[SkillNode]:
    return SKILL_TREE


def get_shock_feature_cards() -> List[Dict[str, Any]]:
    return [
        {
            "title": "Live Code Battles",
            "body": "Head-to-head Python challenges with AI-style pressure, timed wins, and competitive replay value.",
            "badge": "Shock Feature",
        },
        {
            "title": "AI Code Coach",
            "body": "A future live mentor layer that watches your coding flow and nudges you before mistakes compound.",
            "badge": "Adaptive AI",
        },
        {
            "title": "Portfolio Builder",
            "body": "Projects that can evolve into GitHub-ready artifacts with clearer structure and skill proof.",
            "badge": "Career Value",
        },
    ]


def get_code_arena_preview() -> Dict[str, Any]:
    return {
        "title": "Code Arena Preview",
        "challenge": "Write the cleanest function to return the largest number in a list.",
        "user_goal": "Beat the AI on readability, correctness, and speed.",
        "ai_style": "Fast, compact, Pythonic",
        "reward": 50,
    }


def get_career_paths() -> List[Dict[str, Any]]:
    return [
        {
            "id": "python-developer",
            "title": "Python Developer",
            "description": "Core Python, debugging, projects, and code quality.",
            "focus": ["variables", "conditionals", "loops", "functions", "projects", "debugging", "review"],
        },
        {
            "id": "automation-engineer",
            "title": "Automation Engineer",
            "description": "Python for scripts, repeatable workflows, and practical problem solving.",
            "focus": ["variables", "loops", "functions", "projects", "debugging"],
        },
        {
            "id": "competitive-python",
            "title": "Competitive Python",
            "description": "Sharpen correctness and speed through challenge-driven practice.",
            "focus": ["loops", "functions", "arena", "review"],
        },
    ]
