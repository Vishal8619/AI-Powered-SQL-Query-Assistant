import sqlite3
from datetime import datetime

HISTORY_DB = "chat_history.db"


def init_history_db():
    """Create history database if not exists"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT,
            file_name TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            sql_query TEXT,
            timestamp TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()


def create_session(file_name):
    """Create a new chat session"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    session_name = f"Chat - {datetime.now().strftime('%d %b %Y %I:%M %p')}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO sessions (session_name, file_name, created_at) VALUES (?, ?, ?)",
        (session_name, file_name, created_at)
    )

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


def save_message(session_id, role, content, sql_query=None):
    """Save a single message to history"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO messages (session_id, role, content, sql_query, timestamp) VALUES (?, ?, ?, ?, ?)",
        (session_id, role, content, sql_query, timestamp)
    )

    conn.commit()
    conn.close()


def get_all_sessions():
    """Get all past sessions"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.id, s.session_name, s.file_name, s.created_at,
               COUNT(m.id) as message_count
        FROM sessions s
        LEFT JOIN messages m ON s.id = m.session_id
        GROUP BY s.id
        ORDER BY s.created_at DESC
    """)

    sessions = cursor.fetchall()
    conn.close()
    return sessions


def get_session_messages(session_id):
    """Get all messages for a session"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content, sql_query, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))

    messages = cursor.fetchall()
    conn.close()
    return messages


def delete_session(session_id):
    """Delete a session and its messages"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    conn.commit()
    conn.close()


def rename_session(session_id, new_name):
    """Rename a session"""
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE sessions SET session_name = ? WHERE id = ?",
        (new_name, session_id)
    )

    conn.commit()
    conn.close()