"""
Placement drives and application management module.
"""

import streamlit as st
import pandas as pd
from datetime import date
from utils.database import execute_query
from utils.security import get_current_user, log_audit
from utils.validators import sanitize_string


# ─── DATA ACCESS ─────────────────────────────────────────────────────────────

def get_all_drives(dept_id: int = None, status: str = None):
    """Return placement drives, optionally filtered by department or status."""
    query = """
        SELECT pd.id, c.name AS company, pd.job_role,
               pd.drive_date, pd.min_cgpa, pd.max_arrears,
               pd.package_lpa, pd.vacancies, pd.status,
               pd.eligible_depts, pd.required_skills,
               pd.selection_process, pd.venue,
               pd.registration_deadline,
               COUNT(DISTINCT a.id) AS registered_count,
               COUNT(DISTINCT CASE WHEN a.status='Selected'
                                   THEN a.id END) AS selected_count
        FROM placement_drives pd
        JOIN companies c ON pd.company_id = c.id
        LEFT JOIN applications a ON pd.id = a.drive_id
    """
    conditions, params = [], []
    if status:
        conditions.append("pd.status = %s")
        params.append(status)
    if dept_id:
        conditions.append(
            "FIND_IN_SET(%s, REPLACE(pd.eligible_depts, ' ', '')) > 0"
        )
        params.append(str(dept_id))
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY pd.id ORDER BY pd.drive_date DESC"
    return execute_query(query, tuple(params), fetch="all") or []


def get_drive_by_id(drive_id: int):
    return execute_query(
        """
        SELECT pd.*, c.name AS company_name
        FROM placement_drives pd
        JOIN companies c ON pd.company_id = c.id
        WHERE pd.id = %s
        """,
        (drive_id,),
        fetch="one",
    )


def create_drive(data: dict) -> int:
    """Create a new placement drive."""
    query = """
        INSERT INTO placement_drives
            (company_id, job_role, drive_date, registration_deadline,
             min_cgpa, max_arrears, required_skills, package_lpa,
             vacancies, job_description, selection_process,
             eligible_depts, venue, status, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    user = get_current_user()
    execute_query(
        query,
        (
            data["company_id"],
            sanitize_string(data["job_role"]),
            data["drive_date"],
            data.get("registration_deadline"),
            data.get("min_cgpa", 0),
            data.get("max_arrears", 0),
            sanitize_string(data.get("required_skills", "")),
            data.get("package_lpa", 0),
            data.get("vacancies", 0),
            sanitize_string(data.get("job_description", "")),
            sanitize_string(data.get("selection_process", "")),
            data.get("eligible_depts", ""),
            sanitize_string(data.get("venue", "")),
            data.get("status", "Upcoming"),
            user["id"] if user else None,
        ),
    )
    new_id = execute_query("SELECT LAST_INSERT_ID() AS id", fetch="one")
    did = new_id["id"] if new_id else None
    if user:
        log_audit("DRIVE_CREATED", user["id"],
                  f"Drive for '{data['job_role']}' created",
                  "placement_drives", did)
    return did


def register_student_for_drive(student_id: int, drive_id: int):
    """Register a student for a placement drive."""
    existing = execute_query(
        "SELECT id FROM applications WHERE student_id=%s AND drive_id=%s",
        (student_id, drive_id),
        fetch="one",
    )
    if existing:
        return False, "Student already registered for this drive."
    execute_query(
        "INSERT INTO applications (student_id, drive_id, status) VALUES (%s,%s,'Registered')",
        (student_id, drive_id),
    )
    return True, "Registration successful."


def update_application_status(application_id: int, status: str,
                               remarks: str = ""):
    """Update the status of a student's application."""
    execute_query(
        "UPDATE applications SET status=%s, remarks=%s WHERE id=%s",
        (status, remarks, application_id),
    )
    user = get_current_user()
    if user:
        log_audit("APPLICATION_UPDATED", user["id"],
                  f"Application {application_id} → {status}",
                  "applications", application_id)


