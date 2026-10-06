-- =============================================================
-- Seed Data for College Smart Placement Management System
-- Run AFTER schema.sql
-- =============================================================

USE placement_management;

-- -------------------------------------------------------------
-- ROLES
-- -------------------------------------------------------------
INSERT INTO roles (name, description) VALUES
('ADMIN',   'System Administrator - full access'),
('HOD',     'Head of Department - department access'),
('FACULTY', 'Faculty member - department access'),
('STUDENT', 'Student - personal access')
ON DUPLICATE KEY UPDATE description = VALUES(description);

-- -------------------------------------------------------------
-- DEPARTMENTS
-- -------------------------------------------------------------
INSERT INTO departments (name, code) VALUES
('Computer Science and Engineering', 'CSE'),
('Information Technology',           'IT'),
('Bachelor of Computer Applications','BCA'),
('B.Sc Computer Science',            'BSCS')
ON DUPLICATE KEY UPDATE code = VALUES(code);

-- -------------------------------------------------------------
-- USERS  (passwords: Admin@123, Hod@123, Faculty@123, Student@123)
-- bcrypt hashes pre-generated for these passwords
-- -------------------------------------------------------------
INSERT INTO users (username, password_hash, email, full_name, role_id, department_id, is_active) VALUES
-- ADMIN
('admin',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewOomJimhM.GCBKS',
 'admin@college.edu', 'System Administrator', 1, NULL, TRUE),

-- HODs
('hod_cse',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'hod.cse@college.edu', 'Dr. Rajesh Kumar', 2, 1, TRUE),
('hod_it',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'hod.it@college.edu', 'Dr. Priya Sharma', 2, 2, TRUE),
('hod_bca',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'hod.bca@college.edu', 'Dr. Suresh Babu', 2, 3, TRUE),
('hod_bscs',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'hod.bscs@college.edu', 'Dr. Kavitha Nair', 2, 4, TRUE),

-- FACULTY
('faculty_cse1',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'faculty.cse1@college.edu', 'Prof. Anand Raj', 3, 1, TRUE),
('faculty_cse2',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'faculty.cse2@college.edu', 'Prof. Meena Devi', 3, 1, TRUE),
('faculty_it1',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'faculty.it1@college.edu', 'Prof. Ravi Shankar', 3, 2, TRUE),
('faculty_bca1',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'faculty.bca1@college.edu', 'Prof. Deepa Krishnan', 3, 3, TRUE),

-- STUDENTS (sample; bulk inserted below)
('CSE2021001',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'student001@college.edu', 'Arjun Menon', 4, 1, TRUE),
('CSE2021002',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uDonDWqkVG',
 'student002@college.edu', 'Divya Patel', 4, 1, TRUE)
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- -------------------------------------------------------------
-- HOD RECORDS
-- -------------------------------------------------------------
INSERT INTO hod (user_id, department_id, phone) VALUES
((SELECT id FROM users WHERE username='hod_cse'),  1, '9876543210'),
((SELECT id FROM users WHERE username='hod_it'),   2, '9876543211'),
((SELECT id FROM users WHERE username='hod_bca'),  3, '9876543212'),
((SELECT id FROM users WHERE username='hod_bscs'), 4, '9876543213')
ON DUPLICATE KEY UPDATE phone = VALUES(phone);

-- -------------------------------------------------------------
-- FACULTY RECORDS
-- -------------------------------------------------------------
INSERT INTO faculty (user_id, department_id, employee_id, phone) VALUES
((SELECT id FROM users WHERE username='faculty_cse1'), 1, 'EMP001', '9876540001'),
((SELECT id FROM users WHERE username='faculty_cse2'), 1, 'EMP002', '9876540002'),
((SELECT id FROM users WHERE username='faculty_it1'),  2, 'EMP003', '9876540003'),
((SELECT id FROM users WHERE username='faculty_bca1'), 3, 'EMP004', '9876540004')
ON DUPLICATE KEY UPDATE employee_id = VALUES(employee_id);

-- -------------------------------------------------------------
-- STUDENTS (100+ records across 4 departments)
-- -------------------------------------------------------------
INSERT INTO students
    (register_number, full_name, email, phone, department_id,
     batch_year, current_year, section, gender)
