"""
Admin dashboard module — full college access.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import execute_query
from utils.security import get_current_user, hash_password, log_audit
from utils.validators import validate_email, sanitize_string
from modules.placements import show_drives_page
from modules.companies import show_companies_page


# ─── DATA ACCESS ─────────────────────────────────────────────────────────────

def get_college_stats():
    """Return overall college placement statistics."""
    return execute_query(
        """
        SELECT
            (SELECT COUNT(*) FROM students WHERE is_active=TRUE)    AS total_students,
            (SELECT COUNT(*) FROM departments)                       AS total_departments,
            (SELECT COUNT(*) FROM companies)                         AS total_companies,
            COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                THEN s.id END)                       AS total_placed,
            (SELECT COUNT(*) FROM students WHERE is_active=TRUE) -
            COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                THEN s.id END)                       AS total_not_placed,
            ROUND(
                COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                    THEN s.id END) * 100.0 /
                NULLIF((SELECT COUNT(*) FROM students WHERE is_active=TRUE), 0),
                2
            )                                                        AS overall_placement_pct,
            MAX(pr.package_lpa)                                      AS highest_package,
            ROUND(AVG(CASE WHEN pr.status='Selected'
                           THEN pr.package_lpa END), 2)              AS avg_package,
            COUNT(DISTINCT pr.id)                                    AS total_offers
        FROM students s
        LEFT JOIN placement_results pr ON s.id = pr.student_id
        WHERE s.is_active = TRUE
        """,
        fetch="one",
    ) or {}


def get_department_stats_all():
    """Department-wise placement statistics."""
    return execute_query(
        "SELECT * FROM v_department_stats ORDER BY department",
        fetch="all",
    ) or []


def get_all_users():
    return execute_query(
        """
        SELECT u.id, u.username, u.full_name, u.email,
               r.name AS role, d.name AS department, u.is_active,
               u.created_at
        FROM users u
        JOIN roles r ON u.role_id = r.id
        LEFT JOIN departments d ON u.department_id = d.id
        ORDER BY r.name, u.full_name
        """,
        fetch="all",
    ) or []


def get_all_students(search: str = "", dept_id: int = None,
                     placement_status: str = None):
    query = """
        SELECT s.register_number, s.full_name, s.email,
               d.name AS department, ar.cgpa, ar.arrears,
               s.batch_year, v.companies_attended,
               v.companies_selected, v.placement_status,
               v.highest_package
        FROM students s
        JOIN departments d ON s.department_id = d.id
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
        WHERE s.is_active = TRUE
    """
    params = []
    if search:
        query += " AND (s.full_name LIKE %s OR s.register_number LIKE %s)"
        params += [f"%{search}%", f"%{search}%"]
    if dept_id:
        query += " AND s.department_id = %s"
        params.append(dept_id)
    if placement_status and placement_status != "All":
        query += " AND v.placement_status = %s"
        params.append(placement_status)
    query += " ORDER BY d.name, s.register_number"
    return execute_query(query, tuple(params), fetch="all") or []


def add_user(data: dict):
    """Create a new user (admin action)."""
    execute_query(
        """
        INSERT INTO users
            (username, password_hash, email, full_name, role_id, department_id)
        VALUES (%s,%s,%s,%s,
                (SELECT id FROM roles WHERE name=%s),
                %s)
        """,
        (
            sanitize_string(data["username"]),
            hash_password(data["password"]),
            sanitize_string(data["email"]),
            sanitize_string(data["full_name"]),
            data["role"],
            data.get("department_id"),
        ),
    )
    user = get_current_user()
    if user:
        log_audit("USER_CREATED", user["id"],
                  f"User '{data['username']}' ({data['role']}) created")


def toggle_user_status(user_id: int, is_active: bool):
    execute_query(
        "UPDATE users SET is_active=%s WHERE id=%s",
        (is_active, user_id),
    )
    user = get_current_user()
    if user:
        status_str = "activated" if is_active else "deactivated"
        log_audit("USER_TOGGLED", user["id"],
                  f"User {user_id} {status_str}", "users", user_id)


def add_department(name: str, code: str):
    execute_query(
        "INSERT INTO departments (name, code) VALUES (%s,%s)",
        (sanitize_string(name), sanitize_string(code)),
    )


def get_audit_logs(limit: int = 100):
    return execute_query(
        """
        SELECT al.created_at, u.username, al.action,
               al.target_table, al.description
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT %s
        """,
        (limit,),
        fetch="all",
    ) or []


# ─── Streamlit Dashboard ─────────────────────────────────────────────────────

def show_admin_dashboard():
    """Render the Admin dashboard."""
    user = get_current_user()

    st.sidebar.markdown(f"### 🔑 {user['full_name']}")
    st.sidebar.markdown("**Role:** System Administrator")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👥 Students",
            "🏢 Companies",
            "📅 Placement Drives",
            "👤 User Management",
            "🏛️ Departments",
            "📈 Analytics",
            "📄 Reports",
            "📋 Audit Logs",
        ],
    )

    if page == "🏠 Dashboard":
        _show_admin_home()
    elif page == "👥 Students":
        _show_all_students()
    elif page == "🏢 Companies":
        show_companies_page(can_edit=True)
    elif page == "📅 Placement Drives":
        show_drives_page(can_edit=True)
    elif page == "👤 User Management":
        _show_user_management()
    elif page == "🏛️ Departments":
        _show_departments()
    elif page == "📈 Analytics":
        from modules.analytics import show_analytics_page
        show_analytics_page()
    elif page == "📄 Reports":
        from modules.reports import show_college_report
        show_college_report()
    elif page == "📋 Audit Logs":
        _show_audit_logs()


def _show_admin_home():
    """Admin dashboard overview page."""
    st.markdown("## 🎓 College Placement Dashboard")
    stats = get_college_stats()

    # ── Top KPI Row ──
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Students",   stats.get("total_students", 0))
    col2.metric("Departments",       stats.get("total_departments", 0))
    col3.metric("Companies",         stats.get("total_companies", 0))
    col4.metric("Total Placed",      stats.get("total_placed", 0))
    col5.metric("Total Offers",      stats.get("total_offers", 0))

    col6, col7, col8 = st.columns(3)
    col6.metric("Overall Placement %",
                f"{stats.get('overall_placement_pct', 0) or 0:.1f}%")
    col7.metric("Highest Package",
                f"₹{stats.get('highest_package', 0) or 0} LPA")
    col8.metric("Avg Package",
                f"₹{stats.get('avg_package', 0) or 0:.2f} LPA")

    st.divider()

    # ── Department Table ──
    st.markdown("### 📊 Department-wise Placement Summary")
    dept_stats = get_department_stats_all()
    if dept_stats:
        df = pd.DataFrame(dept_stats)
        display_cols = ["department", "total_students", "placed_students",
                        "not_placed_students", "placement_percentage",
                        "highest_package", "avg_package"]
        df = df[[c for c in display_cols if c in df.columns]]
        df.rename(columns={
            "department": "Department",
            "total_students": "Total",
            "placed_students": "Placed",
            "not_placed_students": "Not Placed",
            "placement_percentage": "Placement %",
            "highest_package": "Highest Pkg",
            "avg_package": "Avg Pkg",
        }, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Department comparison bar chart
        fig = px.bar(
            df,
            x="Department",
            y=["Placed", "Not Placed"],
            barmode="stack",
            title="Department-wise Placement",
            color_discrete_sequence=["#28a745", "#dc3545"],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No department statistics available.")


def _show_all_students():
    """Admin view of all students with filters."""
    st.markdown("## 👥 All Students")
    departments = execute_query(
        "SELECT id, name FROM departments ORDER BY name", fetch="all"
    ) or []

    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Search name/reg no")
    with col2:
        dept_opts = {0: "All Departments"}
        dept_opts.update({d["id"]: d["name"] for d in departments})
        dept_filter = st.selectbox(
            "Department",
            list(dept_opts.keys()),
            format_func=lambda k: dept_opts[k],
        )
    with col3:
        status_filter = st.selectbox(
            "Placement Status",
            ["All", "Placed", "Not Placed"],
        )

    students = get_all_students(
        search=search,
        dept_id=dept_filter if dept_filter else None,
        placement_status=status_filter,
    )

    if not students:
        st.info("No students match the filters.")
        return

    df = pd.DataFrame(students)
    rename = {
        "register_number": "Reg No", "full_name": "Name",
        "email": "Email", "department": "Department",
        "cgpa": "CGPA", "arrears": "Arrears",
        "batch_year": "Batch", "companies_attended": "Attended",
        "companies_selected": "Selected",
        "placement_status": "Status", "highest_package": "Highest Pkg",
    }
    df.rename(columns=rename, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total: {len(df)} students**")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export CSV", csv, "all_students.csv", "text/csv")


def _show_user_management():
    """Admin user management page."""
    st.markdown("## 👤 User Management")
    tabs = st.tabs(["📋 All Users", "➕ Add User", "🔧 Manage Access"])

    with tabs[0]:
        users = get_all_users()
        if users:
            df = pd.DataFrame(users)
            df = df[["username", "full_name", "role",
                     "department", "is_active", "created_at"]]
            df.columns = ["Username", "Full Name", "Role",
                          "Department", "Active", "Created"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[1]:
        _show_add_user_form()

    with tabs[2]:
        _show_manage_access()


def _show_add_user_form():
    """Form to add a new user."""
    departments = execute_query(
        "SELECT id, name FROM departments ORDER BY name", fetch="all"
    ) or []

    with st.form("add_user_form"):
        st.markdown("### Add New User")
        col1, col2 = st.columns(2)
        with col1:
            username  = st.text_input("Username *")
            full_name = st.text_input("Full Name *")
            email     = st.text_input("Email *")
        with col2:
            role = st.selectbox("Role", ["FACULTY", "HOD", "ADMIN", "STUDENT"])
            dept_opts = {0: "— None —"}
            dept_opts.update({d["id"]: d["name"] for d in departments})
            dept_id = st.selectbox(
                "Department",
                list(dept_opts.keys()),
                format_func=lambda k: dept_opts[k],
            )
            password = st.text_input("Password *", type="password",
                                     value="Faculty@123")

        if st.form_submit_button("➕ Create User"):
            errors = []
            if not username.strip():
                errors.append("Username required.")
            if not validate_email(email):
                errors.append("Invalid email.")
            if len(password) < 6:
                errors.append("Password too short.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                existing = execute_query(
                    "SELECT id FROM users WHERE username=%s OR email=%s",
                    (username, email), fetch="one"
                )
                if existing:
                    st.error("Username or email already exists.")
                else:
                    add_user({
                        "username": username, "full_name": full_name,
                        "email": email, "role": role,
                        "department_id": dept_id if dept_id else None,
                        "password": password,
                    })
                    st.success(f"User '{username}' created successfully!")
                    st.rerun()


def _show_manage_access():
    """Enable/disable user accounts."""
    users = get_all_users()
    if not users:
        st.info("No users found.")
        return
    user_labels = [
        f"{u['username']} ({u['role']}) — {'Active' if u['is_active'] else 'Inactive'}"
        for u in users
    ]
    idx = st.selectbox("Select user", range(len(user_labels)),
                       format_func=lambda i: user_labels[i])
    sel_user = users[idx]
    st.markdown(
        f"**User:** {sel_user['full_name']}  |  "
        f"**Status:** {'🟢 Active' if sel_user['is_active'] else '🔴 Inactive'}"
    )
    current = st.session_state.get("user", {})
    if sel_user["id"] == current.get("id"):
        st.warning("You cannot modify your own account status.")
        return
    col1, col2 = st.columns(2)
    with col1:
        if not sel_user["is_active"]:
            if st.button("✅ Activate User"):
                toggle_user_status(sel_user["id"], True)
                st.success("User activated!")
                st.rerun()
    with col2:
        if sel_user["is_active"]:
            if st.button("🚫 Deactivate User"):
                toggle_user_status(sel_user["id"], False)
                st.success("User deactivated!")
                st.rerun()


def _show_departments():
    """Department management page."""
    st.markdown("## 🏛️ Department Management")
    depts = execute_query(
        "SELECT * FROM departments ORDER BY name", fetch="all"
    ) or []

    if depts:
        df = pd.DataFrame(depts)
        df = df[["id", "name", "code", "created_at"]]
        df.columns = ["ID", "Department Name", "Code", "Created"]
        st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("➕ Add Department"):
        with st.form("add_dept_form"):
            col1, col2 = st.columns(2)
            with col1:
                dept_name = st.text_input("Department Name *")
            with col2:
                dept_code = st.text_input("Department Code *",
                                          placeholder="e.g. ECE")
            if st.form_submit_button("Add Department"):
                if dept_name.strip() and dept_code.strip():
                    existing = execute_query(
                        "SELECT id FROM departments WHERE code=%s",
                        (dept_code.upper(),), fetch="one"
                    )
                    if existing:
                        st.error("Department code already exists.")
                    else:
                        add_department(dept_name, dept_code.upper())
                        st.success(f"Department '{dept_name}' added!")
                        st.rerun()
                else:
                    st.error("Both name and code are required.")


def _show_audit_logs():
    """Admin audit log viewer."""
    st.markdown("## 📋 Audit Logs")
    limit = st.number_input("Number of records", 10, 1000, 100, 10)
    logs = get_audit_logs(int(limit))

    if not logs:
        st.info("No audit logs found.")
        return

    df = pd.DataFrame(logs)
    df.columns = ["Timestamp", "User", "Action", "Table", "Description"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export Audit Log", csv,
                       "audit_log.csv", "text/csv")
