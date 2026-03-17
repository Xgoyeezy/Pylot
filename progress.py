from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Any, Dict, List

DB_PATH = "account_progress.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_progress_db() -> None:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY,
            completed_lessons TEXT,
            completed_projects TEXT,
            review_passed TEXT,
            weak_topics TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_active_date TEXT DEFAULT '',
            last_quest_claimed_date TEXT DEFAULT '',
            arena_score INTEGER DEFAULT 0,
            arena_wins INTEGER DEFAULT 0,
            arena_win_streak INTEGER DEFAULT 0,
            best_arena_win_streak INTEGER DEFAULT 0,
            last_arena_win_date TEXT DEFAULT '',
            last_arena_mission_claimed_date TEXT DEFAULT ''
        )
        """
    )

    cur.execute("PRAGMA table_info(progress)")
    existing_columns = {row[1] for row in cur.fetchall()}

    required_columns = {
        "xp": "INTEGER DEFAULT 0",
        "level": "INTEGER DEFAULT 1",
        "current_streak": "INTEGER DEFAULT 0",
        "longest_streak": "INTEGER DEFAULT 0",
        "last_active_date": "TEXT DEFAULT ''",
        "last_quest_claimed_date": "TEXT DEFAULT ''",
        "arena_score": "INTEGER DEFAULT 0",
        "arena_wins": "INTEGER DEFAULT 0",
        "arena_win_streak": "INTEGER DEFAULT 0",
        "best_arena_win_streak": "INTEGER DEFAULT 0",
        "last_arena_win_date": "TEXT DEFAULT ''",
        "last_arena_mission_claimed_date": "TEXT DEFAULT ''",
    }

    for column_name, column_def in required_columns.items():
        if column_name not in existing_columns:
            cur.execute(f"ALTER TABLE progress ADD COLUMN {column_name} {column_def}")

    cur.execute("SELECT COUNT(*) FROM progress")
    if cur.fetchone()[0] == 0:
        cur.execute(
            """
            INSERT INTO progress
            (
                id,
                completed_lessons,
                completed_projects,
                review_passed,
                weak_topics,
                xp,
                level,
                current_streak,
                longest_streak,
                last_active_date,
                last_quest_claimed_date,
                arena_score,
                arena_wins,
                arena_win_streak,
                best_arena_win_streak,
                last_arena_win_date,
                last_arena_mission_claimed_date
            )
            VALUES (1, '', '', '', '', 0, 1, 0, 0, '', '', 0, 0, 0, 0, '', '')
            """
        )

    conn.commit()
    conn.close()


def load_progress() -> Dict[str, Any]:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            completed_lessons,
            completed_projects,
            review_passed,
            weak_topics,
            xp,
            level,
            current_streak,
            longest_streak,
            last_active_date,
            last_quest_claimed_date,
            arena_score,
            arena_wins,
            arena_win_streak,
            best_arena_win_streak,
            last_arena_win_date,
            last_arena_mission_claimed_date
        FROM progress
        WHERE id = 1
        LIMIT 1
        """
    )

    row = cur.fetchone()
    conn.close()

    if row is None:
        return _default_progress()

    return {
        "completed_lessons": _parse_set(row[0]),
        "completed_projects": _parse_set(row[1]),
        "review_passed": _parse_set(row[2]),
        "weak_topics": _parse_topics(row[3]),
        "xp": int(row[4] or 0),
        "level": int(row[5] or 1),
        "current_streak": int(row[6] or 0),
        "longest_streak": int(row[7] or 0),
        "last_active_date": row[8] or "",
        "last_quest_claimed_date": row[9] or "",
        "arena_score": int(row[10] or 0),
        "arena_wins": int(row[11] or 0),
        "arena_win_streak": int(row[12] or 0),
        "best_arena_win_streak": int(row[13] or 0),
        "last_arena_win_date": row[14] or "",
        "last_arena_mission_claimed_date": row[15] or "",
    }