VALUES
-- CSE batch (30 students)
('CSE2021001','Arjun Menon','arjun.menon@college.edu','9876501001',1,2021,4,'A','Male'),
('CSE2021002','Divya Patel','divya.patel@college.edu','9876501002',1,2021,4,'A','Female'),
('CSE2021003','Karthik Ram','karthik.ram@college.edu','9876501003',1,2021,4,'A','Male'),
('CSE2021004','Sneha Iyer','sneha.iyer@college.edu','9876501004',1,2021,4,'B','Female'),
('CSE2021005','Rahul Nair','rahul.nair@college.edu','9876501005',1,2021,4,'B','Male'),
('CSE2021006','Pooja Singh','pooja.singh@college.edu','9876501006',1,2021,4,'A','Female'),
('CSE2021007','Vikram Bose','vikram.bose@college.edu','9876501007',1,2021,4,'B','Male'),
('CSE2021008','Ananya Roy','ananya.roy@college.edu','9876501008',1,2021,4,'A','Female'),
('CSE2021009','Sanjay Kumar','sanjay.kumar@college.edu','9876501009',1,2021,4,'B','Male'),
('CSE2021010','Priya Chakra','priya.chakra@college.edu','9876501010',1,2021,4,'A','Female'),
('CSE2021011','Ajay Mishra','ajay.mishra@college.edu','9876501011',1,2021,4,'A','Male'),
('CSE2021012','Rekha Pillai','rekha.pillai@college.edu','9876501012',1,2021,4,'B','Female'),
('CSE2021013','Nikhil Joshi','nikhil.joshi@college.edu','9876501013',1,2021,4,'A','Male'),
('CSE2021014','Swati Verma','swati.verma@college.edu','9876501014',1,2021,4,'B','Female'),
('CSE2021015','Deepak Nath','deepak.nath@college.edu','9876501015',1,2021,4,'A','Male'),
('CSE2021016','Kavya Rao','kavya.rao@college.edu','9876501016',1,2021,4,'B','Female'),
('CSE2021017','Rohit Sharma','rohit.sharma@college.edu','9876501017',1,2021,4,'A','Male'),
('CSE2021018','Neha Gupta','neha.gupta@college.edu','9876501018',1,2021,4,'B','Female'),
('CSE2021019','Arun Balan','arun.balan@college.edu','9876501019',1,2021,4,'A','Male'),
('CSE2021020','Lakshmi Nair','lakshmi.nair@college.edu','9876501020',1,2021,4,'B','Female'),
('CSE2021021','Varun Das','varun.das@college.edu','9876501021',1,2021,4,'A','Male'),
('CSE2021022','Shreya Sen','shreya.sen@college.edu','9876501022',1,2021,4,'B','Female'),
('CSE2021023','Vivek Mathew','vivek.mathew@college.edu','9876501023',1,2021,4,'A','Male'),
('CSE2021024','Asha Thomas','asha.thomas@college.edu','9876501024',1,2021,4,'B','Female'),
('CSE2021025','Gopal Reddy','gopal.reddy@college.edu','9876501025',1,2021,4,'A','Male'),
('CSE2021026','Meghna Jain','meghna.jain@college.edu','9876501026',1,2021,4,'B','Female'),
('CSE2021027','Sandeep Paul','sandeep.paul@college.edu','9876501027',1,2021,4,'A','Male'),
('CSE2021028','Preethi Raj','preethi.raj@college.edu','9876501028',1,2021,4,'B','Female'),
('CSE2021029','Harish Babu','harish.babu@college.edu','9876501029',1,2021,4,'A','Male'),
('CSE2021030','Nithya Devi','nithya.devi@college.edu','9876501030',1,2021,4,'B','Female'),

