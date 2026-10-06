"""
Faculty dashboard module.
"""

import streamlit as st
import pandas as pd
from utils.database import execute_query
from utils.security import get_current_user, hash_password, log_audit
from utils.validators import (
    validate_email, validate_phone, sanitize_string,
    validate_cgpa, validate_arrears,
)
from modules.placements import (
    get_all_drives, get_drive_applications,
    update_application_status, add_placement_result,
    create_drive, show_drives_page,
)
from modules.companies import get_all_companies, add_company, show_companies_page


# ─── DATA ACCESS ─────────────────────────────────────────────────────────────

def get_faculty_info(user_id: int):
    return execute_query(
        """
        SELECT f.*, u.full_name, u.email, d.name AS dept_name
        FROM faculty f
        JOIN users u ON f.user_id = u.id
        JOIN departments d ON f.department_id = d.id
        WHERE f.user_id = %s
        """,
        (user_id,),
        fetch="one",
    )


def get_dept_students(dept_id: int, search: str = ""):
    """Return all active students in a department."""
    query = """
        SELECT s.id, s.register_number, s.full_name,
               s.email, s.phone, s.batch_year, s.section,
               ar.cgpa, ar.arrears,
               v.companies_attended, v.companies_selected,
               v.placement_status, v.highest_package
        FROM students s
        JOIN academic_records ar ON s.id = ar.student_id
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
        WHERE s.department_id = %s AND s.is_active = TRUE
    """
    params = [dept_id]
    if search:
        query += " AND (s.full_name LIKE %s OR s.register_number LIKE %s)"
        like = f"%{search}%"
        params += [like, like]
    query += " ORDER BY s.register_number"
    return execute_query(query, tuple(params), fetch="all") or []


