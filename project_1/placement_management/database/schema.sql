-- =============================================================
-- College Smart Placement Management System - Database Schema
-- MySQL 8.0+
-- =============================================================

CREATE DATABASE IF NOT EXISTS placement_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE placement_management;

-- -------------------------------------------------------------
-- ROLES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- DEPARTMENTS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    code       VARCHAR(20)  NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- USERS (all roles share one users table)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    full_name       VARCHAR(150) NOT NULL,
    role_id         INT          NOT NULL,
    department_id   INT,
    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id)       REFERENCES roles(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    INDEX idx_username   (username),
    INDEX idx_role       (role_id),
    INDEX idx_department (department_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- HOD  (one per department)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hod (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL UNIQUE,
    department_id INT NOT NULL UNIQUE,
    designation   VARCHAR(100) DEFAULT 'Head of Department',
    phone         VARCHAR(20),
    joined_date   DATE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- FACULTY
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faculty (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL UNIQUE,
    department_id INT NOT NULL,
    designation   VARCHAR(100) DEFAULT 'Assistant Professor',
    phone         VARCHAR(20),
    employee_id   VARCHAR(50) UNIQUE,
    joined_date   DATE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    INDEX idx_dept (department_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- STUDENTS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          UNIQUE,
    register_number VARCHAR(30)  NOT NULL UNIQUE,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    department_id   INT          NOT NULL,
    batch_year      YEAR         NOT NULL,
    current_year    TINYINT      DEFAULT 4,
    section         VARCHAR(10),
    gender          ENUM('Male','Female','Other'),
    date_of_birth   DATE,
    address         TEXT,
    photo_url       VARCHAR(500),
    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    INDEX idx_dept       (department_id),
    INDEX idx_batch      (batch_year),
    INDEX idx_reg_number (register_number)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- ACADEMIC RECORDS (CGPA + Arrears per semester)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS academic_records (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT          NOT NULL,
    cgpa       DECIMAL(4,2) NOT NULL DEFAULT 0.00,
    arrears    INT          NOT NULL DEFAULT 0,
    semester   TINYINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- SKILLS (master list)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    category   VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- STUDENT SKILLS (many-to-many)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS student_skills (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    skill_name  VARCHAR(100) NOT NULL,
    proficiency ENUM('Beginner','Intermediate','Advanced') DEFAULT 'Intermediate',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY uq_student_skill (student_id, skill_name),
    INDEX idx_student (student_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- CERTIFICATIONS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS certifications (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT          NOT NULL,
    title           VARCHAR(200) NOT NULL,
    issuing_org     VARCHAR(200),
    issue_date      DATE,
    expiry_date     DATE,
    credential_url  VARCHAR(500),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- PROJECTS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT          NOT NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT,
    tech_stack  VARCHAR(500),
    github_url  VARCHAR(500),
    demo_url    VARCHAR(500),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- COMPANIES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(200) NOT NULL,
    industry         VARCHAR(100),
    location         VARCHAR(200),
    website          VARCHAR(500),
    description      TEXT,
    contact_person   VARCHAR(150),
    contact_email    VARCHAR(150),
    contact_phone    VARCHAR(20),
    created_by       INT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_name (name)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- PLACEMENT DRIVES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_drives (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    company_id         INT          NOT NULL,
    job_role           VARCHAR(200) NOT NULL,
    drive_date         DATE         NOT NULL,
    registration_deadline DATE,
    min_cgpa           DECIMAL(4,2) DEFAULT 0.00,
    max_arrears        INT          DEFAULT 0,
    required_skills    TEXT,
    package_lpa        DECIMAL(6,2),
    package_details    VARCHAR(500),
    vacancies          INT          DEFAULT 0,
    job_description    TEXT,
    selection_process  TEXT,
    eligible_depts     TEXT,          -- comma-separated dept IDs
    venue              VARCHAR(300),
    status             ENUM('Upcoming','Active','Completed','Cancelled') DEFAULT 'Upcoming',
    created_by         INT,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id)  REFERENCES companies(id),
    FOREIGN KEY (created_by)  REFERENCES users(id),
    INDEX idx_company   (company_id),
    INDEX idx_drive_date (drive_date),
    INDEX idx_status    (status)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- APPLICATIONS (student registers for a drive)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    drive_id    INT NOT NULL,
    applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_eligible BOOLEAN  DEFAULT TRUE,
    status      ENUM(
                    'Registered',
                    'Attended',
                    'Shortlisted',
                    'Technical Round',
                    'HR Round',
                    'Selected',
                    'Rejected',
                    'Withdrawn'
                ) DEFAULT 'Registered',
    remarks     TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (drive_id)   REFERENCES placement_drives(id) ON DELETE CASCADE,
    UNIQUE KEY uq_student_drive (student_id, drive_id),
    INDEX idx_student (student_id),
    INDEX idx_drive   (drive_id),
    INDEX idx_status  (status)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- INTERVIEW ROUNDS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interview_rounds (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    round_name     ENUM(
                       'Aptitude',
                       'Group Discussion',
                       'Technical Interview',
                       'HR Interview',
                       'Final Selection'
                   ) NOT NULL,
    round_date     DATETIME,
    result         ENUM('Pending','Pass','Fail','Absent') DEFAULT 'Pending',
    score          DECIMAL(5,2),
    feedback       TEXT,
    conducted_by   INT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    FOREIGN KEY (conducted_by)   REFERENCES users(id),
    INDEX idx_application (application_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- PLACEMENT RESULTS (final verified outcome)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS placement_results (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT          NOT NULL,
    drive_id        INT          NOT NULL,
    application_id  INT          NOT NULL UNIQUE,
    status          ENUM('Selected','Rejected','On Hold') NOT NULL,
    package_lpa     DECIMAL(6,2),
    offer_letter_url VARCHAR(500),
    joining_date    DATE,
    is_verified     BOOLEAN DEFAULT FALSE,
    verified_by     INT,
    verified_at     DATETIME,
    remarks         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id)    REFERENCES students(id)           ON DELETE CASCADE,
    FOREIGN KEY (drive_id)      REFERENCES placement_drives(id),
    FOREIGN KEY (application_id) REFERENCES applications(id),
    FOREIGN KEY (verified_by)   REFERENCES users(id),
    UNIQUE KEY uq_student_drive (student_id, drive_id),
    INDEX idx_student  (student_id),
    INDEX idx_drive    (drive_id),
    INDEX idx_verified (is_verified)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- RESUMES
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resumes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    student_id     INT          NOT NULL,
    filename       VARCHAR(300) NOT NULL,
    file_data      LONGBLOB,
    uploaded_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    parsed_skills  TEXT,
    parsed_data    JSON,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- NOTIFICATIONS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    title       VARCHAR(200) NOT NULL,
    message     TEXT         NOT NULL,
    type        ENUM('Drive','Shortlist','Interview','Result','General') DEFAULT 'General',
    is_read     BOOLEAN      DEFAULT FALSE,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user   (user_id),
    INDEX idx_unread (user_id, is_read)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- AUDIT LOGS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT,
    action       VARCHAR(100) NOT NULL,
    target_table VARCHAR(100),
    target_id    INT,
    description  TEXT,
    ip_address   VARCHAR(45),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user      (user_id),
    INDEX idx_action    (action),
    INDEX idx_created   (created_at)
) ENGINE=InnoDB;

-- =============================================================
-- VIEWS for common queries
-- =============================================================

-- Student placement summary view
CREATE OR REPLACE VIEW v_student_placement_summary AS
SELECT
    s.id                                                    AS student_id,
    s.register_number,
    s.full_name,
    s.email,
    d.name                                                  AS department,
    d.id                                                    AS department_id,
    s.batch_year,
    COALESCE(ar.cgpa, 0)                                    AS cgpa,
    COALESCE(ar.arrears, 0)                                 AS arrears,
    COUNT(DISTINCT a.id)                                    AS companies_attended,
    COUNT(DISTINCT CASE WHEN pr.status='Selected'
                        THEN pr.id END)                     AS companies_selected,
    COUNT(DISTINCT CASE WHEN pr.status='Rejected'
                        THEN pr.id END)                     AS companies_rejected,
    MAX(CASE WHEN pr.status='Selected'
             THEN pr.package_lpa END)                       AS highest_package,
    CASE WHEN COUNT(DISTINCT CASE WHEN pr.status='Selected'
                                  THEN pr.id END) > 0
         THEN 'Placed'
         ELSE 'Not Placed' END                              AS placement_status
FROM students s
JOIN departments d  ON s.department_id = d.id
LEFT JOIN academic_records ar ON s.id = ar.student_id
LEFT JOIN applications a ON s.id = a.student_id
    AND a.status NOT IN ('Registered','Withdrawn')
LEFT JOIN placement_results pr ON s.id = pr.student_id
GROUP BY s.id, s.register_number, s.full_name, s.email,
         d.name, d.id, s.batch_year, ar.cgpa, ar.arrears;

-- Department placement statistics view
CREATE OR REPLACE VIEW v_department_stats AS
SELECT
    d.id                                                    AS department_id,
    d.name                                                  AS department,
    d.code,
    COUNT(DISTINCT s.id)                                    AS total_students,
    COUNT(DISTINCT CASE WHEN ps.placement_status='Placed'
                        THEN s.id END)                      AS placed_students,
    COUNT(DISTINCT CASE WHEN ps.placement_status='Not Placed'
                        THEN s.id END)                      AS not_placed_students,
    ROUND(
        COUNT(DISTINCT CASE WHEN ps.placement_status='Placed'
                            THEN s.id END) * 100.0 /
        NULLIF(COUNT(DISTINCT s.id), 0), 2
    )                                                       AS placement_percentage,
    MAX(ps.highest_package)                                 AS highest_package,
    ROUND(AVG(CASE WHEN ps.placement_status='Placed'
                   THEN ps.highest_package END), 2)         AS avg_package
FROM departments d
LEFT JOIN students s ON d.id = s.department_id AND s.is_active = TRUE
LEFT JOIN v_student_placement_summary ps ON s.id = ps.student_id
GROUP BY d.id, d.name, d.code;