-- IT batch (25 students)
('IT2021001','Aishwarya KN','aishwarya.kn@college.edu','9876502001',2,2021,4,'A','Female'),
('IT2021002','Balaji SK','balaji.sk@college.edu','9876502002',2,2021,4,'A','Male'),
('IT2021003','Chitra MV','chitra.mv@college.edu','9876502003',2,2021,4,'B','Female'),
('IT2021004','Dinesh TR','dinesh.tr@college.edu','9876502004',2,2021,4,'A','Male'),
('IT2021005','Eswari PL','eswari.pl@college.edu','9876502005',2,2021,4,'B','Female'),
('IT2021006','Faisal AR','faisal.ar@college.edu','9876502006',2,2021,4,'A','Male'),
('IT2021007','Geetha SN','geetha.sn@college.edu','9876502007',2,2021,4,'B','Female'),
('IT2021008','Hari PK','hari.pk@college.edu','9876502008',2,2021,4,'A','Male'),
('IT2021009','Indira KR','indira.kr@college.edu','9876502009',2,2021,4,'B','Female'),
('IT2021010','Jagan RA','jagan.ra@college.edu','9876502010',2,2021,4,'A','Male'),
('IT2021011','Kamala DS','kamala.ds@college.edu','9876502011',2,2021,4,'B','Female'),
('IT2021012','Lokesh MP','lokesh.mp@college.edu','9876502012',2,2021,4,'A','Male'),
('IT2021013','Malathi RK','malathi.rk@college.edu','9876502013',2,2021,4,'B','Female'),
('IT2021014','Naveen CM','naveen.cm@college.edu','9876502014',2,2021,4,'A','Male'),
('IT2021015','Oviya TN','oviya.tn@college.edu','9876502015',2,2021,4,'B','Female'),
('IT2021016','Pradeep KS','pradeep.ks@college.edu','9876502016',2,2021,4,'A','Male'),
('IT2021017','Queen MJ','queen.mj@college.edu','9876502017',2,2021,4,'B','Female'),
('IT2021018','Rajesh VN','rajesh.vn@college.edu','9876502018',2,2021,4,'A','Male'),
('IT2021019','Sangeetha AR','sangeetha.ar@college.edu','9876502019',2,2021,4,'B','Female'),
('IT2021020','Tamil SM','tamil.sm@college.edu','9876502020',2,2021,4,'A','Male'),
('IT2021021','Uma KP','uma.kp@college.edu','9876502021',2,2021,4,'B','Female'),
('IT2021022','Vasanth LR','vasanth.lr@college.edu','9876502022',2,2021,4,'A','Male'),
('IT2021023','Wendy JA','wendy.ja@college.edu','9876502023',2,2021,4,'B','Female'),
('IT2021024','Xavier PN','xavier.pn@college.edu','9876502024',2,2021,4,'A','Male'),
('IT2021025','Yamini SK','yamini.sk@college.edu','9876502025',2,2021,4,'B','Female'),

-- BCA batch (25 students)
('BCA2021001','Abhinav MR','abhinav.mr@college.edu','9876503001',3,2021,4,'A','Male'),
('BCA2021002','Bhavana KS','bhavana.ks@college.edu','9876503002',3,2021,4,'A','Female'),
('BCA2021003','Chandru RN','chandru.rn@college.edu','9876503003',3,2021,4,'B','Male'),
('BCA2021004','Dharshini PM','dharshini.pm@college.edu','9876503004',3,2021,4,'A','Female'),
('BCA2021005','Elan TK','elan.tk@college.edu','9876503005',3,2021,4,'B','Male'),
('BCA2021006','Fathima SR','fathima.sr@college.edu','9876503006',3,2021,4,'A','Female'),
('BCA2021007','Gautham NL','gautham.nl@college.edu','9876503007',3,2021,4,'B','Male'),
('BCA2021008','Hemalatha VS','hemalatha.vs@college.edu','9876503008',3,2021,4,'A','Female'),
('BCA2021009','Ilavarasan KM','ilavarasan.km@college.edu','9876503009',3,2021,4,'B','Male'),
('BCA2021010','Janani PR','janani.pr@college.edu','9876503010',3,2021,4,'A','Female'),
('BCA2021011','Kiran DS','kiran.ds@college.edu','9876503011',3,2021,4,'B','Male'),
('BCA2021012','Lalitha MN','lalitha.mn@college.edu','9876503012',3,2021,4,'A','Female'),
('BCA2021013','Madan KR','madan.kr@college.edu','9876503013',3,2021,4,'B','Male'),
('BCA2021014','Nandhini TL','nandhini.tl@college.edu','9876503014',3,2021,4,'A','Female'),
('BCA2021015','Ovath PJ','ovath.pj@college.edu','9876503015',3,2021,4,'B','Male'),
('BCA2021016','Pavithra SM','pavithra.sm@college.edu','9876503016',3,2021,4,'A','Female'),
('BCA2021017','Qadeer RN','qadeer.rn@college.edu','9876503017',3,2021,4,'B','Male'),
('BCA2021018','Ranjitha KP','ranjitha.kp@college.edu','9876503018',3,2021,4,'A','Female'),
('BCA2021019','Senthil VK','senthil.vk@college.edu','9876503019',3,2021,4,'B','Male'),
('BCA2021020','Thenmozhi AL','thenmozhi.al@college.edu','9876503020',3,2021,4,'A','Female'),
('BCA2021021','Udhaya MK','udhaya.mk@college.edu','9876503021',3,2021,4,'B','Male'),
('BCA2021022','Varsha NT','varsha.nt@college.edu','9876503022',3,2021,4,'A','Female'),
('BCA2021023','William SJ','william.sj@college.edu','9876503023',3,2021,4,'B','Male'),
('BCA2021024','Xena PR','xena.pr@college.edu','9876503024',3,2021,4,'A','Female'),
('BCA2021025','Yohannes KL','yohannes.kl@college.edu','9876503025',3,2021,4,'B','Male'),

