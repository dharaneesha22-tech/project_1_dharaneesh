"""
HOD (Head of Department) dashboard module.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import execute_query
from utils.security import get_current_user
from modules.placements import (
    verify_placement_result, get_all_drives, get_drive_applications
)
from modules.analytics import (
    plot_placement_status_pie, plot_package_distribution,
    plot_company_selection_bar,
)


# ─── DATA ACCESS ─────────────────────────────────────────────────────────────

def get_hod_info(user_id: int):
    return execute_query(
        """
        SELECT h.*, u.full_name, u.email, d.name AS dept_name
        FROM hod h
        JOIN users u ON h.user_id = u.id
        JOIN departments d ON h.department_id = d.id
        WHERE h.user_id = %s
        """,
        (user_id,),
        fetch="one",
    )


def get_dept_full_stats(dept_id: int):
    return execute_query(
        "SELECT * FROM v_department_stats WHERE department_id = %s",
        (dept_id,),
        fetch="one",
    )


def get_dept_company_report(dept_id: int):
    """Company-wise statistics for the department."""
    return execute_query(
        """
        SELECT c.name AS company,
               pd.job_role,
               pd.drive_date,
               pd.package_lpa,
               COUNT(DISTINCT a.id)                                   AS attended,
               COUNT(DISTINCT CASE WHEN a.status = 'Shortlisted'
                                   THEN a.id END)                     AS shortlisted,
               COUNT(DISTINCT CASE WHEN pr.status = 'Selected'
                                   THEN pr.id END)                    AS selected,
               MAX(pr.package_lpa)                                    AS max_package
        FROM placement_drives pd
        JOIN companies c ON pd.company_id = c.id
        JOIN applications a ON pd.id = a.drive_id
        JOIN students s ON a.student_id = s.id
        LEFT JOIN placement_results pr ON a.id = pr.application_id
        WHERE s.department_id = %s
          AND a.status NOT IN ('Registered', 'Withdrawn')
        GROUP BY c.id, pd.id
        ORDER BY pd.drive_date DESC
        """,
        (dept_id,),
        fetch="all",
    ) or []


def get_unverified_results(dept_id: int):
    """Return unverified placement results for HOD verification."""
    return execute_query(
        """
        SELECT pr.id AS result_id,
               s.register_number, s.full_name,
               c.name AS company, pd.job_role,
               pr.package_lpa, pr.status,
               pr.created_at
        FROM placement_results pr
        JOIN students s ON pr.student_id = s.id
        JOIN placement_drives pd ON pr.drive_id = pd.id
        JOIN companies c ON pd.company_id = c.id
        WHERE s.department_id = %s
          AND pr.is_verified = FALSE
        ORDER BY pr.created_at DESC
        """,
        (dept_id,),
        fetch="all",
    ) or []


def get_dept_students_for_hod(dept_id: int):
    """All students with placement summary for HOD view."""
    return execute_query(
        """
        SELECT s.register_number, s.full_name, s.email,
               ar.cgpa, ar.arrears,
               v.companies_attended, v.companies_selected,
               v.highest_package, v.placement_status
        FROM students s
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
        WHERE s.department_id = %s AND s.is_active = TRUE
        ORDER BY s.register_number
        """,
        (dept_id,),
        fetch="all",
    ) or []


# ─── Streamlit Dashboard ─────────────────────────────────────────────────────

def show_hod_dashboard():
    """Render the HOD dashboard."""
    user = get_current_user()
    hod = get_hod_info(user["id"])

    if not hod:
        st.error("HOD profile not found.")
        return

    dept_id   = hod["department_id"]
    dept_name = hod["dept_name"]

    st.sidebar.markdown(f"### 👨‍💼 {hod['full_name']}")
    st.sidebar.markdown(f"**Dept:** {dept_name}")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👥 Students",
            "✅ Verify Placements",
            "📊 Company Report",
            "📈 Analytics",
            "📄 Reports",
        ],
    )

    if page == "🏠 Dashboard":
        _show_hod_home(dept_id, dept_name)
    elif page == "👥 Students":
        _show_hod_students(dept_id)
    elif page == "✅ Verify Placements":
        _show_verification(dept_id)
    elif page == "📊 Company Report":
        _show_company_report(dept_id)
    elif page == "📈 Analytics":
        _show_hod_analytics(dept_id, dept_name)
    elif page == "📄 Reports":
        from modules.reports import show_dept_report
        show_dept_report(dept_id, dept_name)


def _show_hod_home(dept_id: int, dept_name: str):
    """HOD dashboard home page."""
    st.markdown(f"## 🏫 HOD Dashboard — {dept_name}")
    stats = get_dept_full_stats(dept_id)

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
        col7.metric("Companies Visited", len(drives))
    else:
        st.info("No statistics available.")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📋 Pending Verifications")
        unverified = get_unverified_results(dept_id)
        if unverified:
            st.warning(
                f"**{len(unverified)} placement results** awaiting verification."
            )
            df = pd.DataFrame(unverified[:5])
            st.dataframe(df[["full_name", "company", "package_lpa"]],
                         use_container_width=True, hide_index=True)
        else:
            st.success("All placement results are verified.")

    with col_b:
        st.markdown("### 🏆 Top Packages")
        top = execute_query(
            """
            SELECT s.full_name, c.name AS company,
                   pr.package_lpa AS package
            FROM placement_results pr
            JOIN students s ON pr.student_id = s.id
            JOIN placement_drives pd ON pr.drive_id = pd.id
            JOIN companies c ON pd.company_id = c.id
            WHERE s.department_id = %s AND pr.status='Selected'
            ORDER BY pr.package_lpa DESC LIMIT 5
            """,
            (dept_id,),
            fetch="all",
        ) or []
        if top:
            df_top = pd.DataFrame(top)
            df_top.columns = ["Student", "Company", "Package (LPA)"]
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No placement data yet.")


def _show_hod_students(dept_id: int):
    """HOD view of all department students."""
    st.markdown("## 👥 Department Students")
    search = st.text_input("🔍 Search student")
    students = get_dept_students_for_hod(dept_id)

    if search:
        students = [
            s for s in students
            if search.lower() in s["full_name"].lower()
            or search.lower() in s["register_number"].lower()
        ]

    if not students:
        st.info("No students found.")
        return

    filter_status = st.selectbox(
        "Filter by Placement Status",
        ["All", "Placed", "Not Placed"],
    )
    if filter_status != "All":
        students = [s for s in students
                    if s.get("placement_status", "Not Placed") == filter_status]

    df = pd.DataFrame(students)
    display_cols = ["register_number", "full_name", "cgpa", "arrears",
                    "companies_attended", "companies_selected",
                    "highest_package", "placement_status"]
    df = df[[c for c in display_cols if c in df.columns]]
    rename = {
        "register_number": "Reg No", "full_name": "Name",
        "cgpa": "CGPA", "arrears": "Arrears",
        "companies_attended": "Attended",
        "companies_selected": "Selected",
        "highest_package": "Highest Pkg",
        "placement_status": "Status",
    }
    df.rename(columns=rename, inplace=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown(f"**Showing {len(df)} students**")

    # CSV export
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export CSV", csv, "students.csv", "text/csv")


def _show_verification(dept_id: int):
    """HOD placement verification page."""
    st.markdown("## ✅ Placement Verification")
    unverified = get_unverified_results(dept_id)

    if not unverified:
        st.success("All placement results are verified! ✅")
        return

    st.info(f"**{len(unverified)} results** pending verification.")
    df = pd.DataFrame(unverified)
    df.columns = [
        "Result ID", "Reg No", "Student Name", "Company",
        "Job Role", "Package (LPA)", "Status", "Date",
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Verify Individual Result")
    result_labels = [
        f"{r['register_number']} - {r['full_name']} @ {r['company']} "
        f"(₹{r['package_lpa']} LPA)"
        for r in unverified
    ]
    idx = st.selectbox("Select result to verify",
                       range(len(result_labels)),
                       format_func=lambda i: result_labels[i])
    sel = unverified[idx]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Student:** {sel['full_name']}")
        st.markdown(f"**Company:** {sel['company']}")
    with col2:
        st.markdown(f"**Package:** ₹{sel['package_lpa']} LPA")
        st.markdown(f"**Status:** {sel['status']}")

    if st.button("✅ Verify This Result", type="primary"):
        verify_placement_result(sel["result_id"])
        st.success("Result verified successfully!")
        st.rerun()

    if st.button("✅ Verify All Pending"):
        for r in unverified:
            verify_placement_result(r["result_id"])
        st.success(f"All {len(unverified)} results verified!")
        st.rerun()


def _show_company_report(dept_id: int):
    """Company-wise placement report for the department."""
    st.markdown("## 📊 Company-wise Report")
    report = get_dept_company_report(dept_id)

    if not report:
        st.info("No company placement data available.")
        return

    df = pd.DataFrame(report)
    df.columns = [
        "Company", "Job Role", "Drive Date", "Package (LPA)",
        "Attended", "Shortlisted", "Selected", "Max Package",
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Selection ratio chart
    fig = px.bar(
        df,
        x="Company",
        y=["Attended", "Shortlisted", "Selected"],
        barmode="group",
        title="Company-wise Funnel",
        color_discrete_sequence=["#1e3c72", "#2a5298", "#48b5f0"],
    )
    st.plotly_chart(fig, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export CSV", csv, "company_report.csv", "text/csv")


def _show_hod_analytics(dept_id: int, dept_name: str):
    """Analytics charts for the HOD."""
    st.markdown(f"## 📈 Analytics — {dept_name}")

    students = get_dept_students_for_hod(dept_id)
    if not students:
        st.info("No data available for analytics.")
        return

    df = pd.DataFrame(students)

    col1, col2 = st.columns(2)
    with col1:
        # Placed vs Not Placed pie
        placed = sum(1 for s in students
                     if s.get("placement_status") == "Placed")
        not_placed = len(students) - placed
        fig_pie = px.pie(
            values=[placed, not_placed],
            names=["Placed", "Not Placed"],
            title="Placement Status",
            color_discrete_sequence=["#28a745", "#dc3545"],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # CGPA Distribution
        if "cgpa" in df.columns:
            fig_cgpa = px.histogram(
                df,
                x="cgpa",
                nbins=20,
                title="CGPA Distribution",
                color_discrete_sequence=["#1e3c72"],
                labels={"cgpa": "CGPA", "count": "Students"},
            )
            st.plotly_chart(fig_cgpa, use_container_width=True)

    # Package distribution for placed students
    placed_students = [
        s for s in students
        if s.get("highest_package") and float(s["highest_package"] or 0) > 0
    ]
    if placed_students:
        df_placed = pd.DataFrame(placed_students)
        fig_pkg = px.histogram(
            df_placed,
            x="highest_package",
            nbins=10,
            title="Package Distribution (LPA)",
            color_discrete_sequence=["#2a5298"],
            labels={"highest_package": "Package (LPA)", "count": "Students"},
        )
        st.plotly_chart(fig_pkg, use_container_width=True)
