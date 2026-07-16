import io
import contextlib
import time
import streamlit as st

import db
from questions import get_question, get_level_questions

st.set_page_config(page_title="CR@CK TH3 B0X", page_icon="💀", layout="wide")
db.init_db()

# ----------------------------------------------------------------------------
# STYLE — hacker / thriller terminal aesthetic
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&display=swap');

html, body, [class*="css"]  {
    font-family: 'Share Tech Mono', monospace;
}
.stApp {
    background: radial-gradient(circle at 50% 0%, #0d1a0d 0%, #050705 70%);
    color: #39ff14;
}
h1, h2, h3 {
    font-family: 'VT323', monospace !important;
    color: #39ff14 !important;
    text-shadow: 0 0 8px #39ff14aa;
    letter-spacing: 2px;
}
.terminal-box {
    background: #05100599;
    border: 1px solid #39ff14;
    border-radius: 4px;
    padding: 18px 22px;
    box-shadow: 0 0 18px #39ff1433 inset, 0 0 12px #39ff1422;
    margin-bottom: 14px;
}
.mission-title {
    font-family: 'VT323', monospace;
    font-size: 30px;
    color: #ff2b2b;
    text-shadow: 0 0 10px #ff2b2baa;
}
.code-block {
    background: #000;
    border-left: 3px solid #39ff14;
    padding: 12px 16px;
    font-family: 'Share Tech Mono', monospace;
    color: #b6ffb6;
    white-space: pre;
    overflow-x: auto;
}
.locked-badge {
    color: #ff2b2b; border:1px solid #ff2b2b; padding:2px 10px; border-radius: 12px; font-size:12px;
}
.unlocked-badge {
    color: #39ff14; border:1px solid #39ff14; padding:2px 10px; border-radius: 12px; font-size:12px;
}
.stButton>button {
    background: #061006;
    color: #39ff14;
    border: 1px solid #39ff14;
    font-family: 'Share Tech Mono', monospace;
    border-radius: 3px;
}
.stButton>button:hover {
    background: #39ff14;
    color: #000;
    box-shadow: 0 0 14px #39ff14;
}
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    background: #020602 !important;
    color: #39ff14 !important;
    border: 1px solid #145214 !important;
    font-family: 'Share Tech Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "nav" not in st.session_state:
    st.session_state.nav = "dashboard"
if "active_difficulty" not in st.session_state:
    st.session_state.active_difficulty = None
if "active_level" not in st.session_state:
    st.session_state.active_level = None
if "feedback" not in st.session_state:
    st.session_state.feedback = None

DIFF_ICON = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}


def code_grader(user_code: str, check_fn):
    """Executes user code in a restricted namespace, captures stdout, applies check_fn."""
    safe_builtins = {
        "print": print, "range": range, "len": len, "sum": sum, "min": min, "max": max,
        "sorted": sorted, "list": list, "dict": dict, "set": set, "tuple": tuple, "str": str,
        "int": int, "float": float, "bool": bool, "enumerate": enumerate, "zip": zip,
        "map": map, "filter": filter, "abs": abs, "round": round, "reversed": reversed,
        "isinstance": isinstance, "type": type, "Exception": Exception, "ValueError": ValueError,
        "TypeError": TypeError, "StopIteration": StopIteration, "next": next, "iter": iter,
        "staticmethod": staticmethod, "property": property, "super": super,
        "__import__": __import__,
    }
    ns = {"__builtins__": safe_builtins}
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            exec(user_code, ns)
        output = stdout.getvalue()
        ok = check_fn(output, ns)
        return ok, output, None
    except Exception as e:
        return False, stdout.getvalue(), str(e)


