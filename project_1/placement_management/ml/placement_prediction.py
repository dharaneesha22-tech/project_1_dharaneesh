"""
ML module: Placement probability prediction using Scikit-learn.
Predicts HIGH / MEDIUM / LOW placement probability.

The module is self-contained and trains an in-memory model on every
call (since the dataset grows over time).  If scikit-learn or pandas
are unavailable the functions degrade gracefully and return None.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Feature & target definitions ────────────────────────────────────────────

FEATURE_COLUMNS = [
    "cgpa",
    "arrears",
    "coding_score",
    "aptitude_score",
    "skills_count",
    "certifications_count",
    "projects_count",
    "interview_score",
]

LABEL_MAP = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}


# ─── Data preparation ─────────────────────────────────────────────────────────

def _load_training_data():
    """
    Load training data from the database.
    Returns (X, y) as numpy arrays, or (None, None) on failure.
    """
    try:
        import pandas as pd
        import numpy as np
        from utils.database import execute_query

        rows = execute_query(
            """
            SELECT
                COALESCE(ar.cgpa, 0)                                AS cgpa,
                COALESCE(ar.arrears, 0)                             AS arrears,
                0                                                   AS coding_score,
                0                                                   AS aptitude_score,
                COUNT(DISTINCT ss.id)                               AS skills_count,
                COUNT(DISTINCT cert.id)                             AS certifications_count,
                COUNT(DISTINCT proj.id)                             AS projects_count,
                0                                                   AS interview_score,
                CASE
                    WHEN COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                            THEN pr.id END) > 0
                    THEN 2
                    WHEN ar.cgpa >= 7.0 AND ar.arrears <= 1 THEN 1
                    ELSE 0
                END                                                 AS label
            FROM students s
            LEFT JOIN academic_records ar       ON s.id = ar.student_id
            LEFT JOIN student_skills ss         ON s.id = ss.student_id
            LEFT JOIN certifications cert       ON s.id = cert.student_id
            LEFT JOIN projects proj             ON s.id = proj.student_id
            LEFT JOIN placement_results pr      ON s.id = pr.student_id
            WHERE s.is_active = TRUE
            GROUP BY s.id, ar.cgpa, ar.arrears
            HAVING cgpa > 0
            """,
            fetch="all",
        )

        if not rows or len(rows) < 10:
            return None, None

        df = pd.DataFrame(rows)
        X = df[FEATURE_COLUMNS].values.astype(float)
        y = df["label"].values.astype(int)
        return X, y

    except Exception as e:
        logger.warning(f"Could not load training data: {e}")
        return None, None


def _build_synthetic_data():
    """
    Build synthetic training data when DB data is insufficient.
    Ensures the model is always trainable.
    """
    try:
        import numpy as np

        rng = np.random.default_rng(42)
        n = 300

        cgpa        = rng.uniform(5.0, 10.0, n)
        arrears     = rng.integers(0, 6, n)
        coding      = rng.uniform(30, 100, n)
        aptitude    = rng.uniform(30, 100, n)
        skills      = rng.integers(1, 15, n)
        certs       = rng.integers(0, 6, n)
        projects    = rng.integers(0, 5, n)
        interview   = rng.uniform(30, 100, n)

        score = (
            cgpa * 8 +
            (5 - arrears) * 4 +
            coding * 0.3 +
            aptitude * 0.3 +
            skills * 1.5 +
            certs * 2 +
            projects * 1 +
            interview * 0.2
        )

        labels = np.where(score > 90, 2, np.where(score > 70, 1, 0))

        X = np.column_stack([
            cgpa, arrears, coding, aptitude,
            skills, certs, projects, interview,
        ])
        return X, labels

    except Exception as e:
        logger.warning(f"Could not build synthetic data: {e}")
        return None, None


def train_model():
    """
    Train a RandomForest classifier.
    Returns (model, scaler) or (None, None).
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        X, y = _load_training_data()

        if X is None or len(X) < 20:
            X, y = _build_synthetic_data()

        if X is None:
            return None, None

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        )
        model.fit(X_scaled, y)
        return model, scaler

    except ImportError:
        logger.warning(
            "scikit-learn not available. ML prediction disabled."
        )
        return None, None
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return None, None


# ─── Prediction ───────────────────────────────────────────────────────────────

