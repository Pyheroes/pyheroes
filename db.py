import sqlite3 as sq
import os

token = "8416634651:AAHnUBn1DuARU2_VHVhL96w5RaEgF4pJT10"
group_id = -1003509081936

# Use environment variable for DB path on Render, or default to local path
db_path = os.environ.get("DATABASE_URL", "database/bot.db")
connection = sq.connect(db_path, check_same_thread=False)

cursor = connection.cursor()


def table():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        name TEXT,
        state TEXT
    )
    """)
    connection.commit()


def set_user_state(chat_id, state):
    cursor.execute("""
        INSERT INTO users (chat_id, state)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET state=excluded.state
    """, (chat_id, state))
    connection.commit()


def get_user_state(chat_id):
    cursor.execute("SELECT state FROM users WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def set_user_name(chat_id, name):
    cursor.execute("""
        INSERT INTO users (chat_id, name)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET name=excluded.name
    """, (chat_id, name))
    connection.commit()


def get_user_name(chat_id):
    cursor.execute("SELECT name FROM users WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    return row[0] if row else None

