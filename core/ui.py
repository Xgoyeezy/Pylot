from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

import streamlit as st


def mode_header(title: str, description: str, icon: str) -> None:
    st.markdown(
        f"""
        <div style="
            padding: 1rem;
            border-radius: 18px;
            background: rgb(248, 250, 252);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-bottom: 1rem;
        ">
            <h3 style="margin:0;">{icon} {title}</h3>
            <p style="margin:0.35rem 0 0 0; color: rgb(71, 85, 105);">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_panel(title: str, description: str, icon: str = "📘", track: str | None = None) -> None:
    track_html = ""
    if track:
        track_html = (
            f'<div style="font-size:0.9rem; color: rgb(100, 116, 139); margin-bottom:0.25rem;">'
            f"{track}</div>"
        )

    st.markdown(
        f"""
        <div style="
            padding: 1rem;
            border-radius: 18px;
            background: rgb(248, 250, 252);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-bottom: 1rem;
        ">
            {track_html}
            <h3 style="margin:0;">{icon} {title}</h3>
            <p style="margin:0.35rem 0 0 0; color: rgb(71, 85, 105);">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def content_card(
    title: str,
    body: str,
    badge: str = "",
    subbadge: str = "",
    meta_text: str = "",
    eyebrow: str = "",
    min_height: int = 210,
) -> None:
    eyebrow_html = ""
    if eyebrow:
        eyebrow_html = (
            f'<div style="font-size:0.85rem; color: rgb(100, 116, 139); margin-bottom:0.25rem;">'
            f"{eyebrow}</div>"
        )

    badge_html = ""
    if badge or subbadge:
        badge_html = f"""
        <div style="text-align:right; white-space:nowrap;">
            <div style="font-size:0.9rem; color: rgb(51, 65, 85);">{badge}</div>
            <div style="font-size:0.85rem; color: rgb(100, 116, 139);">{subbadge}</div>
        </div>
        """

    meta_html = ""
    if meta_text:
        meta_html = f"""
        <div style="margin-top:0.8rem; color: rgb(71, 85, 105); font-size:0.92rem;">
            {meta_text}
        </div>
        """

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 18px;
            padding: 1rem;
            background: white;
            min-height: {min_height}px;
        ">
            <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start;">
                <div>
                    {eyebrow_html}
                    <h4 style="margin:0;">{title}</h4>
                    <p style="margin:0.3rem 0 0 0; color: rgb(71, 85, 105);">{body}</p>
                </div>
                {badge_html}
            </div>
            {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats(stats: Sequence[tuple[str, Any]]) -> None:
    columns = st.columns(len(stats))
    for column, (label, value) in zip(columns, stats):
        with column:
            st.metric(label, value)


def render_bullet_list(items: Iterable[str]) -> None:
    for item in items:
        st.write(f"- {item}")


def render_action_buttons(buttons: Sequence[dict[str, Any]]) -> None:
    columns = st.columns(len(buttons))
    for column, button in zip(columns, buttons):
        with column:
            if st.button(
                button["label"],
                key=button["key"],
                use_container_width=button.get("use_container_width", True),
                disabled=button.get("disabled", False),
            ):
                action: Callable[[], None] = button["action"]
                action()


def make_button(
    label: str,
    key: str,
    action: Callable[[], None],
    *,
    use_container_width: bool = True,
    disabled: bool = False,
) -> dict[str, Any]:
    return {
        "label": label,
        "key": key,
        "action": action,
        "use_container_width": use_container_width,
        "disabled": disabled,
    }