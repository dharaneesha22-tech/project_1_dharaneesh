"""
Security utilities: password hashing, session management, and authorization.
"""

import bcrypt
import streamlit as st
import logging
from datetime import datetime
from utils.database import execute_query

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), hashed.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def authenticate_user(username: str, password: str):
    """
    Authenticate a user by username and password.
    Returns user dict on success, None on failure.
    """
    query = """
        SELECT u.id, u.username, u.password_hash, u.email, u.full_name,
               u.is_active, r.name AS role, u.department_id
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.username = %s AND u.is_active = TRUE
    """
    user = execute_query(query, (username,), fetch="one")
    
    if user and verify_password(password, user["password_hash"]):
        # Remove password hash from session data
        user.pop("password_hash", None)
        return user
    return None


def init_session_state():
    """Initialize Streamlit session state for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "department_id" not in st.session_state:
        st.session_state.department_id = None


def login_user(user: dict):
    """Set session state after successful login."""
    st.session_state.authenticated = True
    st.session_state.user = user
    st.session_state.role = user["role"]
    st.session_state.department_id = user.get("department_id")
    log_audit("LOGIN", user["id"], f"User {user['username']} logged in")


def logout_user():
    """Clear session state on logout."""
    if st.session_state.get("user"):
        log_audit("LOGOUT", st.session_state.user["id"],
                  f"User {st.session_state.user['username']} logged out")
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.department_id = None


def require_role(*roles):
    """
    Decorator / check function for role-based access.
    Returns True if current user has one of the required roles.
    """
    current_role = st.session_state.get("role")
    return current_role in roles


def get_current_user():
    """Return the currently logged-in user dict."""
    return st.session_state.get("user")


def get_current_role():
    """Return the current user's role string."""
    return st.session_state.get("role")


def get_current_department_id():
    """Return the department_id for the current user (faculty/HOD)."""
    return st.session_state.get("department_id")


def log_audit(action: str, user_id: int, description: str,
              target_table: str = None, target_id: int = None):
    """Insert an audit log entry."""
    try:
        query = """
            INSERT INTO audit_logs
                (user_id, action, target_table, target_id,
                 description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_query(
            query,
            (user_id, action, target_table, target_id,
             description, datetime.now()),
        )
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")