# ----------------------------------------------------------------------------
# AUTH SCREENS
# ----------------------------------------------------------------------------
def auth_screen():
    st.markdown("<h1>💀 CR@CK TH3 B0X</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='terminal-box'>SYSTEM ONLINE... AWAITING AGENT CREDENTIALS.<br>"
        "Learn Python from scratch to advanced by breaching one level at a time.</div>",
        unsafe_allow_html=True,
    )
    tab_login, tab_signup = st.tabs(["🔓 LOGIN", "🆕 SIGN UP"])

    with tab_login:
        with st.form("login_form"):
            identifier = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("BREACH SYSTEM →")
            if submitted:
                user = db.authenticate(identifier.strip(), password)
                if user:
                    st.session_state.user = user
                    st.session_state.nav = "dashboard"
                    st.success(f"ACCESS GRANTED. Welcome back, {user['username']}.")
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error("ACCESS DENIED. Invalid credentials.")

    with tab_signup:
        with st.form("signup_form"):
            username = st.text_input("Choose a Username (unique)")
            email = st.text_input("Email (unique)")
            password = st.text_input("Choose a Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("CREATE AGENT PROFILE →")
            if submitted:
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = db.create_user(username.strip(), email.strip(), password)
                    if ok:
                        st.success(msg + " Switch to the LOGIN tab.")
                    else:
                        st.error(msg)


# ----------------------------------------------------------------------------
# SIDEBAR NAV
# ----------------------------------------------------------------------------
def sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 🕵️ AGENT: `{user['username']}`")
        st.caption(user["email"])
        done, total = db.get_overall_progress(user["id"])
        pct = done / total if total else 0
        st.progress(pct, text=f"Overall Progress: {done}/{total} ({int(pct*100)}%)")
        st.markdown("---")
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.nav = "dashboard"
            st.session_state.active_difficulty = None
            st.rerun()
        if st.button("📊 My Progress", use_container_width=True):
            st.session_state.nav = "progress"
            st.rerun()
        if user["is_admin"]:
            if st.button("🛡️ Admin Panel", use_container_width=True):
                st.session_state.nav = "admin"
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.nav = "dashboard"
            st.rerun()
        with st.expander("⚠️ Delete Profile"):
            st.warning("This permanently erases your agent profile and all progress.")
            confirm_del = st.text_input("Type DELETE to confirm", key="del_confirm")
            if st.button("💣 Permanently Delete Account"):
                if confirm_del == "DELETE":
                    db.delete_user(user["id"])
                    st.session_state.user = None
                    st.success("Profile terminated.")
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.error("Type DELETE exactly to confirm.")


# ----------------------------------------------------------------------------
# DASHBOARD — choose difficulty
# ----------------------------------------------------------------------------
def dashboard():
    st.markdown("<h1>🎯 MISSION CONTROL</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='terminal-box'>Select a difficulty track to begin infiltration. "
        "Complete all questions in a level to unlock the next one.</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for col, diff in zip(cols, db.DIFFICULTIES):
        done, total = db.get_difficulty_progress(st.session_state.user["id"], diff)
        with col:
            st.markdown(f"""
            <div class='terminal-box'>
            <div class='mission-title'>{DIFF_ICON[diff]} {diff.upper()}</div>
            <p>{diff} track — {db.LEVELS_PER_DIFFICULTY} levels × {db.QUESTIONS_PER_LEVEL} questions</p>
            </div>
            """, unsafe_allow_html=True)
            st.progress(done / total if total else 0, text=f"{done}/{total} solved")
            if st.button(f"ENTER {diff.upper()} TRACK", key=f"enter_{diff}", use_container_width=True):
                st.session_state.active_difficulty = diff
                st.session_state.nav = "levels"
                st.rerun()


# ----------------------------------------------------------------------------
# LEVEL SELECT
# ----------------------------------------------------------------------------
def levels_screen():
    diff = st.session_state.active_difficulty
    user = st.session_state.user
    st.markdown(f"<h1>{DIFF_ICON[diff]} {diff.upper()} TRACK</h1>", unsafe_allow_html=True)
    if st.button("← Back to Mission Control"):
        st.session_state.nav = "dashboard"
        st.rerun()

    for lvl in range(1, db.LEVELS_PER_DIFFICULTY + 1):
        unlocked = db.is_level_unlocked(user["id"], diff, lvl)
        prog = db.get_progress(user["id"], diff, lvl)
        badge = "<span class='unlocked-badge'>UNLOCKED</span>" if unlocked else "<span class='locked-badge'>LOCKED</span>"
        status = "✅ COMPLETED" if prog["completed"] else f"Question {prog['current_question']}/{db.QUESTIONS_PER_LEVEL}"
        st.markdown(f"""
        <div class='terminal-box'>
        <div class='mission-title'>LEVEL {lvl} {badge}</div>
        <p>{status}</p>
        </div>
        """, unsafe_allow_html=True)
        if unlocked:
            label = "REVIEW LEVEL" if prog["completed"] else "CONTINUE MISSION →"
            if st.button(label, key=f"lvl_{lvl}"):
                st.session_state.active_level = lvl
                st.session_state.nav = "play"
                st.session_state.feedback = None
                st.rerun()
        else:
            st.caption("🔒 Complete the previous level to unlock.")


# ----------------------------------------------------------------------------
# PLAY SCREEN — question by question
# ----------------------------------------------------------------------------
def play_screen():
    diff = st.session_state.active_difficulty
    lvl = st.session_state.active_level
    user = st.session_state.user
    prog = db.get_progress(user["id"], diff, lvl)

    if prog["completed"]:
        st.markdown("<h1>🏁 LEVEL CLEARED</h1>", unsafe_allow_html=True)
        st.balloons()
        st.markdown(
            f"<div class='terminal-box'>Mission accomplished. Level {lvl} of the {diff} track is fully breached.</div>",
            unsafe_allow_html=True,
        )
        if st.button("← Back to Level Select"):
            st.session_state.nav = "levels"
            st.rerun()
        return

    q_index = prog["current_question"]
    q = get_question(diff, lvl, q_index)

    st.markdown(f"<h1>🎯 {diff.upper()} — LEVEL {lvl}</h1>", unsafe_allow_html=True)
    st.progress(q_index / db.QUESTIONS_PER_LEVEL, text=f"Question {q_index}/{db.QUESTIONS_PER_LEVEL}")
    st.markdown(f"<div class='mission-title'>🎬 {q['title']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='terminal-box'>{q['briefing']}</div>", unsafe_allow_html=True)

    if q["type"] == "output":
        st.markdown("**Intercepted code:**")
        st.markdown(f"<div class='code-block'>{q['code_snippet']}</div>", unsafe_allow_html=True)
        st.caption(f"Sample-style output format: {q['sample_output']}  *(illustrative — exact wording may vary)*")
        answer = st.text_input("🔑 Your predicted output:", key=f"ans_{diff}_{lvl}_{q_index}")
        submit = st.button("SUBMIT →", key=f"submit_{diff}_{lvl}_{q_index}")
        if submit:
            normalized = " ".join(answer.strip().split()).lower()
            accepted = [" ".join(a.split()).lower() for a in q["accepted_answers"]]
            if normalized in accepted:
                db.advance_question(user["id"], diff, lvl)
                st.success("✅ CORRECT — Access granted to next node.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ INCORRECT. Node remains locked. Try again.")
                if q.get("hint"):
                    st.info(f"💡 Hint: {q['hint']}")

    else:  # code type
        st.markdown(f"**Task:** {q['task']}")
        st.caption(f"Sample-style output format: {q['sample_output']}  *(illustrative — exact wording may vary)*")
        code_input = st.text_area("💻 Write your Python code:", value=q.get("starter_code", ""),
                                   height=180, key=f"code_{diff}_{lvl}_{q_index}")
        submit = st.button("EXECUTE & SUBMIT →", key=f"submit_{diff}_{lvl}_{q_index}")
        if submit:
            ok, output, err = code_grader(code_input, q["check"])
            if err:
                st.error(f"⚠️ RUNTIME ERROR: {err}")
            elif ok:
                db.advance_question(user["id"], diff, lvl)
                st.success("✅ CORRECT — Access granted to next node.")
                if output.strip():
                    st.code(output)
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ INCORRECT OUTPUT. Node remains locked. Try again.")
                if output.strip():
                    st.caption("Your output:")
                    st.code(output)
                if q.get("hint"):
                    st.info(f"💡 Hint: {q['hint']}")

    st.markdown("---")
    if st.button("← Back to Level Select"):
        st.session_state.nav = "levels"
        st.rerun()


# ----------------------------------------------------------------------------
# PROGRESS SCREEN
# ----------------------------------------------------------------------------
def progress_screen():
    user = st.session_state.user
    st.markdown("<h1>📊 AGENT DOSSIER</h1>", unsafe_allow_html=True)
    done, total = db.get_overall_progress(user["id"])
    st.progress(done / total if total else 0, text=f"Overall: {done}/{total} questions cracked")

    for diff in db.DIFFICULTIES:
        d_done, d_total = db.get_difficulty_progress(user["id"], diff)
        st.markdown(f"#### {DIFF_ICON[diff]} {diff}")
        st.progress(d_done / d_total if d_total else 0, text=f"{d_done}/{d_total}")
        cols = st.columns(db.LEVELS_PER_DIFFICULTY)
        for i, lvl in enumerate(range(1, db.LEVELS_PER_DIFFICULTY + 1)):
            prog = db.get_progress(user["id"], diff, lvl)
            with cols[i]:
                state = "✅ Done" if prog["completed"] else ("🔓 In progress" if db.is_level_unlocked(user["id"], diff, lvl) else "🔒 Locked")
                st.markdown(f"**Level {lvl}**: {state}")


# ----------------------------------------------------------------------------
# ADMIN SCREEN
# ----------------------------------------------------------------------------
def admin_screen():
    user = st.session_state.user
    if not user["is_admin"]:
        st.error("ACCESS DENIED.")
        return
    st.markdown("<h1>🛡️ ADMIN CONTROL ROOM</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='terminal-box'>Total registered agents: <b>{db.user_count()}</b></div>",
                unsafe_allow_html=True)
    users = db.all_users()
    for u in users:
        done, total = db.get_overall_progress(u["id"])
        with st.expander(f"👤 {u['username']}  ({u['email']})" + ("  🛡️ ADMIN" if u["is_admin"] else "")):
            st.write(f"Joined: {u['created_at']}")
            st.progress(done / total if total else 0, text=f"Progress: {done}/{total}")
            if not u["is_admin"]:
                if st.button(f"🗑️ Remove Agent {u['username']}", key=f"admin_del_{u['id']}"):
                    db.delete_user(u["id"])
                    st.rerun()


# ----------------------------------------------------------------------------
# ROUTER
# ----------------------------------------------------------------------------
if st.session_state.user is None:
    auth_screen()
else:
    sidebar()
    nav = st.session_state.nav
    if nav == "dashboard":
        dashboard()
    elif nav == "levels":
        levels_screen()
    elif nav == "play":
        play_screen()
    elif nav == "progress":
        progress_screen()
    elif nav == "admin":
        admin_screen()
    else:
        dashboard()