-- BSCS batch (25 students)
('BSCS2021001','Aakash MN','aakash.mn@college.edu','9876504001',4,2021,4,'A','Male'),
('BSCS2021002','Bindhu KR','bindhu.kr@college.edu','9876504002',4,2021,4,'A','Female'),
('BSCS2021003','Clement VS','clement.vs@college.edu','9876504003',4,2021,4,'B','Male'),
('BSCS2021004','Devi PT','devi.pt@college.edu','9876504004',4,2021,4,'A','Female'),
('BSCS2021005','Edwin KL','edwin.kl@college.edu','9876504005',4,2021,4,'B','Male'),
('BSCS2021006','Flora MR','flora.mr@college.edu','9876504006',4,2021,4,'A','Female'),
('BSCS2021007','Ganesh NP','ganesh.np@college.edu','9876504007',4,2021,4,'B','Male'),
('BSCS2021008','Hemavathi KS','hemavathi.ks@college.edu','9876504008',4,2021,4,'A','Female'),
('BSCS2021009','Imran TK','imran.tk@college.edu','9876504009',4,2021,4,'B','Male'),
('BSCS2021010','Jeya PR','jeya.pr@college.edu','9876504010',4,2021,4,'A','Female'),
('BSCS2021011','Kannan LS','kannan.ls@college.edu','9876504011',4,2021,4,'B','Male'),
('BSCS2021012','Lavanya MK','lavanya.mk@college.edu','9876504012',4,2021,4,'A','Female'),
('BSCS2021013','Madhan VR','madhan.vr@college.edu','9876504013',4,2021,4,'B','Male'),
('BSCS2021014','Nandhitha SP','nandhitha.sp@college.edu','9876504014',4,2021,4,'A','Female'),
('BSCS2021015','Omar KN','omar.kn@college.edu','9876504015',4,2021,4,'B','Male'),
('BSCS2021016','Parvathy LM','parvathy.lm@college.edu','9876504016',4,2021,4,'A','Female'),
('BSCS2021017','Rajkumar TR','rajkumar.tr@college.edu','9876504017',4,2021,4,'B','Male'),
('BSCS2021018','Selvi NK','selvi.nk@college.edu','9876504018',4,2021,4,'A','Female'),
('BSCS2021019','Thilak PS','thilak.ps@college.edu','9876504019',4,2021,4,'B','Male'),
('BSCS2021020','Usha MV','usha.mv@college.edu','9876504020',4,2021,4,'A','Female'),
('BSCS2021021','Vimal KT','vimal.kt@college.edu','9876504021',4,2021,4,'B','Male'),
('BSCS2021022','Winitha RS','winitha.rs@college.edu','9876504022',4,2021,4,'A','Female'),
('BSCS2021023','Xaviour PM','xaviour.pm@college.edu','9876504023',4,2021,4,'B','Male'),
('BSCS2021024','Yamuna KL','yamuna.kl@college.edu','9876504024',4,2021,4,'A','Female'),
('BSCS2021025','Zoya AR','zoya.ar@college.edu','9876504025',4,2021,4,'B','Female')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);

