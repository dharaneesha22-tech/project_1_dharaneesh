"""
ML module: Career path recommendation based on student skill profile.
Uses a simple cosine-similarity approach against predefined career profiles.
Falls back to rule-based matching if scikit-learn is unavailable.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Career profiles ──────────────────────────────────────────────────────────

CAREER_PROFILES = {
    "Java Developer": {
        "skills": {"java", "spring boot", "sql", "rest api",
                   "data structures", "algorithms", "maven", "git"},
        "description": "Build enterprise applications using Java and Spring ecosystem.",
    },
    "Python Developer": {
        "skills": {"python", "django", "flask", "sql", "rest api",
                   "git", "data structures"},
        "description": "Develop backend services and automation using Python.",
    },
    "Data Analyst": {
        "skills": {"python", "sql", "excel", "power bi", "tableau",
                   "pandas", "numpy", "data analysis"},
        "description": "Analyze and visualize data to drive business decisions.",
    },
    "Data Scientist": {
        "skills": {"python", "machine learning", "deep learning", "pandas",
                   "numpy", "scikit-learn", "sql", "statistics"},
        "description": "Build predictive models and extract insights from data.",
    },
    "ML Engineer": {
        "skills": {"python", "machine learning", "deep learning",
                   "tensorflow", "pytorch", "docker", "aws", "mlops"},
        "description": "Deploy and maintain machine learning models at scale.",
    },
    "Backend Developer": {
        "skills": {"python", "java", "sql", "rest api", "docker",
                   "microservices", "redis", "git"},
        "description": "Design and build scalable backend APIs and services.",
    },
    "Software Developer": {
        "skills": {"python", "java", "javascript", "sql",
                   "data structures", "algorithms", "git", "agile"},
        "description": "Full-stack or general software development role.",
    },
    "Frontend Developer": {
        "skills": {"html", "css", "javascript", "react",
                   "typescript", "bootstrap", "git"},
        "description": "Build responsive and interactive user interfaces.",
    },
    "DevOps Engineer": {
        "skills": {"docker", "kubernetes", "aws", "linux",
                   "bash", "git", "ci/cd", "terraform"},
        "description": "Automate infrastructure and deployment pipelines.",
    },
    "Business Analyst": {
        "skills": {"sql", "excel", "power bi", "communication",
                   "agile", "jira", "data analysis"},
        "description": "Bridge technical teams and business stakeholders.",
    },
}


def _cosine_similarity(set_a: set, set_b: set) -> float:
    """Simple Jaccard similarity between two skill sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def recommend_careers(student_skills: list,
                      top_n: int = 3) -> list:
    """
    Recommend top-N career paths for a student based on their skills.

    Args:
        student_skills: List of skill name strings the student has.
        top_n: Number of recommendations to return.

    Returns:
        List of dicts:
        {
            "career": str,
            "match_pct": float,
            "matched_skills": list,
            "missing_skills": list,
            "description": str,
        }
    """
    if not student_skills:
        return []

    student_set = {s.lower().strip() for s in student_skills}
    results = []

    for career, profile in CAREER_PROFILES.items():
        required = profile["skills"]
        match_score = _cosine_similarity(student_set, required)
        matched  = sorted(student_set & required)
        missing  = sorted(required - student_set)

        results.append({
            "career": career,
            "match_pct": round(match_score * 100, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "description": profile["description"],
        })

    results.sort(key=lambda r: r["match_pct"], reverse=True)
    return results[:top_n]


def get_student_career_recommendations(student_id: int,
                                        top_n: int = 3) -> list:
    """
    Fetch student skills from DB and return career recommendations.
    """
    try:
        from utils.database import execute_query

        skills_rows = execute_query(
            "SELECT skill_name FROM student_skills WHERE student_id=%s",
            (student_id,),
            fetch="all",
        ) or []
        skills = [r["skill_name"] for r in skills_rows]
        return recommend_careers(skills, top_n)
    except Exception as e:
        logger.error(f"get_student_career_recommendations error: {e}")
        return []


# ─── Streamlit widget ─────────────────────────────────────────────────────────

def show_career_recommendations(student_id: int = None,
                                 student_skills: list = None):
    """
    Streamlit widget showing career recommendations and skill gaps.
    """
    try:
        import streamlit as st

        st.markdown("### 🎯 Career Path Recommendations")

        if student_id:
            recommendations = get_student_career_recommendations(student_id)
            st.caption("*Based on your current skill profile*")
        elif student_skills:
            recommendations = recommend_careers(student_skills)
        else:
            # Manual skill entry
            with st.expander("✍️ Enter Skills Manually"):
                manual = st.text_area(
                    "Enter your skills (comma-separated)",
                    placeholder="Python, SQL, Machine Learning, React",
                )
            if manual:
                skills_input = [s.strip() for s in manual.split(",")
                                if s.strip()]
                recommendations = recommend_careers(skills_input)
            else:
                st.info("Add skills to get career recommendations.")
                return

        if not recommendations:
            st.warning(
                "No recommendations available. "
                "Add skills to your profile first."
            )
            return

        for i, rec in enumerate(recommendations):
            rank_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🏅"
            pct = rec["match_pct"]
            bar_color = (
                "#28a745" if pct >= 60
                else "#ffc107" if pct >= 30
                else "#dc3545"
            )

            with st.expander(
                f"{rank_icon} {rec['career']} — {pct:.0f}% match",
                expanded=(i == 0),
            ):
                st.markdown(f"*{rec['description']}*")

                # Progress bar styled with markdown
                st.progress(pct / 100)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**✅ Matched Skills:**")
                    if rec["matched_skills"]:
                        for sk in rec["matched_skills"]:
                            st.markdown(f"- {sk.title()}")
                    else:
                        st.markdown("*None yet*")

                with col2:
                    st.markdown("**📚 Skills to Learn:**")
                    if rec["missing_skills"]:
                        for sk in rec["missing_skills"]:
                            st.markdown(f"- {sk.title()}")
                    else:
                        st.markdown("*You have all required skills!* 🎉")

    except Exception as e:
        logger.error(f"show_career_recommendations error: {e}")
