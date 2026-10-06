"""
College Smart Placement Management System
==========================================
Main entry point.  Run with:
    streamlit run streamlit_app.py

Roles: ADMIN | HOD | FACULTY | STUDENT
"""

import sys
import os

# ── Ensure imports resolve from the project root ──────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page configuration (must be the very first Streamlit call) ─────────────
st.set_page_config(
    page_title="Smart Placement Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "College Smart Placement Management System v1.0",
    },
)

# ── Global CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Layout ── */
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p { color: #d0d8f0 !important; }
    section[data-testid="stSidebar"] b { color: #ffffff !important; }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #1e3c72;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] { border-radius: 8px; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 0.4rem 1rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #1e3c72 !important;
        color: white !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        border: none;
        color: white;
    }

    /* ── Divider ── */
    hr { margin: 0.8rem 0; border-color: #e0e0e0; }

    /* ── Hide default Streamlit branding ── */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state init ─────────────────────────────────────────────────────
from utils.security import init_session_state
init_session_state()


# ── Database connectivity check ────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _check_db():
    """Check DB connectivity once per session (cached)."""
    try:
        from utils.database import test_connection
        return test_connection()
    except Exception as e:
        return False, str(e)


def _show_db_error(msg: str):
    """Display a clear, actionable MySQL connection error page."""
    from utils.database import get_db_config_summary

    st.error("🔌 Cannot connect to MySQL — the app cannot start without a database.")

    # Show exactly what config was attempted
    try:
        cfg_summary = get_db_config_summary()
    except Exception:
        cfg_summary = "Could not read config"

    st.markdown(
        f"""
        <div style='background:#fff3cd; border:1px solid #ffc107;
                    border-radius:8px; padding:1rem; margin:0.5rem 0;'>
            <b>Connection attempted with:</b><br>
            <code>{cfg_summary}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🔍 Error Details", expanded=True):
        st.code(msg, language="text")

    st.markdown("---")
    st.markdown("## 🛠️ How to fix this on Windows")

    st.markdown("""
### Step 1 — Start MySQL

**Option A — Services (recommended):**
1. Press **Win + R**, type `services.msc`, press Enter
2. Find **MySQL80** (or MySQL57 / MySQL)
3. Right-click → **Start**

**Option B — Command Prompt (run as Administrator):**
```
net start MySQL80
```
*(Replace `MySQL80` with your MySQL service name if different)*

**Option C — XAMPP / WAMP:**
Open XAMPP Control Panel → click **Start** next to MySQL

---

### Step 2 — Set your password in `.env`

Open the file:
```
c:\\project_1\\placement_management\\.env
```

Edit it to match your MySQL credentials:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=placement_management
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
```
> Leave `DB_PASSWORD=` blank only if your MySQL root has **no password set**.

---

### Step 3 — Create the database (first time only)

Open a terminal in the project folder and run:
```
cd c:\\project_1\\placement_management
python setup_db.py
```
This creates the database, all tables, and loads sample data.

---

### Step 4 — Restart the app

```
streamlit run streamlit_app.py
```

Then refresh this browser page.
""")

    st.markdown("---")
    st.info(
        "💡 **Quick check:** Open MySQL Workbench or run `mysql -u root -p` "
        "in a terminal. If it connects, MySQL is running and your credentials are correct."
    )
    st.stop()


# ── Routing ────────────────────────────────────────────────────────────────

def _sidebar_header():
    """Render the sidebar logo/header."""
    st.sidebar.markdown(
        """
        <div style='text-align:center; padding:1rem 0;'>
            <div style='font-size:2.5rem;'>🎓</div>
            <div style='font-size:1rem; font-weight:700; color:white;'>
                Smart Placement Portal
            </div>
            <div style='font-size:0.75rem; color:#b0c4de;'>
                Placement Management System
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()


def main():
    # ── Database check ────────────────────────────────────────────────
    ok, msg = _check_db()
    if not ok:
        _show_db_error(msg)

    # ── Not logged in → show login ─────────────────────────────────────
    if not st.session_state.authenticated:
        from modules.auth import show_login_page
        show_login_page()
        return

    # ── Logged in → route to role dashboard ───────────────────────────
    _sidebar_header()

    from modules.auth import show_logout_button
    show_logout_button()

    role = st.session_state.role

    if role == "STUDENT":
        from modules.student import show_student_dashboard
        show_student_dashboard()

    elif role == "FACULTY":
        from modules.faculty import show_faculty_dashboard
        show_faculty_dashboard()

    elif role == "HOD":
        from modules.hod import show_hod_dashboard
        show_hod_dashboard()

    elif role == "ADMIN":
        from modules.admin import show_admin_dashboard
        show_admin_dashboard()

    else:
        st.error(f"Unknown role '{role}'. Contact system administrator.")

    # ── Footer ────────────────────────────────────────────────────────
    st.sidebar.markdown(
        "<div style='position:fixed; bottom:1rem; left:0; right:0; "
        "text-align:center; font-size:0.7rem; color:#b0c4de;'>"
        "Smart Placement Portal v1.0<br>© 2026 College ERP</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