-- -------------------------------------------------------------
-- ACADEMIC RECORDS
-- -------------------------------------------------------------
INSERT INTO academic_records (student_id, cgpa, arrears) VALUES
-- CSE students
((SELECT id FROM students WHERE register_number='CSE2021001'), 8.9, 0),
((SELECT id FROM students WHERE register_number='CSE2021002'), 9.2, 0),
((SELECT id FROM students WHERE register_number='CSE2021003'), 7.8, 1),
((SELECT id FROM students WHERE register_number='CSE2021004'), 8.5, 0),
((SELECT id FROM students WHERE register_number='CSE2021005'), 7.2, 2),
((SELECT id FROM students WHERE register_number='CSE2021006'), 9.0, 0),
((SELECT id FROM students WHERE register_number='CSE2021007'), 6.8, 3),
((SELECT id FROM students WHERE register_number='CSE2021008'), 8.7, 0),
((SELECT id FROM students WHERE register_number='CSE2021009'), 7.5, 1),
((SELECT id FROM students WHERE register_number='CSE2021010'), 9.1, 0),
((SELECT id FROM students WHERE register_number='CSE2021011'), 7.0, 2),
((SELECT id FROM students WHERE register_number='CSE2021012'), 8.3, 0),
((SELECT id FROM students WHERE register_number='CSE2021013'), 8.8, 0),
((SELECT id FROM students WHERE register_number='CSE2021014'), 7.6, 1),
((SELECT id FROM students WHERE register_number='CSE2021015'), 9.3, 0),
((SELECT id FROM students WHERE register_number='CSE2021016'), 8.1, 0),
((SELECT id FROM students WHERE register_number='CSE2021017'), 7.4, 1),
((SELECT id FROM students WHERE register_number='CSE2021018'), 8.6, 0),
((SELECT id FROM students WHERE register_number='CSE2021019'), 7.9, 0),
((SELECT id FROM students WHERE register_number='CSE2021020'), 9.4, 0),
((SELECT id FROM students WHERE register_number='CSE2021021'), 6.5, 4),
((SELECT id FROM students WHERE register_number='CSE2021022'), 8.2, 0),
((SELECT id FROM students WHERE register_number='CSE2021023'), 7.7, 1),
((SELECT id FROM students WHERE register_number='CSE2021024'), 8.9, 0),
((SELECT id FROM students WHERE register_number='CSE2021025'), 8.0, 0),
((SELECT id FROM students WHERE register_number='CSE2021026'), 7.3, 2),
((SELECT id FROM students WHERE register_number='CSE2021027'), 9.0, 0),
((SELECT id FROM students WHERE register_number='CSE2021028'), 8.4, 0),
((SELECT id FROM students WHERE register_number='CSE2021029'), 7.1, 3),
((SELECT id FROM students WHERE register_number='CSE2021030'), 8.8, 0),
-- IT students
((SELECT id FROM students WHERE register_number='IT2021001'), 8.7, 0),
((SELECT id FROM students WHERE register_number='IT2021002'), 7.5, 1),
((SELECT id FROM students WHERE register_number='IT2021003'), 9.0, 0),
((SELECT id FROM students WHERE register_number='IT2021004'), 8.2, 0),
((SELECT id FROM students WHERE register_number='IT2021005'), 7.8, 0),
((SELECT id FROM students WHERE register_number='IT2021006'), 8.5, 0),
((SELECT id FROM students WHERE register_number='IT2021007'), 7.0, 2),
((SELECT id FROM students WHERE register_number='IT2021008'), 9.1, 0),
((SELECT id FROM students WHERE register_number='IT2021009'), 8.3, 0),
((SELECT id FROM students WHERE register_number='IT2021010'), 7.6, 1),
((SELECT id FROM students WHERE register_number='IT2021011'), 8.8, 0),
((SELECT id FROM students WHERE register_number='IT2021012'), 7.2, 1),
((SELECT id FROM students WHERE register_number='IT2021013'), 8.9, 0),
((SELECT id FROM students WHERE register_number='IT2021014'), 7.4, 0),
((SELECT id FROM students WHERE register_number='IT2021015'), 9.2, 0),
((SELECT id FROM students WHERE register_number='IT2021016'), 8.0, 0),
((SELECT id FROM students WHERE register_number='IT2021017'), 7.7, 1),
((SELECT id FROM students WHERE register_number='IT2021018'), 8.4, 0),
((SELECT id FROM students WHERE register_number='IT2021019'), 6.9, 3),
((SELECT id FROM students WHERE register_number='IT2021020'), 8.6, 0),
((SELECT id FROM students WHERE register_number='IT2021021'), 7.3, 1),
((SELECT id FROM students WHERE register_number='IT2021022'), 9.0, 0),
((SELECT id FROM students WHERE register_number='IT2021023'), 8.1, 0),
((SELECT id FROM students WHERE register_number='IT2021024'), 7.9, 0),
((SELECT id FROM students WHERE register_number='IT2021025'), 8.5, 0),
-- BCA students
((SELECT id FROM students WHERE register_number='BCA2021001'), 8.1, 0),
((SELECT id FROM students WHERE register_number='BCA2021002'), 7.6, 1),
((SELECT id FROM students WHERE register_number='BCA2021003'), 8.4, 0),
((SELECT id FROM students WHERE register_number='BCA2021004'), 9.0, 0),
((SELECT id FROM students WHERE register_number='BCA2021005'), 7.2, 2),
((SELECT id FROM students WHERE register_number='BCA2021006'), 8.7, 0),
((SELECT id FROM students WHERE register_number='BCA2021007'), 7.5, 1),
((SELECT id FROM students WHERE register_number='BCA2021008'), 8.9, 0),
((SELECT id FROM students WHERE register_number='BCA2021009'), 7.0, 0),
((SELECT id FROM students WHERE register_number='BCA2021010'), 8.3, 0),
((SELECT id FROM students WHERE register_number='BCA2021011'), 7.8, 1),
((SELECT id FROM students WHERE register_number='BCA2021012'), 8.5, 0),
((SELECT id FROM students WHERE register_number='BCA2021013'), 6.8, 3),
((SELECT id FROM students WHERE register_number='BCA2021014'), 8.2, 0),
((SELECT id FROM students WHERE register_number='BCA2021015'), 7.4, 0),
((SELECT id FROM students WHERE register_number='BCA2021016'), 8.8, 0),
((SELECT id FROM students WHERE register_number='BCA2021017'), 7.1, 2),
((SELECT id FROM students WHERE register_number='BCA2021018'), 9.1, 0),
((SELECT id FROM students WHERE register_number='BCA2021019'), 7.9, 0),
((SELECT id FROM students WHERE register_number='BCA2021020'), 8.0, 1),
((SELECT id FROM students WHERE register_number='BCA2021021'), 7.3, 1),
((SELECT id FROM students WHERE register_number='BCA2021022'), 8.6, 0),
((SELECT id FROM students WHERE register_number='BCA2021023'), 7.7, 0),
((SELECT id FROM students WHERE register_number='BCA2021024'), 8.4, 0),
((SELECT id FROM students WHERE register_number='BCA2021025'), 6.5, 4),
-- BSCS students
((SELECT id FROM students WHERE register_number='BSCS2021001'), 8.5, 0),
((SELECT id FROM students WHERE register_number='BSCS2021002'), 7.8, 1),
((SELECT id FROM students WHERE register_number='BSCS2021003'), 8.2, 0),
((SELECT id FROM students WHERE register_number='BSCS2021004'), 9.0, 0),
((SELECT id FROM students WHERE register_number='BSCS2021005'), 7.0, 2),
((SELECT id FROM students WHERE register_number='BSCS2021006'), 8.7, 0),
((SELECT id FROM students WHERE register_number='BSCS2021007'), 7.5, 1),
((SELECT id FROM students WHERE register_number='BSCS2021008'), 8.9, 0),
((SELECT id FROM students WHERE register_number='BSCS2021009'), 7.3, 0),
((SELECT id FROM students WHERE register_number='BSCS2021010'), 8.1, 0),
((SELECT id FROM students WHERE register_number='BSCS2021011'), 7.6, 1),
((SELECT id FROM students WHERE register_number='BSCS2021012'), 8.4, 0),
((SELECT id FROM students WHERE register_number='BSCS2021013'), 7.2, 2),
((SELECT id FROM students WHERE register_number='BSCS2021014'), 8.8, 0),
((SELECT id FROM students WHERE register_number='BSCS2021015'), 6.9, 3),
((SELECT id FROM students WHERE register_number='BSCS2021016'), 9.2, 0),
((SELECT id FROM students WHERE register_number='BSCS2021017'), 7.7, 0),
((SELECT id FROM students WHERE register_number='BSCS2021018'), 8.3, 0),
((SELECT id FROM students WHERE register_number='BSCS2021019'), 7.4, 1),
((SELECT id FROM students WHERE register_number='BSCS2021020'), 8.6, 0),
((SELECT id FROM students WHERE register_number='BSCS2021021'), 7.1, 1),
((SELECT id FROM students WHERE register_number='BSCS2021022'), 8.0, 0),
((SELECT id FROM students WHERE register_number='BSCS2021023'), 7.9, 0),
((SELECT id FROM students WHERE register_number='BSCS2021024'), 8.5, 0),
((SELECT id FROM students WHERE register_number='BSCS2021025'), 6.7, 2)
ON DUPLICATE KEY UPDATE cgpa=VALUES(cgpa), arrears=VALUES(arrears);

