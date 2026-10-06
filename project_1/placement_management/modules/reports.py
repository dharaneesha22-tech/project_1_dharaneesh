"""
Reports module: CSV/Excel exports and resume analyzer.
"""

import streamlit as st
import pandas as pd
import io
from utils.database import execute_query


# ─── Data fetchers ──────────────────────────────────────────────────────────

def _get_student_report_data(student_id: int):
    student = execute_query(
        """
        SELECT s.register_number, s.full_name, s.email, s.phone,
               d.name AS department, s.batch_year, s.section,
               ar.cgpa, ar.arrears,
               v.companies_attended, v.companies_selected,
               v.companies_rejected, v.highest_package,
               v.placement_status
        FROM students s
        JOIN departments d ON s.department_id = d.id
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
        WHERE s.id = %s
        """,
        (student_id,),
        fetch="one",
    )
    placements = execute_query(
        """
        SELECT c.name AS company, pd.job_role,
               pd.drive_date, a.status,
               pr.status AS final_status,
               pr.package_lpa AS offered_package,
               pr.is_verified
        FROM applications a
        JOIN placement_drives pd ON a.drive_id = pd.id
        JOIN companies c ON pd.company_id = c.id
        LEFT JOIN placement_results pr ON a.id = pr.application_id
        WHERE a.student_id = %s
        ORDER BY pd.drive_date
        """,
        (student_id,),
        fetch="all",
    ) or []
    skills = execute_query(
        "SELECT skill_name, proficiency FROM student_skills WHERE student_id=%s",
        (student_id,), fetch="all",
    ) or []
    certs = execute_query(
        "SELECT title, issuing_org FROM certifications WHERE student_id=%s",
        (student_id,), fetch="all",
    ) or []
    return student, placements, skills, certs


def _get_dept_report_data(dept_id: int):
    students = execute_query(
        """
        SELECT s.register_number, s.full_name,
               ar.cgpa, ar.arrears,
               v.companies_attended, v.companies_selected,
               v.placement_status, v.highest_package
        FROM students s
        LEFT JOIN academic_records ar ON s.id = ar.student_id
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
        WHERE s.department_id = %s AND s.is_active = TRUE
        ORDER BY v.placement_status, s.register_number
        """,
        (dept_id,),
        fetch="all",
    ) or []
    companies = execute_query(
        """
        SELECT c.name AS company, pd.job_role, pd.drive_date,
               COUNT(DISTINCT a.id)                                    AS attended,
               COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                   THEN pr.id END)                    AS selected,
               MAX(pr.package_lpa)                                     AS max_package
        FROM companies c
        JOIN placement_drives pd ON c.id = pd.company_id
        JOIN applications a ON pd.id = a.drive_id
        JOIN students s ON a.student_id = s.id
        LEFT JOIN placement_results pr ON a.id = pr.application_id
        WHERE s.department_id = %s
        GROUP BY c.id, pd.id
        ORDER BY pd.drive_date DESC
        """,
        (dept_id,),
        fetch="all",
    ) or []
    return students, companies


def _get_college_report_data():
    dept_stats = execute_query(
        "SELECT * FROM v_department_stats ORDER BY department",
        fetch="all",
    ) or []
    company_stats = execute_query(
        """
        SELECT c.name AS company, c.industry,
               COUNT(DISTINCT a.id)                                    AS attended,
               COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                   THEN pr.id END)                    AS selected,
               MAX(pr.package_lpa)                                     AS max_package,
               AVG(CASE WHEN pr.status='Selected'
                        THEN pr.package_lpa END)                       AS avg_package
        FROM companies c
        JOIN placement_drives pd ON c.id = pd.company_id
        JOIN applications a ON pd.id = a.drive_id
            AND a.status NOT IN ('Registered','Withdrawn')
        LEFT JOIN placement_results pr ON a.id = pr.application_id
        GROUP BY c.id
        ORDER BY selected DESC
        """,
        fetch="all",
    ) or []
    return dept_stats, company_stats


