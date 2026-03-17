from __future__ import annotations

from typing import Any, Dict, List, TypedDict

import streamlit as st

from core.ui import action_row, bullet_list, content_card, make_button, metric_row, mode_header


class SettingOption(TypedDict):
    label: str
    value: str
    description: str


LEARNING_STYLE_OPTIONS: List[SettingOption] = [
    {
        "label": "Builder",
        "value": "builder",
        "description": "Learn best by making projects and applying concepts quickly.",
    },
    {
        "label": "Structured",
        "value": "structured",
        "description": "Prefer a step-by-step, lesson-first path.",
    },
    {
        "label": "Explainer",
        "value": "explainer",
        "description": "Prefer deeper explanations before practice.",
    },
    {
        "label": "Competitive",
        "value": "competitive",
        "description": "Prefer challenges, arena play, and visible progression.",
    },
]

DIFFICULTY_OPTIONS: List[SettingOption] = [
    {
        "label": "Easy Start",
        "value": "easy",
        "description": "Gentle pace with simpler practice and more guidance.",
    },
    {
        "label": "Balanced",
        "value": "balanced",
        "description": "Default pace with a mix of help and challenge.",
    },
    {
        "label": "Push Me",
        "value": "hard",
        "description": "Harder prompts, less hand-holding, faster progression.",
    },
]

SESSION_GOAL_OPTIONS: List[SettingOption] = [
    {
        "label": "10 Minutes",
        "value": "10",
        "description": "Quick daily progress.",
    },
    {
        "label": "20 Minutes",
        "value": "20",
        "description": "Balanced focused session.",
    },
    {
        "label": "30 Minutes",
        "value": "30",
        "description": "Longer learning block.",
    },
    {
        "label": "Deep Work",
        "value": "45+",
        "description": "Extended session for projects and debugging.",
    },
]

UI_DENSITY_OPTIONS: List[SettingOption] = [
    {
        "label": "Comfortable",
        "value": "comfortable",
        "description": "More spacing and easier reading.",
    },
    {
        "label": "Compact",
        "value": "compact",
        "description": "More content on screen at once.",
    },
]