-- -------------------------------------------------------------
-- STUDENT SKILLS (sample)
-- -------------------------------------------------------------
INSERT INTO student_skills (student_id, skill_name, proficiency)
SELECT s.id, 'Python', 'Advanced'
FROM students s WHERE s.register_number IN
  ('CSE2021001','CSE2021002','CSE2021010','CSE2021015','IT2021003','IT2021008','BCA2021004','BSCS2021004')
ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency);

INSERT INTO student_skills (student_id, skill_name, proficiency)
SELECT s.id, 'Java', 'Intermediate'
FROM students s WHERE s.register_number IN
  ('CSE2021001','CSE2021003','CSE2021006','IT2021001','IT2021006','BCA2021001','BSCS2021001','BSCS2021016')
ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency);

INSERT INTO student_skills (student_id, skill_name, proficiency)
SELECT s.id, 'SQL', 'Advanced'
FROM students s WHERE s.register_number IN
  ('CSE2021002','CSE2021004','CSE2021008','IT2021003','IT2021011','BCA2021004','BCA2021008','BSCS2021004')
ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency);

INSERT INTO student_skills (student_id, skill_name, proficiency)
SELECT s.id, 'Machine Learning', 'Intermediate'
FROM students s WHERE s.register_number IN
  ('CSE2021002','CSE2021010','CSE2021015','IT2021003','IT2021015')
ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency);

