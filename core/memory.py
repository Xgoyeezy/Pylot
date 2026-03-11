from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from core.ui import make_button, render_action_buttons, section_panel

DB_PATH = "memory.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def execute_write(query: str, params: tuple = ()) -> int:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    affected = cursor.rowcount
    connection.commit()
    connection.close()
    return affected


def fetch_all(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()
    return rows


def fetch_one(query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    connection.close()
    return row


def init_memory_db() -> None:
    execute_write(
        """
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(category, key)
        )
        """
    )

    execute_write(
        """
        CREATE TABLE IF NOT EXISTS memory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


def log_event(event_type: str, payload: Dict[str, Any]) -> None:
    execute_write(
        """
        INSERT INTO memory_events (event_type, payload, created_at)
        VALUES (?, ?, ?)
        """,
        (event_type, json.dumps(payload, ensure_ascii=False), utc_now()),
    )


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)


def list_memory_entries(category: Optional[str] = None) -> List[Dict[str, Any]]:
    if category:
        rows = fetch_all(
            """
            SELECT id, category, key, value, notes, created_at, updated_at
            FROM memory_entries
            WHERE category = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (category,),
        )
    else:
        rows = fetch_all(
            """
            SELECT id, category, key, value, notes, created_at, updated_at
            FROM memory_entries
            ORDER BY updated_at DESC, id DESC
            """
        )

    return [row_to_dict(row) for row in rows]


def get_memory_entry(category: str, key: str) -> Optional[Dict[str, Any]]:
    row = fetch_one(
        """
        SELECT id, category, key, value, notes, created_at, updated_at
        FROM memory_entries
        WHERE category = ? AND key = ?
        """,
        (category, key),
    )
    return row_to_dict(row) if row else None


def set_memory_entry(category: str, key: str, value: Any, notes: str = "") -> None:
    now = utc_now()
    value_text = json.dumps(value, ensure_ascii=False, indent=2)

    execute_write(
        """
        INSERT INTO memory_entries (category, key, value, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(category, key) DO UPDATE SET
            value = excluded.value,
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (category, key, value_text, notes, now, now),
    )

    log_event(
        "set_memory_entry",
        {
            "category": category,
            "key": key,
            "notes": notes,
        },
    )


def delete_memory_entry(category: str, key: str) -> bool:
    deleted = execute_write(
        """
        DELETE FROM memory_entries
        WHERE category = ? AND key = ?
        """,
        (category, key),
    ) > 0

    if deleted:
        log_event(
            "delete_memory_entry",
            {
                "category": category,
                "key": key,
            },
        )

    return deleted


def clear_category(category: str) -> int:
    deleted_count = execute_write(
        """
        DELETE FROM memory_entries
        WHERE category = ?
        """,
        (category,),
    )

    log_event(
        "clear_category",
        {
            "category": category,
            "deleted_count": deleted_count,
        },
    )

    return deleted_count


def search_memory(query: str) -> List[Dict[str, Any]]:
    like_query = f"%{query}%"

    rows = fetch_all(
        """
        SELECT id, category, key, value, notes, created_at, updated_at
        FROM memory_entries
        WHERE category LIKE ?
           OR key LIKE ?
           OR value LIKE ?
           OR notes LIKE ?
        ORDER BY updated_at DESC, id DESC
        """,
        (like_query, like_query, like_query, like_query),
    )

    return [row_to_dict(row) for row in rows]


def get_recent_events(limit: int = 25) -> List[Dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, event_type, payload, created_at
        FROM memory_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    return [row_to_dict(row) for row in rows]


def try_parse_json(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return ""

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped


def export_memory_to_file(output_path: str) -> str:
    entries = list_memory_entries()
    path = Path(output_path)
    path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def copy_entry_to_editor(entry: Dict[str, Any]) -> None:
    st.session_state["memory_edit_category"] = entry["category"]
    st.session_state["memory_edit_key"] = entry["key"]
    st.session_state["memory_edit_value"] = entry["value"]
    st.session_state["memory_edit_notes"] = entry["notes"]
    st.success("Entry copied to editor.")


def render_entry_block(entry: Dict[str, Any], allow_copy: bool = True, key_prefix: str = "memory") -> None:
    with st.expander(f'{entry["category"]} / {entry["key"]}', expanded=False):
        st.caption(f'Updated: {entry["updated_at"]}')
        if entry.get("notes"):
            st.write(f'Notes: {entry["notes"]}')
        st.code(entry["value"], language="json")

        buttons = [
            make_button(
                label="Delete entry",
                key=f'{key_prefix}_delete_{entry["id"]}',
                action=lambda: _delete_and_rerun(entry["category"], entry["key"]),
            )
        ]

        if allow_copy:
            buttons.append(
                make_button(
                    label="Copy to editor",
                    key=f'{key_prefix}_copy_{entry["id"]}',
                    action=lambda: copy_entry_to_editor(entry),
                )
            )

        render_action_buttons(buttons)


def _delete_and_rerun(category: str, key: str) -> None:
    if delete_memory_entry(category, key):
        st.success("Entry deleted.")
        st.rerun()
    else:
        st.error("Could not delete entry.")


def _clear_category_and_rerun(category: str) -> None:
    deleted_count = clear_category(category)
    st.success(f"Deleted {deleted_count} entries from '{category}'.")
    st.rerun()


def _save_entry_and_rerun(category: str, key: str, value_text: str, notes: str) -> None:
    parsed_value = try_parse_json(value_text)
    set_memory_entry(
        category=category.strip(),
        key=key.strip(),
        value=parsed_value,
        notes=notes.strip(),
    )
    st.success("Entry saved.")
    st.rerun()


def render_browse_tab() -> None:
    st.markdown("### Memory Entries")

    all_entries = list_memory_entries()
    categories = sorted({entry["category"] for entry in all_entries})
    selected_category = st.selectbox(
        "Filter by category",
        ["All"] + categories,
        key="memory_category_filter",
    )

    filtered_entries = (
        all_entries
        if selected_category == "All"
        else [entry for entry in all_entries if entry["category"] == selected_category]
    )

    st.caption(f"Entries found: {len(filtered_entries)}")

    if not filtered_entries:
        st.info("No memory entries found.")
    else:
        for entry in filtered_entries:
            render_entry_block(entry, allow_copy=True, key_prefix="browse")

    st.markdown("### Category Tools")
    clear_target = st.text_input(
        "Category to clear",
        key="memory_clear_category_text",
    )

    render_action_buttons(
        [
            make_button(
                label="Clear category",
                key="memory_clear_category_btn",
                action=lambda: (
                    st.warning("Enter a category name first.")
                    if not clear_target.strip()
                    else _clear_category_and_rerun(clear_target.strip())
                ),
            ),
        ]
    )
def export_memory_action() -> None:
    path = export_memory_to_file("memory_export.json")
    st.success(f"Exported memory to {path}.")

    make_button(
        label="Export memory to JSON",
        key="memory_export_btn",
        action=export_memory_action,
    )

def render_add_update_tab() -> None:
    st.markdown("### Add or Update Entry")

    category = st.text_input("Category", key="memory_edit_category")
    key = st.text_input("Key", key="memory_edit_key")
    value_text = st.text_area(
        "Value (JSON or plain text)",
        key="memory_edit_value",
        height=220,
    )
    notes = st.text_area(
        "Notes",
        key="memory_edit_notes",
        height=100,
    )

    render_action_buttons(
        [
            make_button(
                label="Save entry",
                key="memory_save_btn",
                action=lambda: (
                    st.warning("Category and key are required.")
                    if not category.strip() or not key.strip()
                    else _save_entry_and_rerun(category, key, value_text, notes)
                ),
            )
        ]
    )

    st.markdown("### Quick Example")
    st.code(
        json.dumps(
            {
                "topic": "functions",
                "weakness": "parameter passing",
                "last_score": 72,
            },
            indent=2,
        ),
        language="json",
    )


def render_search_tab() -> None:
    st.markdown("### Search Memory")

    query = st.text_input("Search query", key="memory_search_query")
    if query.strip():
        results = search_memory(query.strip())
        st.caption(f"Matches: {len(results)}")

        if not results:
            st.info("No matching entries found.")
        else:
            for entry in results:
                render_entry_block(entry, allow_copy=False, key_prefix="search")
    else:
        st.info("Enter a search query to search memory.")


def render_events_tab() -> None:
    st.markdown("### Recent Memory Events")
    events = get_recent_events()

    if not events:
        st.info("No memory events recorded yet.")
        return

    for event in events:
        with st.expander(f'{event["event_type"]} — {event["created_at"]}', expanded=False):
            st.code(event["payload"], language="json")


def render(progress_data: Dict[str, Any]) -> None:
    _ = progress_data

    init_memory_db()

    section_panel(
        title="Shared Memory Admin Mode",
        description="Manage shared memory entries, search stored context, and inspect recent memory events.",
        icon="🧠",
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Browse", "Add / Update", "Search", "Events"]
    )

    with tab1:
        render_browse_tab()

    with tab2:
        render_add_update_tab()

    with tab3:
        render_search_tab()

    with tab4:
        render_events_tab()


def build_memory_context(query: str = "", top_k: int = 3) -> str:
    if not query:
        entries = list_memory_entries()[:top_k]
    else:
        entries = search_memory(query)[:top_k]

    if not entries:
        return ""

    context_lines = [
        f'{entry["category"]}/{entry["key"]}: {entry["value"]}'
        for entry in entries
    ]
    return "\n".join(context_lines)