def _init_state() -> None:
    defaults = {
        "settings_learning_style": "builder",
        "settings_difficulty": "balanced",
        "settings_session_goal": "20",
        "settings_ui_density": "comfortable",
        "settings_saved": False,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _get_option_by_value(options: List[SettingOption], value: str) -> SettingOption:
    for option in options:
        if option["value"] == value:
            return option
    return options[0]


def _save_settings() -> None:
    st.session_state["settings_saved"] = True
    st.success("Settings saved for this app session.")
    st.rerun()


def _reset_settings() -> None:
    st.session_state["settings_learning_style"] = "builder"
    st.session_state["settings_difficulty"] = "balanced"
    st.session_state["settings_session_goal"] = "20"
    st.session_state["settings_ui_density"] = "comfortable"
    st.session_state["settings_saved"] = False
    st.rerun()


def get_personalization_profile() -> Dict[str, str]:
    _init_state()
    return {
        "learning_style": st.session_state.get("settings_learning_style", "builder"),
        "difficulty": st.session_state.get("settings_difficulty", "balanced"),
        "session_goal": st.session_state.get("settings_session_goal", "20"),
        "ui_density": st.session_state.get("settings_ui_density", "comfortable"),
    }


def _render_option_group(
    title: str,
    key: str,
    options: List[SettingOption],
) -> None:
    st.markdown(f"### {title}")

    current_value = st.session_state.get(key, options[0]["value"])
    labels = [option["label"] for option in options]
    current_label = _get_option_by_value(options, current_value)["label"]
    current_index = labels.index(current_label)

    selected_label = st.radio(
        title,
        labels,
        index=current_index,
        key=f"{key}_selector",
        label_visibility="collapsed",
    )

    for option in options:
        if option["label"] == selected_label:
            st.session_state[key] = option["value"]
            st.caption(option["description"])
            break


def _style_map() -> Dict[str, str]:
    return {option["value"]: option["label"] for option in LEARNING_STYLE_OPTIONS}


def _difficulty_map() -> Dict[str, str]:
    return {option["value"]: option["label"] for option in DIFFICULTY_OPTIONS}


def _goal_map() -> Dict[str, str]:
    return {option["value"]: option["label"] for option in SESSION_GOAL_OPTIONS}


def _density_map() -> Dict[str, str]:
    return {option["value"]: option["label"] for option in UI_DENSITY_OPTIONS}


def _render_summary() -> None:
    profile = get_personalization_profile()

    style_map = _style_map()
    difficulty_map = _difficulty_map()
    goal_map = _goal_map()
    density_map = _density_map()

    st.markdown("### Current Profile")
    metric_row(
        [
            ("Style", style_map.get(profile["learning_style"], "Builder")),
            ("Difficulty", difficulty_map.get(profile["difficulty"], "Balanced")),
            ("Goal", goal_map.get(profile["session_goal"], "20 Minutes")),
            ("Density", density_map.get(profile["ui_density"], "Comfortable")),
        ]
    )

    bullet_list(
        [
            f"Learning style: {style_map.get(profile['learning_style'], 'Builder')}",
            f"Difficulty feel: {difficulty_map.get(profile['difficulty'], 'Balanced')}",
            f"Target session length: {goal_map.get(profile['session_goal'], '20 Minutes')}",
            f"UI density: {density_map.get(profile['ui_density'], 'Comfortable')}",
        ]
    )


def _render_personalized_effects() -> None:
    profile = get_personalization_profile()

    learning_style = profile["learning_style"]
    difficulty = profile["difficulty"]
    session_goal = profile["session_goal"]
    ui_density = profile["ui_density"]

    style_effects = {
        "builder": "Home recommendations will lean toward Project Mode and practical build-first flows.",
        "structured": "Home recommendations will lean toward Course Mode and ordered progression.",
        "explainer": "AI Mode and Explain Mode will be emphasized more heavily.",
        "competitive": "Code Arena and challenge-based paths will be pushed more often.",
    }

    difficulty_effects = {
        "easy": "The platform should feel more supportive and gentle.",
        "balanced": "The platform should balance structure and challenge.",
        "hard": "The platform should push harder and expect more self-direction.",
    }

    goal_effects = {
        "10": "Recommendations should stay short and focused.",
        "20": "Recommendations should favor one main task and one quick follow-up.",
        "30": "Recommendations can include practice plus reinforcement.",
        "45+": "Recommendations can support deeper build and review sessions.",
    }

    density_effects = {
        "comfortable": "The interface should feel more open and easier to scan.",
        "compact": "The interface should favor showing more information at once.",
    }

    st.markdown("### Personalization Effects")
    bullet_list(
        [
            style_effects.get(learning_style, ""),
            difficulty_effects.get(difficulty, ""),
            goal_effects.get(session_goal, ""),
            density_effects.get(ui_density, ""),
        ]
    )


def _render_best_fit_card() -> None:
    profile = get_personalization_profile()

    best_fit_title = {
        "builder": "Best Fit: Project-First Learner",
        "structured": "Best Fit: Step-by-Step Learner",
        "explainer": "Best Fit: Concept-First Learner",
        "competitive": "Best Fit: Challenge-Driven Learner",
    }.get(profile["learning_style"], "Best Fit: Builder")

    best_fit_body = {
        "builder": "You get the most value when Pylix turns concepts into real builds fast.",
        "structured": "You benefit most from ordered lessons, checkpoints, and visible progression.",
        "explainer": "You benefit most when the why behind code is clear before pressure is added.",
        "competitive": "You benefit most when progress feels like a game with clear wins.",
    }.get(profile["learning_style"], "You benefit from practical learning.")

    content_card(
        title=best_fit_title,
        body=best_fit_body,
        badge="Profile Match",
        min_height=150,
    )


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data
    _init_state()

    mode_header(
        "Settings",
        "Personalize how Pylix feels, how fast it pushes you, and how you prefer to learn.",
        "⚙️",
    )

    left_col, right_col = st.columns([2, 1])

    with left_col:
        _render_option_group(
            "Learning Style",
            "settings_learning_style",
            LEARNING_STYLE_OPTIONS,
        )
        _render_option_group(
            "Difficulty Feel",
            "settings_difficulty",
            DIFFICULTY_OPTIONS,
        )
        _render_option_group(
            "Session Goal",
            "settings_session_goal",
            SESSION_GOAL_OPTIONS,
        )
        _render_option_group(
            "UI Density",
            "settings_ui_density",
            UI_DENSITY_OPTIONS,
        )

        action_row(
            [
                make_button(
                    label="Save Settings",
                    key="save_settings_button",
                    action=_save_settings,
                ),
                make_button(
                    label="Reset Defaults",
                    key="reset_settings_button",
                    action=_reset_settings,
                ),
            ]
        )

    with right_col:
        _render_summary()
        _render_best_fit_card()
        _render_personalized_effects()

        st.markdown("### What This Will Influence")
        bullet_list(
            [
                "Recommended modes on the home screen",
                "How strongly Pylix pushes practice vs projects",
                "How the AI tutor frames help",
                "How compact or relaxed the interface should feel",
            ]
        )

        if st.session_state.get("settings_saved", False):
            st.success("Your settings are active for this session.")