def _to_excel(dfs: dict) -> bytes:
    """Write multiple DataFrames to an Excel workbook."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()


# ─── Student Report ─────────────────────────────────────────────────────────

def show_student_report(student_id: int):
    """Show and export student placement report."""
    st.markdown("## 📄 Student Report")
    student, placements, skills, certs = _get_student_report_data(student_id)

    if not student:
        st.error("Student not found.")
        return

    # Personal details
    st.markdown("### 👤 Personal Details")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {student['full_name']}")
        st.markdown(f"**Register No:** {student['register_number']}")
        st.markdown(f"**Department:** {student['department']}")
        st.markdown(f"**Batch Year:** {student['batch_year']}")
    with col2:
        st.markdown(f"**CGPA:** {student.get('cgpa', 'N/A')}")
        st.markdown(f"**Arrears:** {student.get('arrears', 0)}")
        st.markdown(f"**Email:** {student['email']}")
        st.markdown(
            f"**Placement Status:** "
            f"{'🟢 PLACED' if student.get('placement_status')=='Placed' else '🔴 NOT PLACED'}"
        )

    # Summary
    st.markdown("### 📊 Placement Summary")
    col3, col4, col5, col6 = st.columns(4)
    col3.metric("Companies Attended", student.get("companies_attended", 0))
    col4.metric("Selected",           student.get("companies_selected", 0))
    col5.metric("Rejected",           student.get("companies_rejected", 0))
    col6.metric("Highest Package",
                f"₹{student.get('highest_package', 0)} LPA"
                if student.get("highest_package") else "—")

    # Placement history table
    if placements:
        st.markdown("### 🏢 Placement History")
        df_p = pd.DataFrame(placements)
        df_p.rename(columns={
            "company": "Company", "job_role": "Job Role",
            "drive_date": "Drive Date", "status": "Status",
            "final_status": "Result", "offered_package": "Package",
            "is_verified": "Verified",
        }, inplace=True)
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    # Skills & Certs
    col7, col8 = st.columns(2)
    with col7:
        if skills:
            st.markdown("### 🎯 Skills")
            df_s = pd.DataFrame(skills)
            df_s.columns = ["Skill", "Proficiency"]
            st.dataframe(df_s, use_container_width=True, hide_index=True)
    with col8:
        if certs:
            st.markdown("### 🏅 Certifications")
            df_c = pd.DataFrame(certs)
            df_c.columns = ["Title", "Organization"]
            st.dataframe(df_c, use_container_width=True, hide_index=True)

    # Export buttons
    st.markdown("### ⬇️ Export")
    col9, col10 = st.columns(2)
    with col9:
        df_export = pd.DataFrame([student])
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export CSV", csv,
                           f"student_{student['register_number']}.csv",
                           "text/csv")
    with col10:
        excel_data = _to_excel({
            "Student Details": pd.DataFrame([student]),
            "Placements": pd.DataFrame(placements) if placements else pd.DataFrame(),
            "Skills": pd.DataFrame(skills) if skills else pd.DataFrame(),
        })
        st.download_button(
            "📊 Export Excel",
            excel_data,
            f"student_{student['register_number']}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ─── Department Report ───────────────────────────────────────────────────────

def show_dept_report(dept_id: int, dept_name: str):
    """Show and export department placement report."""
    st.markdown(f"## 📄 Department Report — {dept_name}")
    students, companies = _get_dept_report_data(dept_id)

    placed_count     = sum(1 for s in students
                          if s.get("placement_status") == "Placed")
    not_placed_count = len(students) - placed_count
    placement_pct    = (
        placed_count / len(students) * 100 if students else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students",  len(students))
    col2.metric("Placed",          placed_count)
    col3.metric("Not Placed",      not_placed_count)
    col4.metric("Placement %",     f"{placement_pct:.1f}%")

    if students:
        st.markdown("### 👥 Students")
        df_s = pd.DataFrame(students)
        df_s.rename(columns={
            "register_number": "Reg No", "full_name": "Name",
            "cgpa": "CGPA", "arrears": "Arrears",
            "companies_attended": "Attended",
            "companies_selected": "Selected",
            "placement_status": "Status",
            "highest_package": "Highest Pkg",
        }, inplace=True)
        st.dataframe(df_s, use_container_width=True, hide_index=True)

    if companies:
        st.markdown("### 🏢 Company Statistics")
        df_c = pd.DataFrame(companies)
        df_c.rename(columns={
            "company": "Company", "job_role": "Job Role",
            "drive_date": "Drive Date", "attended": "Attended",
            "selected": "Selected", "max_package": "Max Package",
        }, inplace=True)
        st.dataframe(df_c, use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)
    with col_a:
        df_exp = pd.DataFrame(students) if students else pd.DataFrame()
        csv = df_exp.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export CSV", csv,
                           f"dept_{dept_id}_report.csv", "text/csv")
    with col_b:
        excel = _to_excel({
            "Students": pd.DataFrame(students) if students else pd.DataFrame(),
            "Companies": pd.DataFrame(companies) if companies else pd.DataFrame(),
        })
        st.download_button(
            "📊 Export Excel",
            excel,
            f"dept_{dept_id}_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ─── College Report ──────────────────────────────────────────────────────────

def show_college_report():
    """Show and export the full college placement report."""
    st.markdown("## 📄 College Placement Report")
    dept_stats, company_stats = _get_college_report_data()

    if dept_stats:
        st.markdown("### 🏛️ Department-wise Summary")
        df_d = pd.DataFrame(dept_stats)
        display_cols = [
            "department", "total_students", "placed_students",
            "not_placed_students", "placement_percentage",
            "highest_package", "avg_package",
        ]
        df_d = df_d[[c for c in display_cols if c in df_d.columns]]
        df_d.rename(columns={
            "department": "Department",
            "total_students": "Total",
            "placed_students": "Placed",
            "not_placed_students": "Not Placed",
            "placement_percentage": "Placement %",
            "highest_package": "Highest Pkg",
            "avg_package": "Avg Pkg",
        }, inplace=True)
        st.dataframe(df_d, use_container_width=True, hide_index=True)

    if company_stats:
        st.markdown("### 🏢 Company-wise Summary")
        df_c = pd.DataFrame(company_stats)
        df_c.rename(columns={
            "company": "Company", "industry": "Industry",
            "attended": "Attended", "selected": "Selected",
            "max_package": "Max Package", "avg_package": "Avg Package",
        }, inplace=True)
        st.dataframe(df_c, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        csv_d = pd.DataFrame(dept_stats).to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export Dept CSV", csv_d,
                           "college_dept_report.csv", "text/csv")
    with col2:
        excel = _to_excel({
            "Departments": pd.DataFrame(dept_stats) if dept_stats else pd.DataFrame(),
            "Companies": pd.DataFrame(company_stats) if company_stats else pd.DataFrame(),
        })
        st.download_button(
            "📊 Export Excel",
            excel,
            "college_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ─── Resume Analyzer ─────────────────────────────────────────────────────────

def show_resume_analyzer(student: dict):
    """Resume upload and skill matching analyzer."""
    st.markdown("## 📄 Resume Analyzer")
    st.info(
        "Upload your PDF resume to extract skills and compare with job requirements."
    )

    uploaded = st.file_uploader(
        "Upload Resume (PDF)", type=["pdf"],
        help="Maximum size: 5 MB",
    )

    col1, col2 = st.columns(2)
    with col1:
        # Job requirements to compare against
        companies = execute_query(
            """
            SELECT c.name, pd.job_role, pd.required_skills
            FROM companies c
            JOIN placement_drives pd ON c.id = pd.company_id
            WHERE pd.required_skills IS NOT NULL
              AND pd.required_skills != ''
            ORDER BY c.name
            """,
            fetch="all",
        ) or []

        if companies:
            drive_labels = [
                f"{c['name']} — {c['job_role']}" for c in companies
            ]
            sel_idx = st.selectbox(
                "Compare with Job Requirements",
                range(len(drive_labels)),
                format_func=lambda i: drive_labels[i],
            )
            sel_company = companies[sel_idx]
            required_skills_raw = sel_company.get("required_skills", "")
            required_skills = [
                s.strip().lower()
                for s in required_skills_raw.split(",")
                if s.strip()
            ]
        else:
            required_skills = []
            st.info("No job requirements found.")

    with col2:
        if required_skills:
            st.markdown("**Required Skills:**")
            for sk in required_skills:
                st.markdown(f"- {sk.title()}")

    if uploaded:
        if uploaded.size > 5 * 1024 * 1024:
            st.error("File size must be under 5 MB.")
            return

        pdf_text = _extract_pdf_text(uploaded)
        if not pdf_text:
            st.error("Could not extract text from the PDF. "
                     "Ensure the PDF is text-based, not scanned.")
            return

        extracted_skills = _extract_skills_from_text(pdf_text)

        st.markdown("---")
        st.markdown("### 🔍 Analysis Results")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Extracted Skills from Resume:**")
            for sk in sorted(extracted_skills):
                st.markdown(f"✅ {sk.title()}")

        with col4:
            if required_skills:
                st.markdown("**Skill Match Analysis:**")
                matched   = [s for s in required_skills
                             if s in extracted_skills]
                missing   = [s for s in required_skills
                             if s not in extracted_skills]
                match_pct = (
                    len(matched) / len(required_skills) * 100
                    if required_skills else 0
                )
                st.metric("Match Score", f"{match_pct:.0f}%")

                for sk in required_skills:
                    if sk in extracted_skills:
                        st.markdown(f"✅ {sk.title()}")
                    else:
                        st.markdown(f"❌ {sk.title()}")

                if missing:
                    st.markdown("---")
                    st.markdown("**📚 Missing Skills to Learn:**")
                    for sk in missing:
                        st.markdown(f"- {sk.title()}")

        # Store parsed skills in DB
        if extracted_skills:
            skills_str = ", ".join(sorted(extracted_skills))
            execute_query(
                """
                INSERT INTO resumes
                    (student_id, filename, parsed_skills)
                VALUES (%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    filename=VALUES(filename),
                    parsed_skills=VALUES(parsed_skills)
                """,
                (student["id"], uploaded.name, skills_str),
            )
            st.caption(f"Parsed skills saved: {skills_str}")


def _extract_pdf_text(uploaded_file) -> str:
    """Extract text from an uploaded PDF file."""
    try:
        import pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            texts = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(texts)
    except ImportError:
        pass
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(uploaded_file)
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
    except Exception:
        return ""


def _extract_skills_from_text(text: str) -> set:
    """Extract known skills from resume text (keyword matching)."""
    SKILL_KEYWORDS = {
        "python", "java", "c", "c++", "javascript", "typescript",
        "react", "angular", "vue", "node.js", "nodejs",
        "spring", "spring boot", "django", "flask", "fastapi",
        "sql", "mysql", "postgresql", "mongodb", "redis",
        "html", "css", "bootstrap", "tailwind",
        "aws", "azure", "gcp", "docker", "kubernetes",
        "git", "github", "gitlab",
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "data science", "data analysis", "pandas", "numpy",
        "scikit-learn", "power bi", "tableau",
        "rest api", "graphql", "microservices",
        "linux", "bash", "powershell",
        "agile", "scrum", "jira",
        "communication", "teamwork", "leadership",
        "testing", "selenium", "junit", "pytest",
        "data structures", "algorithms", "dbms",
        "networking", "cyber security",
        "excel", "word", "powerpoint",
    }
    text_lower = text.lower()
    found = set()
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found.add(skill)
    return found
