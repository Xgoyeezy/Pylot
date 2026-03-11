from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List


import streamlit as st

DB_PATH = "account_progress.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_tables() -> None:
    connection = _connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lesson_reviews (
            lesson_id TEXT PRIMARY KEY,
            passed INTEGER NOT NULL DEFAULT 0,
            score REAL,
            feedback TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lesson_completion (
            lesson_id TEXT PRIMARY KEY,
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_reviews (
            project_id TEXT PRIMARY KEY,
            passed INTEGER NOT NULL DEFAULT 0,
            score REAL,
            feedback TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_completion (
            project_id TEXT PRIMARY KEY,
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def init_progress_db() -> None:
    _ensure_tables()


def _default_progress_data() -> Dict[str, Any]:
    return {
        "completed_lessons": [],
        "completed_projects": [],
        "review_passed": {},
        "weak_topics": {},
        "recommended_mode": "Course Mode",
        "recommended_topic": "general-python",
    }


def _ensure_session_progress() -> Dict[str, Any]:
    if "progress_data" not in st.session_state:
        st.session_state["progress_data"] = _default_progress_data()

    progress_data = st.session_state["progress_data"]
    defaults = _default_progress_data()

    for key, value in defaults.items():
        progress_data.setdefault(key, value if not isinstance(value, (list, dict)) else value.copy())

    st.session_state["progress_data"] = progress_data
    return progress_data


def load_progress() -> Dict[str, Any]:
    return _ensure_session_progress()


def save_progress(progress_data: Dict[str, Any]) -> None:
    st.session_state["progress_data"] = progress_data


def upsert_current_user() -> str:
    return "guest"


def migrate_guest_to_account() -> None:
    return None


def get_weak_topics() -> Dict[str, int]:
    progress_data = _ensure_session_progress()
    weak_topics = progress_data.get("weak_topics", {})
    return {str(key): int(value) for key, value in weak_topics.items()}


def get_recommended_topic() -> str:
    weak_topics = get_weak_topics()
    if not weak_topics:
        return "general-python"

    sorted_topics = sorted(weak_topics.items(), key=lambda item: item[1], reverse=True)
    return sorted_topics[0][0]


def get_recommended_mode() -> str:
    progress_data = _ensure_session_progress()
    weak_topics = progress_data.get("weak_topics", {})

    if weak_topics:
        top_topic = get_recommended_topic()
        if weak_topics.get(top_topic, 0) >= 3:
            return "Practice Mode"

    if len(progress_data.get("completed_lessons", [])) < 2:
        return "Course Mode"

    if len(progress_data.get("completed_projects", [])) < 1:
        return "Project Mode"

    return "AI Mode"


def _refresh_recommendations(progress_data: Dict[str, Any]) -> None:
    progress_data["recommended_mode"] = get_recommended_mode()
    progress_data["recommended_topic"] = get_recommended_topic()


def update_weak_topics(missed_topics: List[str], success: bool = False) -> Dict[str, int]:
    progress_data = _ensure_session_progress()
    weak_topics = progress_data.get("weak_topics", {})

    if success:
        for topic in missed_topics:
            if topic in weak_topics:
                weak_topics[topic] = max(0, int(weak_topics[topic]) - 1)
    else:
        for topic in missed_topics:
            weak_topics[topic] = int(weak_topics.get(topic, 0)) + 1

    progress_data["weak_topics"] = weak_topics
    _refresh_recommendations(progress_data)
    save_progress(progress_data)
    return weak_topics


def get_learning_profile() -> Dict[str, Any]:
    progress_data = _ensure_session_progress()
    weak_topics = get_weak_topics()
    sorted_topics = sorted(weak_topics.items(), key=lambda item: item[1], reverse=True)

    return {
        "completed_lessons": len(progress_data.get("completed_lessons", [])),
        "completed_projects": len(progress_data.get("completed_projects", [])),
        "review_passed_count": len(progress_data.get("review_passed", {})),
        "weak_topics": weak_topics,
        "top_weak_topics": sorted_topics[:3],
        "recommended_mode": get_recommended_mode(),
        "recommended_topic": get_recommended_topic(),
    }


def _set_review_result(
    *,
    entity_type: str,
    entity_id: str,
    passed: bool,
    score: float | None = None,
    feedback: str | None = None,
) -> None:
    _ensure_tables()

    progress_data = _ensure_session_progress()
    progress_data["review_passed"][f"{entity_type}:{entity_id}"] = bool(passed)
    _refresh_recommendations(progress_data)
    save_progress(progress_data)

    table_name = "lesson_reviews" if entity_type == "lesson" else "project_reviews"
    id_column = "lesson_id" if entity_type == "lesson" else "project_id"

    connection = _connect()
    cursor = connection.cursor()
    cursor.execute(
        f"""
        INSERT INTO {table_name} ({id_column}, passed, score, feedback, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT({id_column}) DO UPDATE SET
            passed = excluded.passed,
            score = excluded.score,
            feedback = excluded.feedback,
            updated_at = excluded.updated_at
        """,
        (entity_id, int(passed), score, feedback, _utc_now()),
    )
    connection.commit()
    connection.close()


def _has_passed_review(entity_type: str, entity_id: str) -> bool:
    progress_data = _ensure_session_progress()
    session_key = f"{entity_type}:{entity_id}"

    if progress_data["review_passed"].get(session_key) is True:
        return True

    _ensure_tables()

    table_name = "lesson_reviews" if entity_type == "lesson" else "project_reviews"
    id_column = "lesson_id" if entity_type == "lesson" else "project_id"

    connection = _connect()
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT passed FROM {table_name} WHERE {id_column} = ?",
        (entity_id,),
    )
    row = cursor.fetchone()
    connection.close()

    return bool(row["passed"]) if row else False


def _mark_completion(entity_type: str, entity_id: str, progress_data: Dict[str, Any]) -> bool:
    _ensure_tables()

    if not _has_passed_review(entity_type, entity_id):
        return False

    completed_key = "completed_lessons" if entity_type == "lesson" else "completed_projects"
    table_name = "lesson_completion" if entity_type == "lesson" else "project_completion"
    id_column = "lesson_id" if entity_type == "lesson" else "project_id"

    if entity_id not in progress_data[completed_key]:
        progress_data[completed_key].append(entity_id)
        _refresh_recommendations(progress_data)
        save_progress(progress_data)

    timestamp = _utc_now()

    connection = _connect()
    cursor = connection.cursor()
    cursor.execute(
        f"""
        INSERT INTO {table_name} ({id_column}, completed, completed_at, updated_at)
        VALUES (?, 1, ?, ?)
        ON CONFLICT({id_column}) DO UPDATE SET
            completed = 1,
            completed_at = COALESCE({table_name}.completed_at, excluded.completed_at),
            updated_at = excluded.updated_at
        """,
        (entity_id, timestamp, timestamp),
    )
    connection.commit()
    connection.close()

    return True


def _is_complete(entity_type: str, entity_id: str) -> bool:
    progress_data = _ensure_session_progress()
    completed_key = "completed_lessons" if entity_type == "lesson" else "completed_projects"

    if entity_id in progress_data[completed_key]:
        return True

    _ensure_tables()

    table_name = "lesson_completion" if entity_type == "lesson" else "project_completion"
    id_column = "lesson_id" if entity_type == "lesson" else "project_id"

    connection = _connect()
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT completed FROM {table_name} WHERE {id_column} = ?",
        (entity_id,),
    )
    row = cursor.fetchone()
    connection.close()

    return bool(row["completed"]) if row else False


def set_lesson_review_result(
    lesson_id: str,
    passed: bool,
    score: float | None = None,
    feedback: str | None = None,
) -> None:
    _set_review_result(
        entity_type="lesson",
        entity_id=lesson_id,
        passed=passed,
        score=score,
        feedback=feedback,
    )


def has_passed_lesson_review(lesson_id: str) -> bool:
    return _has_passed_review("lesson", lesson_id)


def mark_lesson_complete(*args: Any) -> bool:
    if len(args) == 2:
        progress_data, lesson_id = args
    elif len(args) == 1:
        lesson_id = args[0]
        progress_data = _ensure_session_progress()
    else:
        raise TypeError("mark_lesson_complete expects (lesson_id) or (progress_data, lesson_id)")

    return _mark_completion("lesson", lesson_id, progress_data)


def is_lesson_complete(lesson_id: str) -> bool:
    return _is_complete("lesson", lesson_id)


def set_project_review_result(
    project_id: str,
    passed: bool,
    score: float | None = None,
    feedback: str | None = None,
) -> None:
    _set_review_result(
        entity_type="project",
        entity_id=project_id,
        passed=passed,
        score=score,
        feedback=feedback,
    )


def has_passed_project_review(project_id: str) -> bool:
    return _has_passed_review("project", project_id)


def mark_project_complete(*args: Any) -> bool:
    if len(args) == 2:
        progress_data, project_id = args
    elif len(args) == 1:
        project_id = args[0]
        progress_data = _ensure_session_progress()
    else:
        raise TypeError("mark_project_complete expects (project_id) or (progress_data, project_id)")

    return _mark_completion("project", project_id, progress_data)


def is_project_complete(project_id: str) -> bool:
    return _is_complete("project", project_id)