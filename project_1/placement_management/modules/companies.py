"""
Company management module.
"""

import streamlit as st
import pandas as pd
from utils.database import execute_query
from utils.security import get_current_user, log_audit
from utils.validators import sanitize_string


def get_all_companies():
    """Return all companies."""
    return execute_query(
        """
        SELECT c.id, c.name, c.industry, c.location, c.website,
               c.contact_email, c.contact_phone, c.contact_person,
               c.created_at,
               COUNT(DISTINCT pd.id) AS total_drives
        FROM companies c
        LEFT JOIN placement_drives pd ON c.id = pd.company_id
        GROUP BY c.id
        ORDER BY c.name
        """,
        fetch="all",
    ) or []


def get_company_by_id(company_id: int):
    return execute_query(
        "SELECT * FROM companies WHERE id = %s", (company_id,), fetch="one"
    )


def add_company(data: dict) -> int:
    """Insert a new company. Returns new ID."""
    query = """
        INSERT INTO companies
            (name, industry, location, website, description,
             contact_person, contact_email, contact_phone, created_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    user = get_current_user()
    execute_query(
        query,
        (
            sanitize_string(data["name"]),
            sanitize_string(data.get("industry", "")),
            sanitize_string(data.get("location", "")),
            sanitize_string(data.get("website", "")),
            sanitize_string(data.get("description", "")),
            sanitize_string(data.get("contact_person", "")),
            sanitize_string(data.get("contact_email", "")),
            sanitize_string(data.get("contact_phone", "")),
            user["id"] if user else None,
        ),
    )
    new_id = execute_query("SELECT LAST_INSERT_ID() AS id", fetch="one")
    cid = new_id["id"] if new_id else None
    if user:
        log_audit("COMPANY_CREATED", user["id"],
                  f"Company '{data['name']}' created", "companies", cid)
    return cid


def update_company(company_id: int, data: dict):
    """Update company details."""
    query = """
        UPDATE companies
        SET name=%s, industry=%s, location=%s, website=%s,
            description=%s, contact_person=%s,
            contact_email=%s, contact_phone=%s
        WHERE id=%s
    """
    execute_query(
        query,
        (
            sanitize_string(data["name"]),
            sanitize_string(data.get("industry", "")),
            sanitize_string(data.get("location", "")),
            sanitize_string(data.get("website", "")),
            sanitize_string(data.get("description", "")),
            sanitize_string(data.get("contact_person", "")),
            sanitize_string(data.get("contact_email", "")),
            sanitize_string(data.get("contact_phone", "")),
            company_id,
        ),
    )
    user = get_current_user()
    if user:
        log_audit("COMPANY_UPDATED", user["id"],
                  f"Company ID {company_id} updated", "companies", company_id)


def get_company_stats(drive_id: int = None):
    """Return per-company statistics (optionally filtered by drive)."""
    query = """
        SELECT
            c.name        AS company,
            c.industry,
            pd.job_role,
            pd.drive_date,
            pd.package_lpa,
            COUNT(DISTINCT a.id)                                    AS registered,
            COUNT(DISTINCT CASE WHEN a.status != 'Registered'
                                THEN a.id END)                      AS attended,
            COUNT(DISTINCT CASE WHEN a.status IN
                    ('Shortlisted','Technical Round','HR Round',
                     'Selected')
                                THEN a.id END)                      AS shortlisted,
            COUNT(DISTINCT CASE WHEN pr.status = 'Selected'
                                THEN pr.id END)                     AS selected
        FROM companies c
        JOIN placement_drives pd ON c.id = pd.company_id
        LEFT JOIN applications a  ON pd.id = a.drive_id
        LEFT JOIN placement_results pr ON pd.id = pr.drive_id
    """
    params = ()
    if drive_id:
        query += " WHERE pd.id = %s"
        params = (drive_id,)
    query += " GROUP BY c.id, pd.id ORDER BY pd.drive_date DESC"
    return execute_query(query, params, fetch="all") or []


# ─── Streamlit UI ──────────────────────────────────────────────────────────


def show_companies_page(can_edit: bool = False):
    """Render the Companies management page."""
    st.markdown("## 🏢 Companies")

    if can_edit:
        tabs = st.tabs(["📋 All Companies", "📊 Drive Statistics", "➕ Add Company"])
    else:
        tabs = st.tabs(["📋 All Companies", "📊 Drive Statistics"])

    # ── Tab 1: All Companies ──────────────────────────────────────────
    with tabs[0]:
        companies = get_all_companies()
        if not companies:
            st.info("No companies found. Add companies to get started.")
            return

        df = pd.DataFrame(companies)
        df = df[["name", "industry", "location", "total_drives",
                 "contact_email", "contact_phone"]]
        df.columns = ["Company", "Industry", "Location",
                      "Drives", "Email", "Phone"]

        search = st.text_input("🔍 Search companies", placeholder="Company name or industry...")
        if search:
            mask = df.apply(
                lambda r: search.lower() in str(r).lower(), axis=1
            )
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True)

        if can_edit:
            with st.expander("✏️ Edit Company"):
                company_names = [c["name"] for c in companies]
                sel = st.selectbox("Select company to edit", company_names,
                                   key="edit_company_sel")
                cdata = next(c for c in companies if c["name"] == sel)
                _show_edit_company_form(cdata)

    # ── Tab 2: Drive Statistics ───────────────────────────────────────
    with tabs[1]:
        stats = get_company_stats()
        if stats:
            df_stats = pd.DataFrame(stats)
            df_stats.columns = [
                "Company", "Industry", "Job Role", "Drive Date",
                "Package (LPA)", "Registered", "Attended",
                "Shortlisted", "Selected",
            ]
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
        else:
            st.info("No drive data available yet.")

    # ── Tab 3: Add Company ────────────────────────────────────────────
    if can_edit:
        with tabs[2]:
            _show_add_company_form()


def _show_add_company_form():
    """Form to add a new company."""
    with st.form("add_company_form"):
        st.markdown("### Add New Company")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Company Name *")
            industry = st.text_input("Industry")
            location = st.text_input("Location")
            website = st.text_input("Website")
        with col2:
            contact_person = st.text_input("Contact Person")
            contact_email = st.text_input("Contact Email")
            contact_phone = st.text_input("Contact Phone")
        description = st.text_area("Description")

        if st.form_submit_button("💾 Add Company"):
            if not name.strip():
                st.error("Company name is required.")
                return
            add_company({
                "name": name, "industry": industry,
                "location": location, "website": website,
                "description": description, "contact_person": contact_person,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
            })
            st.success(f"Company '{name}' added successfully!")
            st.rerun()


def _show_edit_company_form(cdata: dict):
    """Form to edit an existing company."""
    with st.form(f"edit_company_{cdata['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Company Name", value=cdata.get("name", ""))
            industry = st.text_input("Industry", value=cdata.get("industry", ""))
            location = st.text_input("Location", value=cdata.get("location", ""))
        with col2:
            contact_person = st.text_input(
                "Contact Person", value=cdata.get("contact_person", ""))
            contact_email = st.text_input(
                "Contact Email", value=cdata.get("contact_email", ""))
            contact_phone = st.text_input(
                "Contact Phone", value=cdata.get("contact_phone", ""))

        if st.form_submit_button("💾 Update Company"):
            update_company(cdata["id"], {
                "name": name, "industry": industry,
                "location": location,
                "contact_person": contact_person,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "description": cdata.get("description", ""),
                "website": cdata.get("website", ""),
            })
            st.success("Company updated successfully!")
            st.rerun()
