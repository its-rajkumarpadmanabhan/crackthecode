# 💀 CR@CK TH3 B0X

A thriller-themed, gamified Python-learning platform inspired by Hack The Box —
built entirely with Streamlit + SQLite.

## Features
- Signup/Login with **unique username + email**, hashed passwords (PBKDF2-SHA256)
- Login with **username OR email**
- **3 difficulty tracks**: Beginner → Intermediate → Advanced
- Each track has **3 levels**, each level has **10 questions**
- Levels **unlock sequentially** — a level only opens once the previous one is 100% complete
- Two question types: "predict the output" and "write the code" (auto-graded by safe execution)
- Per-user **progress bars** (overall + per difficulty + per level)
- **Logout** and **Delete Profile** (permanently erases account + progress)
- Hidden **Admin Panel** — only visible to the account whose username is exactly
  `r@jkum@r@@dmin0fcr@ckth3c0d3` (that account is auto-flagged admin at signup).
  Admin can see total registered users, each user's progress, and remove agents.
- Full hacker/thriller terminal visual theme (green-on-black, glowing text, mission briefings)

## Project structure
```
crackthebox/
├── app.py            # Streamlit UI + routing
├── db.py             # SQLite auth & progress logic
├── questions.py       # 90-question bank (3 difficulties x 3 levels x 10 Qs)
├── requirements.txt
├── .streamlit/config.toml   # dark hacker theme
└── data/              # SQLite db file lives here (auto-created)
```

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open http://localhost:8501

## Becoming the Admin
Simply sign up with the username `r@jkum@r@@dmin0fcr@ckth3c0d3` (any email/password) —
that exact username is auto-granted admin rights and unlocks the Admin Panel in the sidebar.

## Deploying to Streamlit Community Cloud
1. Push this folder to a **GitHub repository** (public or private).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **"New app"**, select your repo/branch, and set **Main file path** to `app.py`.
4. Click **Deploy**. Streamlit Cloud will install `requirements.txt` automatically.

### ⚠️ Important note on data persistence
Streamlit Community Cloud's filesystem is **ephemeral** — the SQLite file in `data/`
will reset whenever the app restarts/redeploys (e.g. on a new git push, or after
inactivity). This is fine for a demo/learning tool. For production use with permanent
accounts, swap `db.py`'s SQLite connection for a hosted database (e.g. Postgres via
Supabase/Neon, or `st.connection`) — the rest of the app logic stays the same since
all database access is isolated inside `db.py`.

## Tech notes
- Code-writing questions are graded by executing user code in a **restricted namespace**
  (limited builtins, no file/network/os access) and checking captured stdout — kept
  simple and sandboxed for a learning tool, not intended for untrusted multi-tenant
  production use.
- Passwords are never stored in plaintext — PBKDF2-HMAC-SHA256 with a random salt per user.