def add_interview_round(application_id: int, round_name: str,
                        result: str, score: float = None,
                        feedback: str = ""):
    """Add or update an interview round result."""
    existing = execute_query(
        """SELECT id FROM interview_rounds
           WHERE application_id=%s AND round_name=%s""",
        (application_id, round_name),
        fetch="one",
    )
    user = get_current_user()
    if existing:
        execute_query(
            """UPDATE interview_rounds
               SET result=%s, score=%s, feedback=%s
               WHERE id=%s""",
            (result, score, feedback, existing["id"]),
        )
    else:
        execute_query(
            """INSERT INTO interview_rounds
                   (application_id, round_name, result, score,
                    feedback, conducted_by)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (application_id, round_name, result, score,
             feedback, user["id"] if user else None),
        )


def add_placement_result(student_id: int, drive_id: int,
                         application_id: int, status: str,
                         package_lpa: float, remarks: str = ""):
    """Record final placement result."""
    existing = execute_query(
        "SELECT id FROM placement_results WHERE application_id=%s",
        (application_id,),
        fetch="one",
    )
    if existing:
        execute_query(
            """UPDATE placement_results
               SET status=%s, package_lpa=%s, remarks=%s
               WHERE id=%s""",
            (status, package_lpa, remarks, existing["id"]),
        )
    else:
        execute_query(
            """INSERT INTO placement_results
                   (student_id, drive_id, application_id,
                    status, package_lpa, remarks)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (student_id, drive_id, application_id,
             status, package_lpa, remarks),
        )
    # Sync application status
    app_status = "Selected" if status == "Selected" else "Rejected"
    execute_query(
        "UPDATE applications SET status=%s WHERE id=%s",
        (app_status, application_id),
    )
    user = get_current_user()
    if user:
        log_audit("PLACEMENT_RESULT", user["id"],
                  f"Student {student_id} → {status} in drive {drive_id}",
                  "placement_results")


def verify_placement_result(result_id: int):
    """Mark a placement result as verified (HOD/Admin only)."""
    user = get_current_user()
    execute_query(
        """UPDATE placement_results
           SET is_verified=TRUE, verified_by=%s, verified_at=NOW()
           WHERE id=%s""",
        (user["id"] if user else None, result_id),
    )
    if user:
        log_audit("RESULT_VERIFIED", user["id"],
                  f"Placement result {result_id} verified",
                  "placement_results", result_id)


def get_student_applications(student_id: int):
    """Get all applications for a student with full details."""
    return execute_query(
        """
        SELECT
            a.id           AS application_id,
            c.name         AS company,
            pd.job_role,
            pd.drive_date,
            pd.package_lpa,
            pd.min_cgpa,
            pd.max_arrears,
            a.status       AS application_status,
            a.remarks,
            a.applied_at,
            pr.status      AS final_status,
            pr.package_lpa AS offered_package,
            pr.is_verified
        FROM applications a
        JOIN placement_drives pd ON a.drive_id = pd.id
        JOIN companies c         ON pd.company_id = c.id
        LEFT JOIN placement_results pr ON a.id = pr.application_id
        WHERE a.student_id = %s
        ORDER BY pd.drive_date DESC
        """,
        (student_id,),
        fetch="all",
    ) or []


def get_drive_applications(drive_id: int, dept_id: int = None):
    """Get all applications for a drive, optionally filtered by department."""
    query = """
        SELECT
            a.id           AS application_id,
            s.register_number,
            s.full_name    AS student_name,
            d.name         AS department,
            ar.cgpa,
            ar.arrears,
            a.status,
            a.remarks,
            pr.status      AS final_result,
            pr.package_lpa AS offered_package,
            pr.is_verified
        FROM applications a
        JOIN students s       ON a.student_id = s.id
        JOIN departments d    ON s.department_id = d.id
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        LEFT JOIN placement_results pr ON a.id = pr.application_id
        WHERE a.drive_id = %s
    """
    params = [drive_id]
    if dept_id:
        query += " AND s.department_id = %s"
        params.append(dept_id)
    query += " ORDER BY s.full_name"
    return execute_query(query, tuple(params), fetch="all") or []