def add_student(data: dict, dept_id: int):
    """Add a new student and create their user account."""
    # Create user account first
    username = data["register_number"].upper()
    default_pass = "Student@123"

    execute_query(
        """
        INSERT INTO users
            (username, password_hash, email, full_name, role_id, department_id)
        VALUES (%s,%s,%s,%s,
                (SELECT id FROM roles WHERE name='STUDENT'), %s)
        """,
        (
            username,
            hash_password(default_pass),
            sanitize_string(data["email"]),
            sanitize_string(data["full_name"]),
            dept_id,
        ),
    )
    user_row = execute_query(
        "SELECT id FROM users WHERE username=%s", (username,), fetch="one"
    )
    user_id = user_row["id"] if user_row else None

    # Insert student record
    execute_query(
        """
        INSERT INTO students
            (user_id, register_number, full_name, email, phone,
             department_id, batch_year, current_year, section, gender)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            user_id,
            sanitize_string(data["register_number"]).upper(),
            sanitize_string(data["full_name"]),
            sanitize_string(data["email"]),
            sanitize_string(data.get("phone", "")),
            dept_id,
            data["batch_year"],
            data.get("current_year", 4),
            sanitize_string(data.get("section", "")),
            data.get("gender", "Male"),
        ),
    )
    student_row = execute_query(
        "SELECT id FROM students WHERE register_number=%s",
        (data["register_number"].upper(),),
        fetch="one",
    )
    student_id = student_row["id"] if student_row else None

    if student_id:
        execute_query(
            "INSERT INTO academic_records (student_id, cgpa, arrears) VALUES (%s,%s,%s)",
            (student_id, data.get("cgpa", 0.0), data.get("arrears", 0)),
        )

    user = get_current_user()
    if user:
        log_audit("STUDENT_ADDED", user["id"],
                  f"Student {data['register_number']} added by faculty",
                  "students", student_id)
    return student_id


def update_student(student_id: int, data: dict):
    """Update student details (faculty-level edit)."""
    execute_query(
        """
        UPDATE students SET full_name=%s, email=%s, phone=%s,
               section=%s, current_year=%s
        WHERE id=%s
        """,
        (
            sanitize_string(data["full_name"]),
            sanitize_string(data["email"]),
            sanitize_string(data.get("phone", "")),
            sanitize_string(data.get("section", "")),
            data.get("current_year", 4),
            student_id,
        ),
    )
    execute_query(
        """
        UPDATE academic_records SET cgpa=%s, arrears=%s
        WHERE student_id=%s
        """,
        (data["cgpa"], data["arrears"], student_id),
    )
    user = get_current_user()
    if user:
        log_audit("STUDENT_UPDATED", user["id"],
                  f"Student {student_id} updated by faculty",
                  "students", student_id)


def get_dept_stats(dept_id: int):
    return execute_query(
        "SELECT * FROM v_department_stats WHERE department_id=%s",
        (dept_id,),
        fetch="one",
    )


# ─── Streamlit Dashboard ─────────────────────────────────────────────────────

def show_faculty_dashboard():
    """Render the Faculty dashboard."""
    user = get_current_user()
    faculty = get_faculty_info(user["id"])

    if not faculty:
        st.error("Faculty profile not found.")
        return

    dept_id   = faculty["department_id"]
    dept_name = faculty["dept_name"]

    st.sidebar.markdown(f"### 👨‍🏫 {faculty['full_name']}")
    st.sidebar.markdown(f"**Dept:** {dept_name}")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👥 Students",
            "➕ Add Student",
            "🏢 Companies",
            "📅 Placement Drives",
            "📊 Placement Tracking",
        ],
    )

    if page == "🏠 Dashboard":
        _show_faculty_home(dept_id, dept_name, faculty)
    elif page == "👥 Students":
        _show_students_page(dept_id)
    elif page == "➕ Add Student":
        _show_add_student_form(dept_id)
    elif page == "🏢 Companies":
        show_companies_page(can_edit=True)
    elif page == "📅 Placement Drives":
        show_drives_page(can_edit=True, dept_id=dept_id)
    elif page == "📊 Placement Tracking":
        _show_placement_tracking(dept_id)


def _show_faculty_home(dept_id: int, dept_name: str, faculty: dict):
    """Faculty dashboard home page with metrics."""
    st.markdown(f"## 📊 Faculty Dashboard — {dept_name}")
    stats = get_dept_stats(dept_id)

    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students", stats["total_students"] or 0)
        col2.metric("Placed", stats["placed_students"] or 0)
        col3.metric("Not Placed", stats["not_placed_students"] or 0)
        col4.metric("Placement %",
                    f"{stats['placement_percentage'] or 0:.1f}%")

        col5, col6, col7 = st.columns(3)
        col5.metric("Highest Package",
                    f"₹{stats['highest_package'] or 0} LPA")
        col6.metric("Avg Package",
                    f"₹{stats['avg_package'] or 0:.2f} LPA")

        drives = get_all_drives(dept_id=dept_id)
        col7.metric("Total Drives", len(drives))
    else:
        st.info("No statistics available yet.")

    st.divider()
    st.markdown("### 🏆 Recent Placements")
    recent = execute_query(
        """
        SELECT s.register_number, s.full_name,
               c.name AS company, pd.job_role,
               pr.package_lpa, pr.is_verified
        FROM placement_results pr
        JOIN students s   ON pr.student_id = s.id
        JOIN placement_drives pd ON pr.drive_id = pd.id
        JOIN companies c  ON pd.company_id = c.id
        WHERE s.department_id = %s AND pr.status = 'Selected'
        ORDER BY pr.created_at DESC
        LIMIT 10
        """,
        (dept_id,),
        fetch="all",
    ) or []
    if recent:
        df = pd.DataFrame(recent)
        df.columns = ["Reg No", "Name", "Company",
                      "Job Role", "Package (LPA)", "Verified"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No placement results yet.")


def _show_students_page(dept_id: int):
    """View and edit department students."""
    st.markdown("## 👥 Department Students")
    search = st.text_input("🔍 Search by name or register number")
    students = get_dept_students(dept_id, search)

    if not students:
        st.info("No students found.")
        return

    df = pd.DataFrame(students)
    cols = ["register_number", "full_name", "section", "cgpa",
            "arrears", "companies_attended", "companies_selected",
            "placement_status", "highest_package"]
    df = df[[c for c in cols if c in df.columns]]
    rename = {
        "register_number": "Reg No", "full_name": "Name",
        "section": "Section", "cgpa": "CGPA", "arrears": "Arrears",
        "companies_attended": "Attended", "companies_selected": "Selected",
        "placement_status": "Status", "highest_package": "Highest Pkg",
    }
    df.rename(columns=rename, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(f"**Total Students: {len(students)}**")

    with st.expander("✏️ Edit Student"):
        reg_numbers = [s["register_number"] for s in students]
        sel = st.selectbox("Select student to edit", reg_numbers,
                           key="edit_student_sel")
        sel_student = next(s for s in students if s["register_number"] == sel)
        _show_edit_student_form(sel_student)


def _show_edit_student_form(student: dict):
    """Edit form for a student record."""
    with st.form(f"edit_student_{student['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name",
                                      value=student.get("full_name", ""))
            email = st.text_input("Email", value=student.get("email", ""))
            phone = st.text_input("Phone", value=student.get("phone", "") or "")
        with col2:
            section = st.text_input("Section",
                                    value=student.get("section", "") or "")
            year = st.number_input("Current Year", 1, 4,
                                   int(student.get("current_year", 4)))
            cgpa = st.number_input("CGPA", 0.0, 10.0,
                                   float(student.get("cgpa", 0)), 0.01)
            arrears = st.number_input("Arrears", 0, 50,
                                      int(student.get("arrears", 0)))

        if st.form_submit_button("💾 Update Student"):
            if not validate_email(email):
                st.error("Invalid email address.")
            elif not validate_cgpa(cgpa):
                st.error("CGPA must be between 0 and 10.")
            else:
                update_student(student["id"], {
                    "full_name": full_name, "email": email,
                    "phone": phone, "section": section,
                    "current_year": year, "cgpa": cgpa, "arrears": arrears,
                })
                st.success("Student updated successfully!")
                st.rerun()


def _show_add_student_form(dept_id: int):
    """Form to add a new student to the department."""
    st.markdown("## ➕ Add New Student")
    with st.form("add_student_form"):
        col1, col2 = st.columns(2)
        with col1:
            reg_number = st.text_input("Register Number *",
                                       placeholder="e.g. CSE2021031")
            full_name = st.text_input("Full Name *")
            email = st.text_input("Email *")
            phone = st.text_input("Phone")
        with col2:
            batch_year = st.number_input("Batch Year *", 2015, 2030, 2021)
            current_year = st.number_input("Current Year", 1, 4, 4)
            section = st.text_input("Section", placeholder="A or B")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            cgpa = st.number_input("CGPA", 0.0, 10.0, 0.0, 0.01)
            arrears = st.number_input("Arrears", 0, 50, 0)

        if st.form_submit_button("➕ Add Student"):
            errors = []
            if not reg_number.strip():
                errors.append("Register number is required.")
            if not full_name.strip():
                errors.append("Full name is required.")
            if not validate_email(email):
                errors.append("Invalid email address.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                # Check duplicate
                existing = execute_query(
                    "SELECT id FROM students WHERE register_number=%s",
                    (reg_number.strip().upper(),), fetch="one"
                )
                if existing:
                    st.error("A student with this register number already exists.")
                else:
                    sid = add_student(
                        {
                            "register_number": reg_number,
                            "full_name": full_name,
                            "email": email,
                            "phone": phone,
                            "batch_year": batch_year,
                            "current_year": current_year,
                            "section": section,
                            "gender": gender,
                            "cgpa": cgpa,
                            "arrears": arrears,
                        },
                        dept_id,
                    )
                    st.success(
                        f"Student '{full_name}' added! "
                        f"Login: {reg_number.upper()} / Student@123"
                    )
                    st.rerun()


def _show_placement_tracking(dept_id: int):
    """Placement drive tracking and result entry."""
    st.markdown("## 📊 Placement Tracking")
    drives = get_all_drives(dept_id=dept_id)

    if not drives:
        st.info("No placement drives available.")
        return

    drive_labels = [
        f"{d['company']} — {d['job_role']} ({d['drive_date']})"
        for d in drives
    ]
    selected_idx = st.selectbox(
        "Select Drive",
        range(len(drive_labels)),
        format_func=lambda i: drive_labels[i],
    )
    drive = drives[selected_idx]

    st.markdown(
        f"**Company:** {drive['company']} | "
        f"**Package:** ₹{drive['package_lpa']} LPA | "
        f"**Status:** {drive['status']}"
    )

    applications = get_drive_applications(drive["id"], dept_id)
    if not applications:
        st.info("No applications for this drive from your department.")
        return

    tabs = st.tabs(["📋 Applications", "🔄 Update Status",
                    "🏆 Record Result", "🎯 Round Results"])

    with tabs[0]:
        df = pd.DataFrame(applications)
        display_cols = ["register_number", "student_name", "cgpa",
                        "arrears", "status", "final_result",
                        "offered_package", "is_verified"]
        df = df[[c for c in display_cols if c in df.columns]]
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[1]:
        app_labels = [
            f"{a['register_number']} - {a['student_name']}"
            for a in applications
        ]
        idx = st.selectbox("Select Student", range(len(app_labels)),
                           format_func=lambda i: app_labels[i],
                           key="track_student")
        sel = applications[idx]
        status_options = [
            "Registered", "Attended", "Shortlisted",
            "Technical Round", "HR Round", "Selected", "Rejected",
        ]
        cur = (status_options.index(sel["status"])
               if sel["status"] in status_options else 0)
        new_status = st.selectbox("New Status", status_options, index=cur)
        remarks = st.text_area("Remarks", key="track_remarks")
        if st.button("Update Status", key="track_update"):
            update_application_status(sel["application_id"],
                                      new_status, remarks)
            st.success("Status updated!")
            st.rerun()

    with tabs[2]:
        idx2 = st.selectbox("Select Student", range(len(app_labels)),
                            format_func=lambda i: app_labels[i],
                            key="result_student")
        sel2 = applications[idx2]
        col1, col2 = st.columns(2)
        with col1:
            result = st.selectbox("Result",
                                  ["Selected", "Rejected", "On Hold"])
        with col2:
            pkg = st.number_input("Package (LPA)", 0.0, 100.0, 3.5, 0.1)
        rmk = st.text_area("Remarks", key="result_rmk")
        if st.button("Record Result", key="rec_result"):
            # Get student_id from application
            app_data = execute_query(
                "SELECT student_id FROM applications WHERE id=%s",
                (sel2["application_id"],), fetch="one"
            )
            if app_data:
                add_placement_result(
                    app_data["student_id"], drive["id"],
                    sel2["application_id"], result, pkg, rmk,
                )
                st.success("Result recorded!")
                st.rerun()

    with tabs[3]:
        from modules.placements import add_interview_round
        idx3 = st.selectbox("Select Student", range(len(app_labels)),
                            format_func=lambda i: app_labels[i],
                            key="round_student")
        sel3 = applications[idx3]
        col1, col2 = st.columns(2)
        with col1:
            round_name = st.selectbox(
                "Round",
                ["Aptitude", "Group Discussion",
                 "Technical Interview", "HR Interview", "Final Selection"],
            )
            round_result = st.selectbox("Result",
                                        ["Pass", "Fail", "Absent", "Pending"])
        with col2:
            score = st.number_input("Score (optional)", 0.0, 100.0, 0.0)
        feedback = st.text_area("Feedback", key="round_feedback")
        if st.button("Save Round Result", key="save_round"):
            add_interview_round(
                sel3["application_id"], round_name,
                round_result, score if score > 0 else None, feedback,
            )
            st.success("Round result saved!")
            st.rerun()
