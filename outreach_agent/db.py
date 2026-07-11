import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from models import Prospect, GapSignal, Draft

DB_PATH = Path(__file__).parent / "data" / "outreach.db"

def init_db():
    """Initializes the database schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prospect_name TEXT,
                company TEXT,
                title TEXT,
                timestamp TEXT,
                gap_signals_json TEXT,
                gap_chosen_json TEXT,
                draft_subject TEXT,
                draft_body TEXT,
                human_decision TEXT,
                final_draft_text TEXT
            )
        ''')
        conn.commit()

def log_run(
    prospect: Prospect,
    timestamp: str,
    gap_signals: List[GapSignal],
    gap_chosen: Optional[GapSignal],
    draft: Optional[Draft],
    human_decision: str,
    final_draft_text: Optional[str]
) -> int:
    """Logs a full run into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        gap_signals_json = json.dumps([g.model_dump() for g in gap_signals]) if gap_signals else "[]"
        gap_chosen_json = json.dumps(gap_chosen.model_dump()) if gap_chosen else None
        
        draft_subject = draft.subject if draft else None
        draft_body = draft.body if draft else None

        cursor.execute('''
            INSERT INTO runs (
                prospect_name, company, title, timestamp, 
                gap_signals_json, gap_chosen_json, 
                draft_subject, draft_body, 
                human_decision, final_draft_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prospect.name, prospect.company, prospect.title, timestamp,
            gap_signals_json, gap_chosen_json,
            draft_subject, draft_body,
            human_decision, final_draft_text
        ))
        conn.commit()
        return cursor.lastrowid

# Initialize DB on import
init_db()