INSERT INTO student_skills (student_id, skill_name, proficiency)
SELECT s.id, 'React', 'Intermediate'
FROM students s WHERE s.register_number IN
  ('CSE2021006','CSE2021008','IT2021006','IT2021011','BCA2021006','BCA2021010','BSCS2021008')
ON DUPLICATE KEY UPDATE proficiency=VALUES(proficiency);

-- -------------------------------------------------------------
-- CERTIFICATIONS (sample)
-- -------------------------------------------------------------
INSERT INTO certifications (student_id, title, issuing_org, issue_date) VALUES
((SELECT id FROM students WHERE register_number='CSE2021001'), 'AWS Cloud Practitioner', 'Amazon Web Services', '2023-06-15'),
((SELECT id FROM students WHERE register_number='CSE2021002'), 'Google Data Analytics', 'Google', '2023-08-20'),
((SELECT id FROM students WHERE register_number='CSE2021010'), 'Python for Data Science', 'IBM', '2023-05-10'),
((SELECT id FROM students WHERE register_number='IT2021003'), 'Oracle Java SE', 'Oracle', '2023-07-12'),
((SELECT id FROM students WHERE register_number='IT2021008'), 'Azure Fundamentals', 'Microsoft', '2023-09-01'),
((SELECT id FROM students WHERE register_number='BCA2021004'), 'Salesforce Admin', 'Salesforce', '2023-04-25')
ON DUPLICATE KEY UPDATE title=VALUES(title);

-- -------------------------------------------------------------
-- COMPANIES
-- -------------------------------------------------------------
INSERT INTO companies (name, industry, location, contact_email) VALUES
('Tata Consultancy Services', 'IT Services',    'Chennai',   'placement@tcs.com'),
('Infosys',                   'IT Services',    'Bangalore', 'campus@infosys.com'),
('Wipro',                     'IT Services',    'Bangalore', 'campus@wipro.com'),
('HCL Technologies',          'IT Services',    'Noida',     'campus@hcl.com'),
('Cognizant',                 'IT Services',    'Chennai',   'campus@cognizant.com'),
('Zoho Corporation',          'Software',       'Chennai',   'hr@zoho.com'),
('Freshworks',                'SaaS',           'Chennai',   'hr@freshworks.com'),
('Sutherland Global',         'BPO/IT',         'Chennai',   'hr@sutherland.com'),
('Capgemini',                 'IT Consulting',  'Mumbai',    'campus@capgemini.com'),
('Accenture',                 'Consulting',     'Bangalore', 'campus@accenture.com'),
('Hexaware Technologies',     'IT Services',    'Chennai',   'hr@hexaware.com'),
('Mphasis',                   'IT Services',    'Bangalore', 'hr@mphasis.com')
ON DUPLICATE KEY UPDATE industry=VALUES(industry);

-- -------------------------------------------------------------
-- PLACEMENT DRIVES
-- -------------------------------------------------------------
INSERT INTO placement_drives
    (company_id, job_role, drive_date, min_cgpa, max_arrears,
     required_skills, package_lpa, vacancies, eligible_depts, status)
VALUES
((SELECT id FROM companies WHERE name='Tata Consultancy Services'),
 'Software Engineer', '2024-02-15', 6.0, 2,
 'Python,Java,SQL', 3.5, 50, '1,2,3,4', 'Completed'),

((SELECT id FROM companies WHERE name='Infosys'),
 'Systems Engineer', '2024-02-28', 6.5, 1,
 'Java,Python,SQL', 3.6, 40, '1,2,3,4', 'Completed'),

((SELECT id FROM companies WHERE name='Wipro'),
 'Project Engineer', '2024-03-10', 6.0, 2,
 'Python,SQL,Communication', 3.5, 35, '1,2,3,4', 'Completed'),

((SELECT id FROM companies WHERE name='HCL Technologies'),
 'Graduate Engineer Trainee', '2024-03-20', 6.5, 1,
 'C,Java,DBMS', 3.8, 30, '1,2', 'Completed'),

((SELECT id FROM companies WHERE name='Cognizant'),
 'Programmer Analyst', '2024-04-05', 7.0, 0,
 'Python,Machine Learning,SQL', 4.0, 25, '1,2', 'Completed'),

((SELECT id FROM companies WHERE name='Zoho Corporation'),
 'Software Developer', '2024-04-20', 8.0, 0,
 'Python,Java,SQL,Data Structures', 6.0, 20, '1,2', 'Completed'),

((SELECT id FROM companies WHERE name='Freshworks'),
 'Software Development Engineer', '2024-05-10', 7.5, 0,
 'Python,React,SQL', 7.0, 15, '1,2', 'Completed'),

