"""
Analytics module: Plotly charts and interactive dashboards.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import execute_query


# ─── Data helpers ──────────────────────────────────────────────────────────

def _get_dept_placement_data(batch_year: int = None, dept_id: int = None):
    query = """
        SELECT d.name AS department, d.id AS dept_id,
               COUNT(DISTINCT s.id)                                         AS total,
               COUNT(DISTINCT CASE WHEN v.placement_status='Placed'
                                   THEN s.id END)                          AS placed,
               COUNT(DISTINCT CASE WHEN v.placement_status='Not Placed'
                                   THEN s.id END)                          AS not_placed,
               ROUND(
                   COUNT(DISTINCT CASE WHEN v.placement_status='Placed'
                                       THEN s.id END) * 100.0 /
                   NULLIF(COUNT(DISTINCT s.id), 0), 2
               )                                                            AS pct,
               MAX(v.highest_package)                                       AS highest_pkg,
               ROUND(AVG(CASE WHEN v.placement_status='Placed'
                              THEN v.highest_package END), 2)              AS avg_pkg
        FROM departments d
        LEFT JOIN students s ON d.id = s.department_id AND s.is_active=TRUE
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
    """
    conds, params = [], []
    if batch_year:
        conds.append("s.batch_year = %s")
        params.append(batch_year)
    if dept_id:
        conds.append("d.id = %s")
        params.append(dept_id)
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " GROUP BY d.id ORDER BY d.name"
    return execute_query(query, tuple(params), fetch="all") or []


def _get_company_selection_data():
    return execute_query(
        """
        SELECT c.name AS company,
               COUNT(DISTINCT a.id)                                         AS attended,
               COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                   THEN pr.id END)                         AS selected
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


def _get_package_distribution_data(dept_id: int = None):
    query = """
        SELECT pr.package_lpa AS package, d.name AS department
        FROM placement_results pr
        JOIN students s ON pr.student_id = s.id
        JOIN departments d ON s.department_id = d.id
        WHERE pr.status = 'Selected' AND pr.package_lpa IS NOT NULL
    """
    params = ()
    if dept_id:
        query += " AND s.department_id = %s"
        params = (dept_id,)
    return execute_query(query, params, fetch="all") or []


def _get_year_wise_trend():
    return execute_query(
        """
        SELECT s.batch_year,
               COUNT(DISTINCT s.id)                                         AS total,
               COUNT(DISTINCT CASE WHEN v.placement_status='Placed'
                                   THEN s.id END)                          AS placed,
               ROUND(
                   COUNT(DISTINCT CASE WHEN v.placement_status='Placed'
                                       THEN s.id END) * 100.0 /
                   NULLIF(COUNT(DISTINCT s.id), 0), 2
               )                                                            AS pct
        FROM students s
        LEFT JOIN v_student_placement_summary v ON s.id = v.student_id
        WHERE s.is_active = TRUE
        GROUP BY s.batch_year
        ORDER BY s.batch_year
        """,
        fetch="all",
    ) or []


# ─── Chart functions ───────────────────────────────────────────────────────

def plot_dept_placement_bar(data: list) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="department",
        y=["placed", "not_placed"],
        barmode="stack",
        title="Department-wise Placement",
        labels={"value": "Students", "variable": "Status",
                "department": "Department"},
        color_discrete_map={"placed": "#28a745", "not_placed": "#dc3545"},
    )
    fig.update_layout(legend_title_text="Status")
    return fig


def plot_placement_status_pie(placed: int, not_placed: int,
                              title: str = "Placement Status") -> go.Figure:
    fig = px.pie(
        values=[placed, not_placed],
        names=["Placed", "Not Placed"],
        title=title,
        color_discrete_sequence=["#28a745", "#dc3545"],
        hole=0.4,
    )
    return fig


def plot_company_selection_bar(data: list) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="company",
        y=["attended", "selected"],
        barmode="group",
        title="Company-wise Attendance vs Selection",
        color_discrete_sequence=["#1e3c72", "#48b5f0"],
        labels={"value": "Students", "variable": "Category",
                "company": "Company"},
    )
    fig.update_xaxes(tickangle=30)
    return fig


def plot_package_distribution(data: list,
                               dept: str = None) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    title = f"Package Distribution — {dept}" if dept else "Package Distribution (LPA)"
    fig = px.histogram(
        df,
        x="package",
        nbins=15,
        title=title,
        color_discrete_sequence=["#2a5298"],
        labels={"package": "Package (LPA)", "count": "Students"},
    )
    return fig