def _default_progress() -> Dict[str, Any]:
    return {
        "completed_lessons": set(),
        "completed_projects": set(),
        "review_passed": set(),
        "weak_topics": {},
        "xp": 0,
        "level": 1,
        "current_streak": 0,
        "longest_streak": 0,
        "last_active_date": "",
        "last_quest_claimed_date": "",
        "arena_score": 0,
        "arena_wins": 0,
        "arena_win_streak": 0,
        "best_arena_win_streak": 0,
        "last_arena_win_date": "",
        "last_arena_mission_claimed_date": "",
    }


def save_progress(data: Dict[str, Any]) -> None:
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE progress
        SET completed_lessons=?,
            completed_projects=?,
            review_passed=?,
            weak_topics=?,
            xp=?,
            level=?,
            current_streak=?,
            longest_streak=?,
            last_active_date=?,
            last_quest_claimed_date=?,
            arena_score=?,
            arena_wins=?,
            arena_win_streak=?,
            best_arena_win_streak=?,
            last_arena_win_date=?,
            last_arena_mission_claimed_date=?
        WHERE id=1
        """,
        (
            _join_set(data["completed_lessons"]),
            _join_set(data["completed_projects"]),
            _join_set(data["review_passed"]),
            _join_topics(data["weak_topics"]),
            int(data.get("xp", 0)),
            int(data.get("level", 1)),
            int(data.get("current_streak", 0)),
            int(data.get("longest_streak", 0)),
            str(data.get("last_active_date", "")),
            str(data.get("last_quest_claimed_date", "")),
            int(data.get("arena_score", 0)),
            int(data.get("arena_wins", 0)),
            int(data.get("arena_win_streak", 0)),
            int(data.get("best_arena_win_streak", 0)),
            str(data.get("last_arena_win_date", "")),
            str(data.get("last_arena_mission_claimed_date", "")),
        ),
    )

    conn.commit()
    conn.close()


def _today_iso() -> str:
    return date.today().isoformat()


def touch_daily_activity() -> Dict[str, Any]:
    data = load_progress()
    today = date.today()
    today_iso = today.isoformat()
    last_active_raw = data.get("last_active_date", "")

    if not last_active_raw:
        data["current_streak"] = max(1, int(data.get("current_streak", 0)))
        data["longest_streak"] = max(int(data.get("longest_streak", 0)), int(data["current_streak"]))
        data["last_active_date"] = today_iso
        save_progress(data)
        return data

    if last_active_raw == today_iso:
        return data

    try:
        last_active = date.fromisoformat(last_active_raw)
    except ValueError:
        last_active = today - timedelta(days=2)

    days_since = (today - last_active).days

    if days_since == 1:
        data["current_streak"] = int(data.get("current_streak", 0)) + 1
    else:
        data["current_streak"] = 1

    data["longest_streak"] = max(int(data.get("longest_streak", 0)), int(data["current_streak"]))
    data["last_active_date"] = today_iso
    save_progress(data)
    return data


def can_claim_daily_quest() -> bool:
    data = load_progress()
    return data.get("last_quest_claimed_date", "") != _today_iso()


def mark_daily_quest_claimed() -> None:
    data = load_progress()
    data["last_quest_claimed_date"] = _today_iso()
    save_progress(data)


def can_claim_daily_arena_mission() -> bool:
    data = load_progress()
    return data.get("last_arena_mission_claimed_date", "") != _today_iso()


def mark_daily_arena_mission_claimed() -> None:
    data = load_progress()
    data["last_arena_mission_claimed_date"] = _today_iso()
    save_progress(data)


def _mark_set_value(field: str, value: str, add: bool = True) -> None:
    data = load_progress()
    target = data[field]

    if add:
        target.add(value)
    else:
        target.discard(value)

    save_progress(data)


def add_xp(amount: int) -> None:
    if amount <= 0:
        return

    data = load_progress()
    data["xp"] = int(data.get("xp", 0)) + amount
    data["level"] = _calculate_level(data["xp"])
    save_progress(data)


def record_arena_win(score_gain: int = 25) -> None:
    data = load_progress()
    today = date.today()
    today_iso = today.isoformat()
    last_win_raw = data.get("last_arena_win_date", "")

    data["arena_wins"] = int(data.get("arena_wins", 0)) + 1
    data["arena_score"] = int(data.get("arena_score", 0)) + max(0, score_gain)

    if not last_win_raw:
        data["arena_win_streak"] = 1
    else:
        try:
            last_win = date.fromisoformat(last_win_raw)
        except ValueError:
            last_win = today - timedelta(days=2)

        days_since = (today - last_win).days
        if days_since == 0:
            data["arena_win_streak"] = max(1, int(data.get("arena_win_streak", 0)))
        elif days_since == 1:
            data["arena_win_streak"] = int(data.get("arena_win_streak", 0)) + 1
        else:
            data["arena_win_streak"] = 1

    data["best_arena_win_streak"] = max(
        int(data.get("best_arena_win_streak", 0)),
        int(data.get("arena_win_streak", 0)),
    )
    data["last_arena_win_date"] = today_iso
    save_progress(data)


def get_arena_rank(arena_score: int) -> str:
    if arena_score >= 300:
        return "Python Slayer"
    if arena_score >= 180:
        return "Gold"
    if arena_score >= 80:
        return "Silver"
    return "Bronze"


def _calculate_level(xp: int) -> int:
    thresholds = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500]
    for index, threshold in enumerate(thresholds, start=1):
        if xp < threshold:
            return max(1, index - 1)
    return max(1, int((xp / 250) ** 0.8))


def xp_to_next_level(current_xp: int) -> int:
    thresholds = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500]
    for threshold in thresholds:
        if current_xp < threshold:
            return threshold - current_xp
    next_threshold = ((current_xp // 250) + 1) * 250
    return next_threshold - current_xp


def mark_lesson_complete(lesson_id: str) -> None:
    data = load_progress()
    if lesson_id not in data["completed_lessons"]:
        data["completed_lessons"].add(lesson_id)
        data["xp"] += 20
        data["level"] = _calculate_level(data["xp"])
        save_progress(data)


def mark_project_complete(project_id: str) -> None:
    data = load_progress()
    if project_id not in data["completed_projects"]:
        data["completed_projects"].add(project_id)
        data["xp"] += 60
        data["level"] = _calculate_level(data["xp"])
        save_progress(data)


def mark_review_passed(target_id: str) -> None:
    data = load_progress()
    if target_id not in data["review_passed"]:
        data["review_passed"].add(target_id)
        data["xp"] += 30
        data["level"] = _calculate_level(data["xp"])
        save_progress(data)


def set_lesson_review_result(
    lesson_id: str,
    passed: bool,
    score: float | None = None,
    feedback: str | None = None,
) -> None:
    _ = score
    _ = feedback
    _mark_set_value("review_passed", lesson_id, passed)
    if passed:
        add_xp(30)


def set_project_review_result(
    project_id: str,
    passed: bool,
    score: float | None = None,
    feedback: str | None = None,
) -> None:
    _ = score
    _ = feedback
    _mark_set_value("review_passed", project_id, passed)
    if passed:
        add_xp(30)


def has_passed_lesson_review(lesson_id: str) -> bool:
    return lesson_id in load_progress()["review_passed"]


def has_passed_project_review(project_id: str) -> bool:
    return project_id in load_progress()["review_passed"]


def is_lesson_complete(lesson_id: str) -> bool:
    return lesson_id in load_progress()["completed_lessons"]


def is_project_complete(project_id: str) -> bool:
    return project_id in load_progress()["completed_projects"]


def add_weak_topic(topic: str) -> None:
    data = load_progress()
    weak_topics = data["weak_topics"]
    weak_topics[topic] = weak_topics.get(topic, 0) + 1
    save_progress(data)


def update_weak_topics(missed_topics: List[str], success: bool = False) -> Dict[str, int]:
    data = load_progress()
    weak_topics = data["weak_topics"]

    for topic in missed_topics:
        if success:
            if topic in weak_topics:
                weak_topics[topic] = max(0, weak_topics[topic] - 1)
                if weak_topics[topic] == 0:
                    weak_topics.pop(topic)
        else:
            weak_topics[topic] = weak_topics.get(topic, 0) + 1

    save_progress(data)
    return weak_topics


def get_badges() -> List[Dict[str, str]]:
    data = load_progress()
    badges: List[Dict[str, str]] = []

    if len(data["completed_lessons"]) >= 1:
        badges.append(
            {
                "title": "First Lesson",
                "icon": "📘",
                "description": "Completed your first lesson.",
            }
        )

    if int(data.get("current_streak", 0)) >= 3 or int(data.get("longest_streak", 0)) >= 3:
        badges.append(
            {
                "title": "3-Day Streak",
                "icon": "🔥",
                "description": "Built a 3-day learning streak.",
            }
        )

    if len(data["completed_projects"]) >= 1:
        badges.append(
            {
                "title": "First Project",
                "icon": "🛠️",
                "description": "Completed your first project.",
            }
        )

    if int(data.get("arena_wins", 0)) >= 1:
        badges.append(
            {
                "title": "Arena Initiate",
                "icon": "⚔️",
                "description": "Won your first arena challenge.",
            }
        )

    if int(data.get("arena_win_streak", 0)) >= 3 or int(data.get("best_arena_win_streak", 0)) >= 3:
        badges.append(
            {
                "title": "Arena Streak",
                "icon": "🏅",
                "description": "Reached a 3-win arena streak.",
            }
        )

    if int(data.get("level", 1)) >= 5:
        badges.append(
            {
                "title": "Level 5",
                "icon": "⭐",
                "description": "Reached level 5.",
            }
        )

    return badges


def get_learning_profile() -> Dict[str, Any]:
    data = load_progress()
    weak_topics = data["weak_topics"]

    sorted_topics = sorted(weak_topics.items(), key=lambda item: item[1], reverse=True)
    top_topics = sorted_topics[:3]
    recommended_topic = top_topics[0][0] if top_topics else "general"

    if weak_topics:
        recommended_mode = "Practice Mode"
    elif len(data["completed_lessons"]) < 2:
        recommended_mode = "Course Mode"
    elif len(data["completed_projects"]) < 1:
        recommended_mode = "Project Mode"
    else:
        recommended_mode = "AI Mode"

    current_xp = int(data.get("xp", 0))
    arena_score = int(data.get("arena_score", 0))
    badges = get_badges()

    return {
        "completed_lessons": len(data["completed_lessons"]),
        "completed_projects": len(data["completed_projects"]),
        "review_passed_count": len(data["review_passed"]),
        "weak_topics": weak_topics,
        "top_weak_topics": top_topics,
        "recommended_mode": recommended_mode,
        "recommended_topic": recommended_topic,
        "xp": current_xp,
        "level": int(data.get("level", 1)),
        "current_streak": int(data.get("current_streak", 0)),
        "longest_streak": int(data.get("longest_streak", 0)),
        "xp_to_next_level": xp_to_next_level(current_xp),
        "can_claim_daily_quest": can_claim_daily_quest(),
        "arena_score": arena_score,
        "arena_wins": int(data.get("arena_wins", 0)),
        "arena_rank": get_arena_rank(arena_score),
        "arena_win_streak": int(data.get("arena_win_streak", 0)),
        "best_arena_win_streak": int(data.get("best_arena_win_streak", 0)),
        "can_claim_daily_arena_mission": can_claim_daily_arena_mission(),
        "badges": badges,
        "badge_count": len(badges),
    }


def _parse_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {v for v in value.split(",") if v}


def _join_set(values: set[str]) -> str:
    return ",".join(sorted(values))


def _parse_topics(value: str | None) -> Dict[str, int]:
    if not value:
        return {}

    topics: Dict[str, int] = {}
    for part in value.split(","):
        if ":" not in part:
            continue

        topic, score = part.split(":", 1)

        try:
            topics[topic] = int(score)
        except ValueError:
            topics[topic] = 0

    return topics


def _join_topics(topics: Dict[str, int]) -> str:
    return ",".join(f"{topic}:{score}" for topic, score in topics.items())
