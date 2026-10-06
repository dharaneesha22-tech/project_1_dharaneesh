"""
Student dashboard module.
"""

import streamlit as st
import pandas as pd
from utils.database import execute_query
from utils.security import get_current_user, log_audit
from utils.validators import (
    validate_email, validate_phone, sanitize_string
)
from modules.placements import (
    get_student_applications, register_student_for_drive, get_all_drives
)


# ─── DATA ACCESS ─────────────────────────────────────────────────────────────

def get_student_by_user_id(user_id: int):
    return execute_query(
        """
        SELECT s.*, d.name AS department_name, d.code AS dept_code,
               ar.cgpa, ar.arrears
        FROM students s
        JOIN departments d ON s.department_id = d.id
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        WHERE s.user_id = %s
        """,
        (user_id,),
        fetch="one",
    )


def get_student_by_id(student_id: int):
    return execute_query(
        """
        SELECT s.*, d.name AS department_name, d.code AS dept_code,
               ar.cgpa, ar.arrears
        FROM students s
        JOIN departments d ON s.department_id = d.id
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        WHERE s.id = %s
        """,
        (student_id,),
        fetch="one",
    )


def get_student_skills(student_id: int):
    return execute_query(
        "SELECT skill_name, proficiency FROM student_skills WHERE student_id=%s ORDER BY skill_name",
        (student_id,),
        fetch="all",
    ) or []


def get_student_certifications(student_id: int):
    return execute_query(
        "SELECT title, issuing_org, issue_date FROM certifications WHERE student_id=%s ORDER BY issue_date DESC",
        (student_id,),
        fetch="all",
    ) or []


def get_student_projects(student_id: int):
    return execute_query(
        "SELECT title, description, tech_stack, github_url FROM projects WHERE student_id=%s",
        (student_id,),
        fetch="all",
    ) or []


def get_placement_summary(student_id: int):
    return execute_query(
        "SELECT * FROM v_student_placement_summary WHERE student_id=%s",
        (student_id,),
        fetch="one",
    )


def get_notifications(user_id: int, limit: int = 10):
    return execute_query(
        """
        SELECT title, message, type, is_read, created_at
        FROM notifications
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit),
        fetch="all",
    ) or []


def update_student_profile(student_id: int, data: dict):
    """Update editable student profile fields."""
    execute_query(
        """
        UPDATE students
        SET phone=%s, address=%s
        WHERE id=%s
        """,
        (
            sanitize_string(data.get("phone", "")),
            sanitize_string(data.get("address", "")),
            student_id,
        ),
    )
    user = get_current_user()
    if user:
        log_audit("STUDENT_UPDATED", user["id"],
                  f"Student {student_id} profile updated",
                  "students", student_id)


def add_student_skill(student_id: int, skill_name: str,
                      proficiency: str = "Intermediate"):
    execute_query(
        """
        INSERT INTO student_skills (student_id, skill_name, proficiency)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency)
        """,
        (student_id, sanitize_string(skill_name), proficiency),
    )


def add_certification(student_id: int, title: str, org: str,
                      issue_date=None, url: str = ""):
    execute_query(
        """
        INSERT INTO certifications
            (student_id, title, issuing_org, issue_date, credential_url)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (student_id, sanitize_string(title),
         sanitize_string(org), issue_date, url),
    )


