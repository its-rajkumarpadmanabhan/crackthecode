"""
CR@CK TH3 B0X — Database Layer
Handles user accounts, authentication, and progress tracking using SQLite.
"""
import sqlite3
import hashlib
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "crackthebox.db")
ADMIN_USERNAME = "r@jkum@r@@dmin0fcr@ckth3c0d3"

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
LEVELS_PER_DIFFICULTY = 3
QUESTIONS_PER_LEVEL = 10


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            difficulty TEXT NOT NULL,
            level INTEGER NOT NULL,
            current_question INTEGER DEFAULT 1,
            completed INTEGER DEFAULT 0,
            UNIQUE(user_id, difficulty, level),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


# ---------- password hashing ----------
def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


def _make_salt() -> str:
    return os.urandom(16).hex()


# ---------- validation ----------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


def is_valid_username(username: str) -> bool:
    if not username or len(username) < 3:
        return False
    return True


# ---------- user management ----------
def username_exists(username: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row is not None


def email_exists(email: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row is not None


def create_user(username: str, email: str, password: str):
    """Returns (success: bool, message: str)"""
    if not is_valid_username(username):
        return False, "Username must be at least 3 characters."
    if not is_valid_email(email):
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if username_exists(username):
        return False, "That username is already taken. Choose another."
    if email_exists(email):
        return False, "An account with that email already exists."

    salt = _make_salt()
    pw_hash = _hash_password(password, salt)
    is_admin = 1 if username == ADMIN_USERNAME else 0

    conn = get_conn()
    conn.execute(
        "INSERT INTO users (username, email, password_hash, salt, is_admin, created_at) VALUES (?,?,?,?,?,?)",
        (username, email, pw_hash, salt, is_admin, datetime.utcnow().isoformat()),
    )
    conn.commit()
    user_id = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()["id"]
    conn.close()

    # seed progress rows
    for diff in DIFFICULTIES:
        for lvl in range(1, LEVELS_PER_DIFFICULTY + 1):
            _seed_progress(user_id, diff, lvl)

    return True, "Account created! You can now log in."


def _seed_progress(user_id, difficulty, level):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO progress (user_id, difficulty, level, current_question, completed) VALUES (?,?,?,1,0)",
        (user_id, difficulty, level),
    )
    conn.commit()
    conn.close()


def authenticate(identifier: str, password: str):
    """identifier = username or email. Returns user row dict or None."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    if _hash_password(password, row["salt"]) == row["password_hash"]:
        return dict(row)
    return None


def get_user_by_id(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_user(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM progress WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def all_users():
    conn = get_conn()
    rows = conn.execute("SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def user_count():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    conn.close()
    return n


# ---------- progress management ----------
def get_progress(user_id, difficulty, level):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM progress WHERE user_id=? AND difficulty=? AND level=?",
        (user_id, difficulty, level),
    ).fetchone()
    conn.close()
    if row is None:
        _seed_progress(user_id, difficulty, level)
        return {"current_question": 1, "completed": 0}
    return dict(row)


def is_level_unlocked(user_id, difficulty, level):
    """Level 1 always unlocked. Level N unlocked if level N-1 is completed."""
    if level == 1:
        return True
    prev = get_progress(user_id, difficulty, level - 1)
    return bool(prev["completed"])


def advance_question(user_id, difficulty, level):
    """Call after a correct answer. Moves to next question or marks level completed."""
    prog = get_progress(user_id, difficulty, level)
    cur_q = prog["current_question"]
    conn = get_conn()
    if cur_q >= QUESTIONS_PER_LEVEL:
        conn.execute(
            "UPDATE progress SET completed=1 WHERE user_id=? AND difficulty=? AND level=?",
            (user_id, difficulty, level),
        )
    else:
        conn.execute(
            "UPDATE progress SET current_question=? WHERE user_id=? AND difficulty=? AND level=?",
            (cur_q + 1, user_id, difficulty, level),
        )
    conn.commit()
    conn.close()


def get_overall_progress(user_id):
    """Returns (questions_completed, total_questions) across all difficulties/levels."""
    total = len(DIFFICULTIES) * LEVELS_PER_DIFFICULTY * QUESTIONS_PER_LEVEL
    done = 0
    for diff in DIFFICULTIES:
        for lvl in range(1, LEVELS_PER_DIFFICULTY + 1):
            prog = get_progress(user_id, diff, lvl)
            if prog["completed"]:
                done += QUESTIONS_PER_LEVEL
            else:
                done += prog["current_question"] - 1
    return done, total


def get_difficulty_progress(user_id, difficulty):
    total = LEVELS_PER_DIFFICULTY * QUESTIONS_PER_LEVEL
    done = 0
    for lvl in range(1, LEVELS_PER_DIFFICULTY + 1):
        prog = get_progress(user_id, difficulty, lvl)
        if prog["completed"]:
            done += QUESTIONS_PER_LEVEL
        else:
            done += prog["current_question"] - 1
    return done, total
