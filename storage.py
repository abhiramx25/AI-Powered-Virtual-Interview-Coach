import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any

DB_PATH = "interview_sessions.db"

def init_db(db_path: str = DB_PATH):
    """Initialize SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        role TEXT NOT NULL,
        question TEXT NOT NULL,
        user_answer TEXT NOT NULL,
        clarity INTEGER DEFAULT 0,
        confidence INTEGER DEFAULT 0,
        content INTEGER DEFAULT 0,
        critique TEXT,
        improved_answer TEXT,
        soft_skills TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def save_result(record: Dict[str, Any], db_path: str = DB_PATH):
    """Save interview session to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Convert soft_skills list to string
    soft_skills = record.get("soft_skills", [])
    soft_skills_str = ",".join(soft_skills) if isinstance(soft_skills, list) else str(soft_skills)
    
    cursor.execute("""
    INSERT INTO sessions (
        timestamp, role, question, user_answer, clarity, confidence, content, 
        critique, improved_answer, soft_skills
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        record.get("role", ""),
        record.get("question", ""),
        record.get("user_answer", ""),
        record.get("clarity", 0),
        record.get("confidence", 0),
        record.get("content", 0),
        record.get("critique", ""),
        record.get("improved_answer", ""),
        soft_skills_str
    ))
    
    conn.commit()
    conn.close()

def load_all(db_path: str = DB_PATH) -> pd.DataFrame:
    """Load all interview sessions"""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM sessions ORDER BY timestamp DESC", conn)
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()