def add_project(student_id: int, title: str, description: str,
                tech_stack: str, github_url: str = ""):
    execute_query(
        """
        INSERT INTO projects
            (student_id, title, description, tech_stack, github_url)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (student_id, sanitize_string(title),
         sanitize_string(description),
         sanitize_string(tech_stack), github_url),
    )


def is_eligible_for_drive(student: dict, drive: dict) -> tuple[bool, str]:
    """Check if a student meets the eligibility criteria for a drive."""
    cgpa = float(student.get("cgpa") or 0)
    arrears = int(student.get("arrears") or 0)
    dept_id = student.get("department_id")

    if cgpa < float(drive.get("min_cgpa") or 0):
        return False, f"CGPA {cgpa} < minimum {drive['min_cgpa']}"
    if arrears > int(drive.get("max_arrears") or 0):
        return False, f"Arrears {arrears} > maximum {drive['max_arrears']}"

    eligible_depts = [
        d.strip() for d in str(drive.get("eligible_depts", "")).split(",") if d.strip()
    ]
    if eligible_depts and str(dept_id) not in eligible_depts:
        return False, "Department not eligible for this drive."

    return True, "Eligible"


# ─── Streamlit Dashboard ─────────────────────────────────────────────────────

def show_student_dashboard():
    """Render the complete Student dashboard."""
    user = get_current_user()
    student = get_student_by_user_id(user["id"])

    if not student:
        st.error(
            "Student profile not found. Contact your placement coordinator."
        )
        return

    # ── Sidebar
    st.sidebar.markdown(f"### 🎓 {student['full_name']}")
    st.sidebar.markdown(f"**Reg No:** {student['register_number']}")
    st.sidebar.markdown(f"**Dept:** {student['department_name']}")
    st.sidebar.markdown(f"**CGPA:** {student.get('cgpa', 'N/A')}")

    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "👤 My Profile", "🏢 Placement Drives",
         "📊 My Placements", "📄 Resume Analyzer",
         "🤖 AI Insights", "🔔 Notifications"],
    )

    if page == "🏠 Dashboard":
        _show_student_home(student, user)
    elif page == "👤 My Profile":
        _show_student_profile(student)
    elif page == "🏢 Placement Drives":
        _show_available_drives(student)
    elif page == "📊 My Placements":
        _show_my_placements(student)
    elif page == "📄 Resume Analyzer":
        from modules.reports import show_resume_analyzer
        show_resume_analyzer(student)
    elif page == "🤖 AI Insights":
        _show_ai_insights(student)
    elif page == "🔔 Notifications":
        _show_notifications(user["id"])


def _show_student_home(student: dict, user: dict):
    """Student home page with summary metrics."""
    st.markdown(f"## 👋 Welcome, {student['full_name']}!")
    summary = get_placement_summary(student["id"])

    # Top metric cards
    col1, col2, col3, col4 = st.columns(4)
    attended = summary["companies_attended"] if summary else 0
    selected = summary["companies_selected"] if summary else 0
    rejected = summary["companies_rejected"] if summary else 0
    highest  = summary["highest_package"] if summary else 0
    ps       = summary["placement_status"] if summary else "Not Placed"

    col1.metric("Companies Attended", attended)
    col2.metric("Companies Selected", selected)
    col3.metric("Companies Rejected", rejected)
    col4.metric("Highest Package",
                f"₹{highest} LPA" if highest else "—")

    # Placement status banner
    if ps == "Placed":
        st.success(
            f"🎉 **PLACED** — Congratulations! "
            f"Highest Package: ₹{highest} LPA"
        )
    else:
        st.warning("⏳ **NOT PLACED YET** — Keep applying to placement drives!")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 📋 Quick Info")
        info = {
            "Register Number": student["register_number"],
            "Department": student["department_name"],
            "Batch Year": student["batch_year"],
            "CGPA": student.get("cgpa", "N/A"),
            "Arrears": student.get("arrears", 0),
            "Email": student["email"],
        }
        for k, v in info.items():
            st.markdown(f"**{k}:** {v}")

    with col_b:
        notifications = get_notifications(user["id"], 5)
        st.markdown("#### 🔔 Recent Notifications")
        if notifications:
            for n in notifications:
                icon = {"Drive": "📅", "Result": "🏆",
                        "Shortlist": "⭐", "Interview": "🎤"}.get(
                    n["type"], "📢"
                )
                bg = "#fff3cd" if not n["is_read"] else "#f8f9fa"
                st.markdown(
                    f"<div style='background:{bg}; padding:0.5rem; "
                    f"border-radius:6px; margin-bottom:0.3rem;'>"
                    f"{icon} <b>{n['title']}</b><br>"
                    f"<small>{n['message'][:80]}…</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No notifications yet.")


def _show_student_profile(student: dict):
    """Student profile view with editable fields."""
    st.markdown("## 👤 My Profile")
    tabs = st.tabs(["📋 Personal", "🎯 Skills", "🏅 Certifications", "💡 Projects"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            fields = {
                "Full Name": student["full_name"],
                "Register Number": student["register_number"],
                "Email": student["email"],
                "Department": student["department_name"],
                "Batch Year": student["batch_year"],
                "Gender": student.get("gender", "—"),
            }
            for k, v in fields.items():
                st.text_input(k, value=str(v) if v else "", disabled=True)
        with col2:
            fields2 = {
                "CGPA": student.get("cgpa", "N/A"),
                "Arrears": student.get("arrears", 0),
                "Current Year": student.get("current_year", "—"),
                "Section": student.get("section", "—"),
            }
            for k, v in fields2.items():
                st.text_input(k, value=str(v) if v else "", disabled=True)

        with st.expander("✏️ Update Contact Info"):
            with st.form("update_profile_form"):
                phone = st.text_input("Phone",
                                      value=student.get("phone", "") or "")
                address = st.text_area("Address",
                                       value=student.get("address", "") or "")
                if st.form_submit_button("💾 Save Changes"):
                    if phone and not validate_phone(phone):
                        st.error("Invalid phone number.")
                    else:
                        update_student_profile(student["id"],
                                               {"phone": phone, "address": address})
                        st.success("Profile updated!")
                        st.rerun()

    with tabs[1]:
        skills = get_student_skills(student["id"])
        if skills:
            df = pd.DataFrame(skills)
            df.columns = ["Skill", "Proficiency"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No skills added yet.")
        with st.expander("➕ Add Skill"):
            with st.form("add_skill_form"):
                skill_name = st.text_input("Skill Name")
                proficiency = st.selectbox("Proficiency",
                                           ["Beginner", "Intermediate", "Advanced"])
                if st.form_submit_button("Add Skill"):
                    if skill_name.strip():
                        add_student_skill(student["id"], skill_name, proficiency)
                        st.success("Skill added!")
                        st.rerun()

    with tabs[2]:
        certs = get_student_certifications(student["id"])
        if certs:
            df = pd.DataFrame(certs)
            df.columns = ["Title", "Issuing Organization", "Issue Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No certifications added yet.")
        with st.expander("➕ Add Certification"):
            with st.form("add_cert_form"):
                cert_title = st.text_input("Certification Title")
                cert_org = st.text_input("Issuing Organization")
                cert_date = st.date_input("Issue Date")
                cert_url = st.text_input("Credential URL (optional)")
                if st.form_submit_button("Add Certification"):
                    if cert_title.strip():
                        add_certification(student["id"], cert_title,
                                          cert_org, cert_date, cert_url)
                        st.success("Certification added!")
                        st.rerun()

    with tabs[3]:
        projects = get_student_projects(student["id"])
        if projects:
            for p in projects:
                with st.expander(f"💡 {p['title']}"):
                    st.markdown(f"**Tech Stack:** {p.get('tech_stack','—')}")
                    st.markdown(f"**Description:** {p.get('description','—')}")
                    if p.get("github_url"):
                        st.markdown(f"**GitHub:** {p['github_url']}")
        else:
            st.info("No projects added yet.")
        with st.expander("➕ Add Project"):
            with st.form("add_project_form"):
                proj_title = st.text_input("Project Title")
                proj_desc = st.text_area("Description")
                tech_stack = st.text_input("Tech Stack (comma-separated)")
                github = st.text_input("GitHub URL (optional)")
                if st.form_submit_button("Add Project"):
                    if proj_title.strip():
                        add_project(student["id"], proj_title,
                                    proj_desc, tech_stack, github)
                        st.success("Project added!")
                        st.rerun()


def _show_available_drives(student: dict):
    """Show drives the student can register for."""
    st.markdown("## 🏢 Available Placement Drives")
    drives = get_all_drives(dept_id=student["department_id"], status="Upcoming")
    active = get_all_drives(dept_id=student["department_id"], status="Active")
    all_drives = drives + active

    if not all_drives:
        st.info("No upcoming placement drives available for your department.")
        return

    for drive in all_drives:
        eligible, reason = is_eligible_for_drive(student, drive)
        status_icon = "✅" if eligible else "❌"

        with st.expander(
            f"{status_icon} {drive['company']} — {drive['job_role']} "
            f"| ₹{drive['package_lpa']} LPA | {drive['drive_date']}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Company:** {drive['company']}")
                st.markdown(f"**Job Role:** {drive['job_role']}")
                st.markdown(f"**Drive Date:** {drive['drive_date']}")
                st.markdown(f"**Package:** ₹{drive['package_lpa']} LPA")
            with col2:
                st.markdown(f"**Min CGPA:** {drive['min_cgpa']}")
                st.markdown(f"**Max Arrears:** {drive['max_arrears']}")
                st.markdown(f"**Vacancies:** {drive['vacancies']}")
                st.markdown(f"**Required Skills:** {drive.get('required_skills', '—')}")

            if eligible:
                # Check if already registered
                existing = execute_query(
                    "SELECT status FROM applications WHERE student_id=%s AND drive_id=%s",
                    (student["id"], drive["id"]),
                    fetch="one",
                )
                if existing:
                    st.success(f"Already registered — Status: {existing['status']}")
                else:
                    if st.button(f"📝 Register for {drive['company']}",
                                 key=f"reg_{drive['id']}"):
                        ok, msg = register_student_for_drive(
                            student["id"], drive["id"]
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)
            else:
                st.error(f"Not Eligible: {reason}")


def _show_my_placements(student: dict):
    """Show the student's complete placement history."""
    st.markdown("## 📊 My Placement History")
    summary = get_placement_summary(student["id"])

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    attended = summary["companies_attended"] if summary else 0
    selected = summary["companies_selected"] if summary else 0
    highest  = summary["highest_package"] if summary else None
    status   = summary["placement_status"] if summary else "Not Placed"

    col1.metric("Companies Attended", attended)
    col2.metric("Companies Selected", selected)
    col3.metric("Companies Rejected",
                (summary["companies_rejected"] if summary else 0))
    col4.metric("Highest Package",
                f"₹{highest} LPA" if highest else "—")

    badge = "🟢 PLACED" if status == "Placed" else "🔴 NOT PLACED"
    bg_color = "#d4edda" if status == "Placed" else "#f8d7da"
    st.markdown(
        f"<div style='padding:1rem; background:{bg_color}; "
        f"border-radius:8px; text-align:center; font-size:1.2rem; font-weight:600;'>"
        f"{badge}</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    apps = get_student_applications(student["id"])
    if not apps:
        st.info("You have not applied for any drives yet.")
        return

    df = pd.DataFrame(apps)
    display_cols = [
        "company", "job_role", "drive_date", "package_lpa",
        "application_status", "final_status", "offered_package", "is_verified",
    ]
    df = df[[c for c in display_cols if c in df.columns]]
    rename = {
        "company": "Company", "job_role": "Job Role",
        "drive_date": "Drive Date", "package_lpa": "Package",
        "application_status": "Status", "final_status": "Result",
        "offered_package": "Offered Package",
        "is_verified": "Verified",
    }
    df.rename(columns=rename, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _show_notifications(user_id: int):
    """Display student notifications."""
    st.markdown("## 🔔 Notifications")
    notifications = get_notifications(user_id, 20)
    if not notifications:
        st.info("No notifications.")
        return
    for n in notifications:
        icon = {"Drive": "📅", "Result": "🏆",
                "Shortlist": "⭐", "Interview": "🎤"}.get(n["type"], "📢")
        bg = "#fff3cd" if not n["is_read"] else "#f8f9fa"
        st.markdown(
            f"<div style='background:{bg}; padding:0.8rem; "
            f"border-radius:8px; margin-bottom:0.5rem; "
            f"border-left:4px solid #1e3c72;'>"
            f"{icon} <b>{n['title']}</b>"
            f"<span style='float:right; color:#888; font-size:0.8rem;'>"
            f"{n['created_at']}</span><br>"
            f"{n['message']}</div>",
            unsafe_allow_html=True,
        )


def _show_ai_insights(student: dict):
    """AI/ML-powered insights page for students."""
    st.markdown("## 🤖 AI Placement Insights")

    tabs = st.tabs(["🔮 Placement Prediction", "🎯 Career Recommendations"])

    with tabs[0]:
        try:
            from ml.placement_prediction import show_prediction_widget
            show_prediction_widget(student["id"])
        except Exception as e:
            st.warning(
                "ML prediction module unavailable. "
                "Install scikit-learn to enable this feature."
            )

    with tabs[1]:
        try:
            from ml.career_recommendation import show_career_recommendations
            show_career_recommendations(student_id=student["id"])
        except Exception as e:
            st.warning(
                "Career recommendation module unavailable."
            )