((SELECT id FROM companies WHERE name='Capgemini'),
 'Analyst', '2024-05-25', 6.0, 2,
 'Python,SQL,Agile', 4.5, 40, '1,2,3,4', 'Completed'),

((SELECT id FROM companies WHERE name='Accenture'),
 'Associate Software Engineer', '2024-06-10', 6.5, 1,
 'Java,Python,Communication', 4.5, 45, '1,2,3,4', 'Completed'),

((SELECT id FROM companies WHERE name='Sutherland Global'),
 'Software Engineer', '2024-06-25', 6.0, 3,
 'Python,SQL', 3.2, 60, '1,2,3,4', 'Completed'),

((SELECT id FROM companies WHERE name='Hexaware Technologies'),
 'Graduate Trainee', '2026-11-15', 6.5, 2,
 'Java,SQL,Testing', 4.2, 30, '1,2,3,4', 'Upcoming'),

((SELECT id FROM companies WHERE name='Mphasis'),
 'Associate Engineer', '2026-12-05', 7.0, 1,
 'Python,Java,SQL', 5.0, 25, '1,2', 'Upcoming')
ON DUPLICATE KEY UPDATE job_role=VALUES(job_role);

-- -------------------------------------------------------
-- APPLICATIONS & PLACEMENT RESULTS (sample data for TCS drive)
-- -------------------------------------------------------
-- Register all CSE + IT students for TCS drive
INSERT IGNORE INTO applications (student_id, drive_id, status)
SELECT s.id,
       (SELECT id FROM placement_drives WHERE job_role='Software Engineer'
        AND company_id=(SELECT id FROM companies WHERE name='Tata Consultancy Services')
        LIMIT 1),
       CASE
         WHEN ar.cgpa >= 8.5 AND ar.arrears = 0 THEN 'Selected'
         WHEN ar.cgpa >= 7.5 AND ar.arrears <= 1 THEN 'Rejected'
         WHEN ar.cgpa >= 6.5 AND ar.arrears <= 2 THEN 'Attended'
         ELSE 'Registered'
       END
FROM students s
JOIN academic_records ar ON s.id = ar.student_id
WHERE s.department_id IN (1,2,3,4);

-- Placement results for selected students in TCS
INSERT IGNORE INTO placement_results
    (student_id, drive_id, application_id, status, package_lpa, is_verified, verified_at)
SELECT
    a.student_id,
    a.drive_id,
    a.id,
    'Selected',
    3.5,
    TRUE,
    NOW()
FROM applications a
WHERE a.drive_id = (
    SELECT id FROM placement_drives
    WHERE job_role='Software Engineer'
    AND company_id=(SELECT id FROM companies WHERE name='Tata Consultancy Services')
    LIMIT 1)
  AND a.status = 'Selected';

-- Register eligible CSE + IT for Zoho drive and mark selections
INSERT IGNORE INTO applications (student_id, drive_id, status)
SELECT s.id,
       (SELECT id FROM placement_drives WHERE job_role='Software Developer'
        AND company_id=(SELECT id FROM companies WHERE name='Zoho Corporation')
        LIMIT 1),
       CASE
         WHEN ar.cgpa >= 9.0 THEN 'Selected'
         WHEN ar.cgpa >= 8.0 THEN 'Rejected'
         ELSE 'Registered'
       END
FROM students s
JOIN academic_records ar ON s.id = ar.student_id
WHERE s.department_id IN (1,2) AND ar.cgpa >= 8.0 AND ar.arrears = 0;

INSERT IGNORE INTO placement_results
    (student_id, drive_id, application_id, status, package_lpa, is_verified, verified_at)
SELECT
    a.student_id,
    a.drive_id,
    a.id,
    'Selected',
    6.0,
    TRUE,
    NOW()
FROM applications a
WHERE a.drive_id = (
    SELECT id FROM placement_drives
    WHERE job_role='Software Developer'
    AND company_id=(SELECT id FROM companies WHERE name='Zoho Corporation')
    LIMIT 1)
  AND a.status = 'Selected';

-- Sample notifications
INSERT INTO notifications (user_id, title, message, type) VALUES
((SELECT id FROM users WHERE username='CSE2021001'),
 'New Drive: Hexaware Technologies',
 'A new placement drive has been scheduled for Hexaware Technologies on 15 Nov 2026. Check eligibility and register.',
 'Drive'),
((SELECT id FROM users WHERE username='CSE2021002'),
 'Drive Result: Zoho Corporation',
 'Congratulations! You have been selected by Zoho Corporation. Package: ₹6.0 LPA.',
 'Result')
ON DUPLICATE KEY UPDATE title=VALUES(title);
