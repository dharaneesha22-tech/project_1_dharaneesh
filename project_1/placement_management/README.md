# 🎓 College Smart Placement Management System

A complete, production-ready **College Placement Management System** built with **Python + Streamlit + MySQL**.

---

## 📋 Project Overview

This system manages the end-to-end placement process for a college — from student registration and company drives to interview rounds, final results, analytics, and reports. Four roles (Admin, HOD, Faculty, Student) each have tailored dashboards with real-time MySQL-backed data.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 Role-based Auth | Admin, HOD, Faculty, Student with bcrypt hashing |
| 👤 Student Portal | Profile, skills, certifications, projects, placement history |
| 🏢 Company Management | Add/edit companies, drive scheduling |
| 📅 Placement Drives | Full drive lifecycle with eligibility filtering |
| 🎯 Interview Rounds | Track Aptitude → GD → Technical → HR → Final |
| ✅ HOD Verification | Verified placement results with audit trail |
| 📈 Analytics | 6+ Plotly charts with department/year/company filters |
| 📄 Resume Analyzer | PDF upload + skill extraction + job match % |
| 🤖 ML Prediction | RandomForest placement probability (HIGH/MEDIUM/LOW) |
| 🎯 Career Recommend | Skill-based career path suggestions with gap analysis |
| 📊 Reports | CSV + Excel export for students, departments, college |
| 🔔 Notifications | Drive announcements and result alerts |
| 📋 Audit Logs | Full audit trail for all critical operations |

---

## 🗂️ Project Structure

```
placement_management/
│
├── streamlit_app.py          # Main entry point
├── requirements.txt
├── .env.example
├── README.md
│
├── database/
│   ├── schema.sql            # Complete MySQL schema + views
│   └── seed_data.sql         # 105+ students, 12 companies, drives, results
│
├── modules/
│   ├── auth.py               # Login/logout UI
│   ├── student.py            # Student dashboard
│   ├── faculty.py            # Faculty dashboard
│   ├── hod.py                # HOD dashboard
│   ├── admin.py              # Admin dashboard
│   ├── companies.py          # Company management
│   ├── placements.py         # Drive management & applications
│   ├── analytics.py          # Plotly analytics charts
│   └── reports.py            # CSV/Excel export + resume analyzer
│
├── utils/
│   ├── database.py           # MySQL connection pool + query helpers
│   ├── security.py           # bcrypt + session + audit logging
│   └── validators.py         # Input validation helpers
│
└── ml/
    ├── placement_prediction.py   # RandomForest placement predictor
    └── career_recommendation.py  # Skill-based career recommender
```

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **Streamlit 1.35** — UI framework
- **MySQL 8.0** — Primary database
- **mysql-connector-python** — DB driver with connection pooling
- **Pandas** — Data manipulation
- **Plotly** — Interactive charts
- **Scikit-learn** — ML placement prediction
- **bcrypt** — Password hashing
- **python-dotenv** — Environment variable management
- **pdfplumber / PyPDF2** — Resume PDF parsing
- **openpyxl** — Excel export

---

## ⚙️ Installation

### 1. Clone / unzip the project

```bash
cd placement_management
```

### 2. Create virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. MySQL Setup

Start MySQL and create the database:

```sql
-- Option A: Run schema file
mysql -u root -p < database/schema.sql

-- Option B: Manual
CREATE DATABASE placement_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Load seed data:

```sql
mysql -u root -p placement_management < database/seed_data.sql
```

### 5. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=placement_management
DB_USER=root
DB_PASSWORD=your_actual_password
```

### 6. Run the Application

```bash
streamlit run streamlit_app.py
```

Open your browser at: **http://localhost:8501**

---

## 🔑 Sample Login Credentials

> ⚠️ Change all passwords after first login in production.

| Role | Username | Password |
|---|---|---|
| **Admin** | `admin` | `Admin@123` |
| **HOD (CSE)** | `hod_cse` | `Hod@123` |
| **HOD (IT)** | `hod_it` | `Hod@123` |
| **HOD (BCA)** | `hod_bca` | `Hod@123` |
| **HOD (BSCS)** | `hod_bscs` | `Hod@123` |
| **Faculty (CSE)** | `faculty_cse1` | `Faculty@123` |
| **Faculty (IT)** | `faculty_it1` | `Faculty@123` |
| **Student** | `CSE2021001` | `Student@123` |
| **Student** | `IT2021003` | `Student@123` |