def plot_dept_placement_percentage(data: list) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="department",
        y="pct",
        title="Placement % by Department",
        color="pct",
        color_continuous_scale="Blues",
        labels={"pct": "Placement %", "department": "Department"},
        text="pct",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, 110])
    return fig


def plot_highest_package_by_dept(data: list) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    df = df[df["highest_pkg"].notna()]
    fig = px.bar(
        df,
        x="department",
        y="highest_pkg",
        title="Highest Package by Department (LPA)",
        color="highest_pkg",
        color_continuous_scale="Teal",
        labels={"highest_pkg": "Package (LPA)", "department": "Department"},
        text="highest_pkg",
    )
    fig.update_traces(texttemplate="₹%{text:.1f}", textposition="outside")
    return fig


def plot_year_wise_trend(data: list) -> go.Figure:
    if not data:
        return go.Figure()
    df = pd.DataFrame(data)
    fig = px.line(
        df,
        x="batch_year",
        y="pct",
        title="Year-wise Placement Trend (%)",
        markers=True,
        color_discrete_sequence=["#1e3c72"],
        labels={"pct": "Placement %", "batch_year": "Batch Year"},
    )
    fig.update_yaxes(range=[0, 110])
    return fig


# ─── Full Analytics Page ────────────────────────────────────────────────────

def show_analytics_page(dept_id: int = None):
    """Render the complete analytics dashboard."""
    st.markdown("## 📈 Placement Analytics")

    # ── Filters ──────────────────────────────────────────────────────
    departments = execute_query(
        "SELECT id, name FROM departments ORDER BY name", fetch="all"
    ) or []
    batch_years = execute_query(
        "SELECT DISTINCT batch_year FROM students ORDER BY batch_year DESC",
        fetch="all",
    ) or []

    col1, col2 = st.columns(2)
    with col1:
        dept_opts = {0: "All Departments"}
        dept_opts.update({d["id"]: d["name"] for d in departments})
        selected_dept = st.selectbox(
            "Department",
            list(dept_opts.keys()),
            format_func=lambda k: dept_opts[k],
        )
        if dept_id:
            selected_dept = dept_id
    with col2:
        year_opts = [0] + [b["batch_year"] for b in batch_years]
        selected_year = st.selectbox(
            "Batch Year",
            year_opts,
            format_func=lambda y: "All Years" if y == 0 else str(y),
        )

    dept_filter = selected_dept if selected_dept else None
    year_filter = selected_year if selected_year else None

    # ── Data ──────────────────────────────────────────────────────────
    dept_data    = _get_dept_placement_data(year_filter, dept_filter)
    company_data = _get_company_selection_data()
    pkg_data     = _get_package_distribution_data(dept_filter)
    trend_data   = _get_year_wise_trend()

    # ── Row 1 ─────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        fig = plot_dept_placement_bar(dept_data)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        if dept_data:
            total  = sum(d["total"] for d in dept_data)
            placed = sum(d["placed"] for d in dept_data)
            fig2   = plot_placement_status_pie(placed, total - placed)
            st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2 ─────────────────────────────────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        fig3 = plot_company_selection_bar(company_data)
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        fig4 = plot_package_distribution(pkg_data)
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3 ─────────────────────────────────────────────────────────
    col5, col6 = st.columns(2)
    with col5:
        fig5 = plot_year_wise_trend(trend_data)
        st.plotly_chart(fig5, use_container_width=True)
    with col6:
        fig6 = plot_highest_package_by_dept(dept_data)
        st.plotly_chart(fig6, use_container_width=True)

    # ── Placement % table ──────────────────────────────────────────────
    st.markdown("### 📊 Detailed Statistics Table")
    if dept_data:
        df = pd.DataFrame(dept_data)
        display_cols = ["department", "total", "placed", "not_placed",
                        "pct", "highest_pkg", "avg_pkg"]
        df = df[[c for c in display_cols if c in df.columns]]
        df.rename(columns={
            "department": "Department",
            "total": "Total",
            "placed": "Placed",
            "not_placed": "Not Placed",
            "pct": "Placement %",
            "highest_pkg": "Highest Pkg",
            "avg_pkg": "Avg Pkg",
        }, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
