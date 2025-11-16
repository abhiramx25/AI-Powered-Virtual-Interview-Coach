from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

DB_PATH = Path(__file__).parent / "interview_coach.db"


def get_connection() -> sqlite3.Connection:
    # check_same_thread=False is helpful for Streamlit
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            role TEXT NOT NULL,
            seniority TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            category TEXT,
            answer TEXT NOT NULL,
            clarity INTEGER,
            confidence INTEGER,
            content_score INTEGER,
            overall REAL,
            strengths TEXT,
            improvements TEXT,
            suggested_answer TEXT,
            soft_skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );
        """
    )

    conn.commit()


def create_session(user_name: str, role: str, seniority: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sessions (user_name, role, seniority)
        VALUES (?, ?, ?)
        """,
        (user_name, role, seniority),
    )
    conn.commit()
    return cur.lastrowid


def log_response(
    session_id: int,
    question: str,
    category: str,
    answer: str,
    evaluation: Dict[str, Any],
) -> None:
    scores = evaluation.get("scores", {})
    strengths = evaluation.get("strengths", [])
    improvements = evaluation.get("improvements", [])
    suggested_answer = evaluation.get("suggested_answer", "")
    soft_skills = evaluation.get("soft_skills", [])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO responses (
            session_id,
            question,
            category,
            answer,
            clarity,
            confidence,
            content_score,
            overall,
            strengths,
            improvements,
            suggested_answer,
            soft_skills
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            question,
            category,
            answer,
            scores.get("clarity"),
            scores.get("confidence"),
            scores.get("content"),
            scores.get("overall"),
            " • ".join(strengths),
            " • ".join(improvements),
            suggested_answer,
            ", ".join(soft_skills),
        ),
    )
    conn.commit()


def fetch_user_history(user_name: str) -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT
            s.id AS session_id,
            s.user_name,
            s.role,
            s.seniority,
            s.created_at AS session_created_at,
            r.id AS response_id,
            r.question,
            r.category,
            r.answer,
            r.clarity,
            r.confidence,
            r.content_score,
            r.overall,
            r.strengths,
            r.improvements,
            r.suggested_answer,
            r.soft_skills,
            r.created_at AS response_created_at
        FROM sessions s
        JOIN responses r ON s.id = r.session_id
        WHERE s.user_name = ?
        ORDER BY r.created_at ASC
    """
    df = pd.read_sql_query(query, conn, params=(user_name,))
    return df


def fetch_session_responses(session_id: int) -> pd.DataFrame:
    conn = get_connection()
    query = """
        SELECT *
        FROM responses
        WHERE session_id = ?
        ORDER BY created_at ASC
    """
    df = pd.read_sql_query(query, conn, params=(session_id,))
    return df