---

## 🧩 Module Explanations

### `modules/auth.py`
Handles the login page UI, form submission, and session management. Calls `authenticate_user()` from `utils/security.py` which verifies bcrypt-hashed passwords.

### `modules/student.py`
Student dashboard with: home metrics, full profile (skills/certs/projects), available drives with eligibility check, placement history, resume analyzer, and AI insights.

### `modules/faculty.py`
Faculty can manage department students (add/edit), create drives, register students, update interview round results, and record final placement outcomes.

### `modules/hod.py`
HOD has read access to the entire department plus the ability to **verify** placement results. Includes company-wise report, analytics charts, and Excel export.

### `modules/admin.py`
Full college access: all students, all departments, user management (create/activate/deactivate), department management, analytics, reports, and audit log viewer.

### `modules/companies.py`
Add, edit, and view companies. Displays company-wise drive statistics.

### `modules/placements.py`
Core placement workflow: create drives, register students, update application status through all interview rounds, record final results, verify results.

### `modules/analytics.py`
Six Plotly charts: department placement bar, placed/not-placed pie, company selection, package distribution, year-wise trend, highest package by department. All with filters.

### `modules/reports.py`
Generate and export student, department, and college reports as CSV and Excel. Resume analyzer with PDF text extraction and skill matching.

### `utils/database.py`
MySQL connection pool (pool size 5), `execute_query()` for parameterized queries, `execute_transaction()` for multi-query transactions.

### `utils/security.py`
bcrypt password hashing, user authentication, session management, role checks, and audit logging.

---

## 🤖 ML Module Explanation

### `ml/placement_prediction.py`
- **Algorithm:** RandomForest Classifier
- **Features:** CGPA, Arrears, Coding Score, Aptitude Score, Skills Count, Certifications Count, Projects Count, Interview Score
- **Labels:** HIGH / MEDIUM / LOW
- **Training:** Uses DB data; falls back to synthetic data if DB has < 20 records
- **Graceful degradation:** Returns `None` if scikit-learn is not installed

### `ml/career_recommendation.py`
- **Algorithm:** Jaccard similarity against 10 predefined career profiles
- **Profiles:** Java Dev, Python Dev, Data Analyst, Data Scientist, ML Engineer, Backend Dev, Software Dev, Frontend Dev, DevOps, Business Analyst
- **Output:** Top-3 careers with matched skills, missing skills, and match %

---

## 🗄️ Database Design

### Key Tables
- `users` + `roles` — authentication and RBAC
- `students` + `academic_records` — student data with CGPA/arrears
- `student_skills`, `certifications`, `projects` — student profile
- `companies` — company master data
- `placement_drives` — drive configuration with eligibility rules
- `applications` — student-drive mapping with status tracking
- `interview_rounds` — per-round results
- `placement_results` — final verified outcomes
- `notifications` — student alerts
- `audit_logs` — complete operation audit trail

### Views
- `v_student_placement_summary` — per-student calculated statistics
- `v_department_stats` — per-department calculated statistics

All statistics (placement %, highest package, etc.) are **calculated dynamically** from these views — never stored manually.

---

## 🔒 Security

- Passwords hashed with **bcrypt** (12 rounds)
- All DB queries use **parameterized statements** (no SQL injection)
- Role-based access: each dashboard enforces role checks
- Students cannot modify **verified** placement results
- **Audit log** records all sensitive operations
- File uploads validated for type and size

---

## 🚀 Deployment

### Streamlit Community Cloud
1. Push to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, set main file to `streamlit_app.py`
4. Add environment variables in the Secrets section

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `Can't connect to MySQL` | Check `.env` credentials and ensure MySQL is running |
| `bcrypt` import error | Run `pip install bcrypt==4.1.3` |
| `pdfplumber` error | Run `pip install pdfplumber` |
| Blank login page | Check console for Python import errors |
| `Unknown role` after login | Ensure seed data was loaded correctly |
| ML prediction not showing | Run `pip install scikit-learn` |
| Excel export fails | Run `pip install openpyxl` |

---

## 📞 Support

Contact your placement coordinator or system administrator for login credentials and access issues.
