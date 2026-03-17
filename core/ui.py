from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

import streamlit as st


def inject_ui_theme() -> None:
    if st.session_state.get("_pylix_ui_theme_loaded", False):
        return

    st.session_state["_pylix_ui_theme_loaded"] = True

    st.markdown(
        """
        <style>
        :root {
            --pylix-bg: #F4F7FB;
            --pylix-surface: #FFFFFF;
            --pylix-surface-soft: #F8FAFC;
            --pylix-border: rgba(148, 163, 184, 0.18);
            --pylix-border-strong: rgba(148, 163, 184, 0.26);
            --pylix-text: #0F172A;
            --pylix-muted: #475569;
            --pylix-muted-soft: #64748B;
            --pylix-primary: #2563EB;
            --pylix-primary-soft: rgba(37, 99, 235, 0.10);
            --pylix-success: #16A34A;
            --pylix-warning: #D97706;
            --pylix-danger: #DC2626;
            --pylix-shadow-sm: 0 6px 20px rgba(15, 23, 42, 0.05);
            --pylix-shadow-md: 0 12px 30px rgba(15, 23, 42, 0.08);
            --pylix-shadow-lg: 0 18px 50px rgba(15, 23, 42, 0.14);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 28%),
                radial-gradient(circle at top right, rgba(99, 102, 241, 0.08), transparent 25%),
                linear-gradient(180deg, #F8FAFC 0%, #F4F7FB 100%);
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }

        .pylix-glass {
            background: rgba(255,255,255,0.72);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.35);
            box-shadow: var(--pylix-shadow-sm);
        }

        .pylix-surface {
            padding: 1rem 1.05rem;
            border-radius: 22px;
            background: linear-gradient(180deg, #FFFFFF 0%, #FCFDFF 100%);
            border: 1px solid var(--pylix-border);
            margin-bottom: 1rem;
            box-shadow: var(--pylix-shadow-sm);
        }

        .pylix-surface-soft {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
            border: 1px solid var(--pylix-border);
            margin-bottom: 0.9rem;
            box-shadow: var(--pylix-shadow-sm);
        }

        .pylix-hero {
            position: relative;
            overflow: hidden;
            padding: 1.35rem 1.35rem;
            border-radius: 26px;
            background:
                radial-gradient(circle at 20% 20%, rgba(96, 165, 250, 0.25), transparent 28%),
                radial-gradient(circle at 80% 10%, rgba(129, 140, 248, 0.20), transparent 26%),
                linear-gradient(135deg, #0F172A 0%, #172554 55%, #1E3A8A 100%);
            color: white;
            border: 1px solid rgba(30, 64, 175, 0.22);
            margin-bottom: 1rem;
            box-shadow: var(--pylix-shadow-lg);
        }

        .pylix-hero::after {
            content: "";
            position: absolute;
            inset: auto -40px -60px auto;
            width: 180px;
            height: 180px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            filter: blur(2px);
        }

        .pylix-card {
            border: 1px solid var(--pylix-border);
            border-radius: 22px;
            padding: 1rem;
            background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
            min-height: 170px;
            margin-bottom: 0.9rem;
            box-shadow: var(--pylix-shadow-sm);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .pylix-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--pylix-shadow-md);
            border-color: rgba(37, 99, 235, 0.18);
        }

        .pylix-card-title {
            margin: 0;
            font-size: 1.04rem;
            font-weight: 700;
            color: var(--pylix-text);
            line-height: 1.3;
            letter-spacing: -0.01em;
        }

        .pylix-card-body {
            margin: 0.42rem 0 0 0;
            color: var(--pylix-muted);
            line-height: 1.58;
            font-size: 0.96rem;
        }

        .pylix-card-meta {
            margin-top: 0.85rem;
            color: var(--pylix-muted-soft);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .pylix-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.28rem 0.6rem;
            border-radius: 999px;
            background: var(--pylix-primary-soft);
            color: #1D4ED8;
            font-size: 0.78rem;
            font-weight: 700;
            white-space: nowrap;
            border: 1px solid rgba(37, 99, 235, 0.14);
        }

        .pylix-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.14);
            color: rgba(255,255,255,0.92);
            font-size: 0.8rem;
            font-weight: 600;
        }

        .pylix-muted {
            color: var(--pylix-muted);
        }

        .pylix-track {
            font-size: 0.82rem;
            color: var(--pylix-muted-soft);
            margin-bottom: 0.25rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .pylix-section-title {
            margin: 0 0 0.65rem 0;
            color: var(--pylix-text);
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #FAFCFF 100%);
            border: 1px solid var(--pylix-border);
            border-radius: 20px;
            padding: 0.8rem 0.95rem;
            box-shadow: var(--pylix-shadow-sm);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--pylix-muted-soft);
            font-weight: 700;
        }

        div[data-testid="stMetricValue"] {
            color: var(--pylix-text);
            letter-spacing: -0.02em;
        }

        div[data-testid="stProgressBar"] > div > div {
            border-radius: 999px;
        }

        .stButton > button {
            border-radius: 14px !important;
            border: 1px solid rgba(37, 99, 235, 0.12) !important;
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%) !important;
            color: #0F172A !important;
            font-weight: 700 !important;
            min-height: 2.65rem !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05) !important;
            transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease !important;
        }

        .stButton > button:hover {
            border-color: rgba(37, 99, 235, 0.26) !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08) !important;
            transform: translateY(-1px);
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%) !important;
            color: white !important;
            border-color: rgba(29, 78, 216, 0.8) !important;
        }

        .stTextArea textarea,
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] > div,
        .stRadio div[role="radiogroup"] {
            border-radius: 16px !important;
        }

        .stTextArea textarea,
        .stTextInput input {
            background: rgba(255,255,255,0.95) !important;
            border: 1px solid var(--pylix-border-strong) !important;
        }

        .stExpander {
            border-radius: 16px !important;
            border: 1px solid var(--pylix-border) !important;
            background: rgba(255,255,255,0.7) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _escape_html(text: Any) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mode_header(title: str, description: str, icon: str = "📘") -> None:
    inject_ui_theme()

    st.markdown(
        f"""
        <div class="pylix-hero">
            <div class="pylix-pill">Interactive Learning Surface</div>
            <h2 style="margin:0.72rem 0 0 0; font-size:1.45rem; letter-spacing:-0.02em;">
                {_escape_html(icon)} {_escape_html(title)}
            </h2>
            <p style="margin:0.5rem 0 0 0; color: rgba(255,255,255,0.86); line-height:1.65; max-width: 860px;">
                {_escape_html(description)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_panel(
    title: str,
    description: str,
    icon: str = "📘",
    track: str | None = None,
) -> None:
    inject_ui_theme()

    track_html = ""
    if track:
        track_html = f'<div class="pylix-track">{_escape_html(track)}</div>'

    st.markdown(
        f"""
        <div class="pylix-surface">
            {track_html}
            <h3 style="margin:0; color:#0F172A; font-size:1.08rem;">
                {_escape_html(icon)} {_escape_html(title)}
            </h3>
            <p style="margin:0.42rem 0 0 0; color:#475569; line-height:1.6;">
                {_escape_html(description)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def content_card(
    title: str,
    body: str,
    *,
    meta: str = "",
    badge: str = "",
    min_height: int = 170,
) -> None:
    inject_ui_theme()

    badge_html = f'<span class="pylix-badge">{_escape_html(badge)}</span>' if badge else ""
    meta_html = f'<div class="pylix-card-meta">{meta}</div>' if meta else ""

    st.markdown(
        f"""
        <div class="pylix-card" style="min-height:{min_height}px;">
            <div style="display:flex; justify-content:space-between; gap:0.9rem; align-items:flex-start;">
                <div style="flex:1;">
                    <div class="pylix-card-title">{_escape_html(title)}</div>
                    <p class="pylix-card-body">{_escape_html(body)}</p>
                </div>
                <div>{badge_html}</div>
            </div>
            {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(items: Sequence[tuple[str, Any]]) -> None:
    if not items:
        return

    inject_ui_theme()

    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        with column:
            st.metric(str(label), value)


def render_stats(items: Sequence[tuple[str, Any]]) -> None:
    metric_row(items)


def bullet_list(items: Iterable[str]) -> None:
    items_list = [str(item) for item in items if str(item).strip()]
    if not items_list:
        return

    inject_ui_theme()

    html = "".join(
        f"""
        <li style="margin-bottom:0.5rem; color:#334155; line-height:1.6;">
            {_escape_html(item)}
        </li>
        """
        for item in items_list
    )

    st.markdown(
        f"""
        <div class="pylix-surface-soft">
            <ul style="margin:0; padding-left:1.1rem;">
                {html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bullet_list(items: Iterable[str]) -> None:
    bullet_list(items)


def action_button(
    label: str,
    key: str,
    action: Callable[[], None],
    *,
    use_container_width: bool = True,
    disabled: bool = False,
) -> None:
    if st.button(
        label,
        key=key,
        use_container_width=use_container_width,
        disabled=disabled,
        type="primary",
    ):
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


def action_row(buttons: Sequence[dict[str, Any]]) -> None:
    if not buttons:
        return

    inject_ui_theme()

    columns = st.columns(len(buttons))
    for index, (column, button) in enumerate(zip(columns, buttons)):
        with column:
            if st.button(
                button["label"],
                key=button["key"],
                use_container_width=button.get("use_container_width", True),
                disabled=button.get("disabled", False),
                type="primary" if index == 0 else "secondary",
            ):
                callback: Callable[[], None] = button["action"]
                callback()


def render_action_buttons(buttons: Sequence[dict[str, Any]]) -> None:
    action_row(buttons)