# ─── Streamlit UI ─────────────────────────────────────────────────────────────

def show_drives_page(can_edit: bool = False, dept_id: int = None):
    """Render the Placement Drives page."""
    st.markdown("## 📅 Placement Drives")

    tab_labels = ["🗓️ Upcoming", "✅ Completed", "📋 All Drives"]
    if can_edit:
        tab_labels.append("➕ Create Drive")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _show_drives_list(
            get_all_drives(dept_id=dept_id, status="Upcoming"),
            can_edit=can_edit, label="upcoming"
        )
    with tabs[1]:
        _show_drives_list(
            get_all_drives(dept_id=dept_id, status="Completed"),
            can_edit=can_edit, label="completed"
        )
    with tabs[2]:
        _show_drives_list(
            get_all_drives(dept_id=dept_id),
            can_edit=can_edit, label="all"
        )
    if can_edit and len(tabs) > 3:
        with tabs[3]:
            _show_create_drive_form()


def _show_drives_list(drives: list, can_edit: bool, label: str):
    if not drives:
        st.info("No drives found.")
        return
    df = pd.DataFrame(drives)
    display_cols = ["company", "job_role", "drive_date", "package_lpa",
                    "min_cgpa", "max_arrears", "vacancies", "status",
                    "registered_count", "selected_count"]
    df = df[[c for c in display_cols if c in df.columns]]
    rename = {
        "company": "Company", "job_role": "Job Role",
        "drive_date": "Drive Date", "package_lpa": "Package (LPA)",
        "min_cgpa": "Min CGPA", "max_arrears": "Max Arrears",
        "vacancies": "Vacancies", "status": "Status",
        "registered_count": "Registered", "selected_count": "Selected",
    }
    df.rename(columns=rename, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if can_edit:
        with st.expander(f"🔧 Manage {label.title()} Drive"):
            drive_labels = [
                f"{d['company']} - {d['job_role']} ({d['drive_date']})"
                for d in drives
            ]
            if drive_labels:
                sel_idx = st.selectbox("Select drive", range(len(drive_labels)),
                                       format_func=lambda i: drive_labels[i],
                                       key=f"drive_sel_{label}")
                sel_drive = drives[sel_idx]
                _show_drive_management(sel_drive)


def _show_drive_management(drive: dict):
    """Show management options for a specific drive."""
    st.markdown(f"### {drive['company']} — {drive['job_role']}")

    sub_tabs = st.tabs(["👥 Applications", "📝 Update Status",
                         "🏆 Record Result"])
    with sub_tabs[0]:
        applications = get_drive_applications(drive["id"])
        if applications:
            df = pd.DataFrame(applications)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No applications yet.")

    with sub_tabs[1]:
        apps = get_drive_applications(drive["id"])
        if apps:
            app_labels = [
                f"{a['register_number']} - {a['student_name']}"
                for a in apps
            ]
            idx = st.selectbox("Select student", range(len(app_labels)),
                               format_func=lambda i: app_labels[i],
                               key=f"app_sel_{drive['id']}")
            sel_app = apps[idx]

            status_options = [
                "Registered", "Attended", "Shortlisted",
                "Technical Round", "HR Round", "Selected", "Rejected"
            ]
            cur_idx = (
                status_options.index(sel_app["status"])
                if sel_app["status"] in status_options else 0
            )
            new_status = st.selectbox("New Status", status_options,
                                      index=cur_idx,
                                      key=f"new_status_{sel_app['application_id']}")
            remarks = st.text_area("Remarks", key=f"rmk_{sel_app['application_id']}")
            if st.button("Update Status", key=f"upd_{sel_app['application_id']}"):
                update_application_status(
                    sel_app["application_id"], new_status, remarks
                )
                st.success("Status updated!")
                st.rerun()

    with sub_tabs[2]:
        apps = get_drive_applications(drive["id"])
        if apps:
            app_labels = [
                f"{a['register_number']} - {a['student_name']}"
                for a in apps
            ]
            idx2 = st.selectbox("Select student", range(len(app_labels)),
                                format_func=lambda i: app_labels[i],
                                key=f"res_sel_{drive['id']}")
            sel_app2 = apps[idx2]

            col1, col2 = st.columns(2)
            with col1:
                result = st.selectbox("Result", ["Selected", "Rejected", "On Hold"],
                                      key=f"res_{sel_app2['application_id']}")
            with col2:
                pkg = st.number_input("Package (LPA)", min_value=0.0,
                                      max_value=100.0, step=0.1,
                                      key=f"pkg_{sel_app2['application_id']}")
            remark2 = st.text_area("Remarks", key=f"res_rmk_{sel_app2['application_id']}")
            if st.button("Record Result", key=f"rec_{sel_app2['application_id']}"):
                # Fetch student_id from application
                app_full = execute_query(
                    "SELECT student_id FROM applications WHERE id=%s",
                    (sel_app2["application_id"],), fetch="one"
                )
                if app_full:
                    add_placement_result(
                        app_full["student_id"],
                        drive["id"],
                        sel_app2["application_id"],
                        result, pkg, remark2,
                    )
                    st.success("Result recorded!")
                    st.rerun()


def _show_create_drive_form():
    """Form to create a new placement drive."""
    companies = execute_query(
        "SELECT id, name FROM companies ORDER BY name", fetch="all"
    ) or []
    departments = execute_query(
        "SELECT id, name FROM departments ORDER BY name", fetch="all"
    ) or []

    if not companies:
        st.warning("Please add companies first.")
        return

    with st.form("create_drive_form"):
        st.markdown("### Create New Placement Drive")
        col1, col2 = st.columns(2)
        with col1:
            company_id = st.selectbox(
                "Company *",
                [c["id"] for c in companies],
                format_func=lambda cid: next(
                    c["name"] for c in companies if c["id"] == cid
                ),
            )
            job_role = st.text_input("Job Role *")
            drive_date = st.date_input("Drive Date *", value=date.today())
            reg_deadline = st.date_input("Registration Deadline")
            venue = st.text_input("Venue")
        with col2:
            min_cgpa = st.number_input("Min CGPA", 0.0, 10.0, 6.0, 0.1)
            max_arrears = st.number_input("Max Arrears", 0, 20, 0)
            package_lpa = st.number_input("Package (LPA)", 0.0, 100.0, 3.5, 0.1)
            vacancies = st.number_input("Vacancies", 0, 1000, 10)
            status = st.selectbox("Status",
                                  ["Upcoming", "Active", "Completed", "Cancelled"])

        eligible_dept_ids = st.multiselect(
            "Eligible Departments",
            [d["id"] for d in departments],
            format_func=lambda did: next(
                d["name"] for d in departments if d["id"] == did
            ),
            default=[d["id"] for d in departments],
        )
        required_skills = st.text_input(
            "Required Skills (comma-separated)",
            placeholder="Python, Java, SQL"
        )
        selection_process = st.text_area(
            "Selection Process",
            value="Aptitude\nGroup Discussion\nTechnical Interview\nHR Interview\nFinal Selection",
        )
        job_description = st.text_area("Job Description")

        if st.form_submit_button("🚀 Create Drive"):
            if not job_role.strip():
                st.error("Job role is required.")
                return
            eligible_str = ",".join(str(d) for d in eligible_dept_ids)
            did = create_drive({
                "company_id": company_id,
                "job_role": job_role,
                "drive_date": drive_date,
                "registration_deadline": reg_deadline,
                "min_cgpa": min_cgpa,
                "max_arrears": max_arrears,
                "required_skills": required_skills,
                "package_lpa": package_lpa,
                "vacancies": vacancies,
                "job_description": job_description,
                "selection_process": selection_process,
                "eligible_depts": eligible_str,
                "venue": venue,
                "status": status,
            })
            st.success(f"Drive created successfully! (ID: {did})")
            st.rerun()
