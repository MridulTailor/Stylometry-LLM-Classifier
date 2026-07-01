import sqlite3
import json
from datetime import datetime
import uuid

DB_PATH = "provenance.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                content_id TEXT PRIMARY KEY,
                creator_id TEXT,
                timestamp TEXT,
                attribution TEXT,
                confidence REAL,
                groq_score REAL,
                stylo_score REAL,
                status TEXT,
                creator_reasoning TEXT
            )
        """)
        conn.commit()

def log_submission(content_id, creator_id, attribution, confidence, groq_score, stylo_score, status="classified"):
    timestamp = datetime.utcnow().isoformat() + "Z"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO audit_log (content_id, creator_id, timestamp, attribution, confidence, groq_score, stylo_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_id, creator_id, timestamp, attribution, confidence, groq_score, stylo_score, status))
        conn.commit()

def update_appeal(content_id, creator_reasoning):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            UPDATE audit_log 
            SET status = 'under_review', creator_reasoning = ?
            WHERE content_id = ?
        """, (creator_reasoning, content_id))
        conn.commit()
        return cursor.rowcount > 0

def get_recent_logs(limit=10):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