def predict_placement(
    cgpa: float,
    arrears: int,
    coding_score: float = 60.0,
    aptitude_score: float = 60.0,
    skills_count: int = 5,
    certifications_count: int = 1,
    projects_count: int = 1,
    interview_score: float = 60.0,
) -> Optional[dict]:
    """
    Predict placement likelihood for a student.

    Returns:
        {
            "prediction": "HIGH" | "MEDIUM" | "LOW",
            "probabilities": {"HIGH": float, "MEDIUM": float, "LOW": float},
            "confidence": float,
        }
        or None if the model is unavailable.
    """
    model, scaler = train_model()
    if model is None:
        return None

    try:
        import numpy as np

        features = np.array([[
            cgpa, arrears, coding_score, aptitude_score,
            skills_count, certifications_count, projects_count,
            interview_score,
        ]])
        features_scaled = scaler.transform(features)
        pred_class = int(model.predict(features_scaled)[0])
        proba = model.predict_proba(features_scaled)[0]

        # Map probabilities to all 3 classes
        classes = list(model.classes_)
        proba_dict = {LABEL_MAP[c]: float(proba[i])
                      for i, c in enumerate(classes)}
        # Fill missing classes with 0
        for label in LABEL_MAP.values():
            proba_dict.setdefault(label, 0.0)

        return {
            "prediction": LABEL_MAP.get(pred_class, "MEDIUM"),
            "probabilities": proba_dict,
            "confidence": float(max(proba)),
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return None


def get_student_prediction(student_id: int) -> Optional[dict]:
    """
    Fetch student data from DB and return placement prediction.
    """
    try:
        from utils.database import execute_query

        data = execute_query(
            """
            SELECT
                COALESCE(ar.cgpa, 0)            AS cgpa,
                COALESCE(ar.arrears, 0)         AS arrears,
                COUNT(DISTINCT ss.id)           AS skills_count,
                COUNT(DISTINCT cert.id)         AS certifications_count,
                COUNT(DISTINCT proj.id)         AS projects_count
            FROM students s
            LEFT JOIN academic_records ar  ON s.id = ar.student_id
            LEFT JOIN student_skills ss    ON s.id = ss.student_id
            LEFT JOIN certifications cert  ON s.id = cert.student_id
            LEFT JOIN projects proj        ON s.id = proj.student_id
            WHERE s.id = %s
            GROUP BY s.id, ar.cgpa, ar.arrears
            """,
            (student_id,),
            fetch="one",
        )

        if not data:
            return None

        return predict_placement(
            cgpa=float(data["cgpa"] or 0),
            arrears=int(data["arrears"] or 0),
            skills_count=int(data["skills_count"] or 0),
            certifications_count=int(data["certifications_count"] or 0),
            projects_count=int(data["projects_count"] or 0),
        )

    except Exception as e:
        logger.error(f"get_student_prediction error: {e}")
        return None


# ─── Streamlit widget ─────────────────────────────────────────────────────────

def show_prediction_widget(student_id: int = None):
    """
    Interactive placement prediction widget for Streamlit.
    Can be used with a live student_id or with manual input.
    """
    try:
        import streamlit as st

        st.markdown("### 🤖 Placement Probability Prediction")

        if student_id:
            result = get_student_prediction(student_id)
            st.markdown("*Using your actual profile data for prediction.*")
        else:
            result = None

        with st.expander("⚙️ Adjust Parameters", expanded=(student_id is None)):
            col1, col2 = st.columns(2)
            with col1:
                cgpa     = st.slider("CGPA", 0.0, 10.0, 7.5, 0.1)
                arrears  = st.slider("Arrears", 0, 10, 0)
                coding   = st.slider("Coding Score", 0, 100, 65)
                aptitude = st.slider("Aptitude Score", 0, 100, 65)
            with col2:
                skills   = st.slider("Skills Count", 0, 20, 5)
                certs    = st.slider("Certifications", 0, 10, 1)
                projects = st.slider("Projects", 0, 10, 1)
                interview = st.slider("Interview Score", 0, 100, 60)

            if st.button("🔮 Predict Now"):
                result = predict_placement(
                    cgpa, arrears, coding, aptitude,
                    skills, certs, projects, interview,
                )

        if result:
            pred  = result["prediction"]
            conf  = result["confidence"]
            proba = result["probabilities"]

            color = {"HIGH": "#28a745", "MEDIUM": "#ffc107",
                     "LOW": "#dc3545"}.get(pred, "#666")
            st.markdown(
                f"<div style='background:{color}20; border:2px solid {color}; "
                f"border-radius:10px; padding:1rem; text-align:center;'>"
                f"<h2 style='color:{color}; margin:0;'>{pred} Probability</h2>"
                f"<p style='margin:0;'>Confidence: {conf*100:.1f}%</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**Probability Breakdown:**")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("HIGH",   f"{proba.get('HIGH',0)*100:.1f}%")
            col_b.metric("MEDIUM", f"{proba.get('MEDIUM',0)*100:.1f}%")
            col_c.metric("LOW",    f"{proba.get('LOW',0)*100:.1f}%")
        elif student_id:
            st.warning(
                "Prediction unavailable. "
                "Ensure scikit-learn is installed and your profile is complete."
            )

    except ImportError:
        pass  # streamlit not in scope during testing
