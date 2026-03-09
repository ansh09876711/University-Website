import email
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
from psycopg2.extras import RealDictCursor
import psycopg2
import pytesseract
from PIL import Image
import os
import smtplib
import threading
import time
import qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table
from reportlab.lib.units import inch
import os
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import TableStyle
from flask import send_file
import os
from email.mime.text import MIMEText
from models import db 
from models import HeroMedia, Placement, Recruiter, PlacementStudent
from datetime import timedelta
from flask_mail import Mail, Message
from flask_session import Session
from apscheduler.schedulers.background import BackgroundScheduler
from email_service import check_new_emails
 
app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.add_job(check_new_emails, 'interval', seconds=60)
scheduler.start()
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:college%40123@localhost:5432/college_portal"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.secret_key = "college_secret"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'collegeportal52@gmail.com'
app.config['MAIL_PASSWORD'] = 'fjnnrfzyknkdomuk'  # Gmail App password
app.config['MAIL_DEFAULT_SENDER'] = 'collegeportal52@gmail.com'
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_TYPE"] = "filesystem"
mail = Mail(app)
Session(app)


db.init_app(app)

# =====================
# DATABASE
# =====================
def get_pg():
    return psycopg2.connect(
        host="localhost",
        database="college_portal",
        user="postgres",
        password="college@123",
        port=5432
    )

# =====================
# HOME
# =====================
@app.route("/")
def home():

    hero_media = HeroMedia.query.all()
    placement = Placement.query.first()
    recruiters = Recruiter.query.all()
    students = PlacementStudent.query.all()

    return render_template(
        "index.html",
        hero_media=hero_media,
        placement=placement,
        recruiters=recruiters,
        students=students
    )

# =====================
# LOGIN (SINGLE LOGIN)
# =====================
@app.route("/login", methods=["GET","POST"])
def login():

    role_from_url = request.args.get("role")

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_pg()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return render_template("login.html", error="Invalid Credentials")

        if not check_password_hash(user["password"], password):
            return render_template("login.html", error="Wrong Password")

        if role_from_url and user["role"] != role_from_url:
            return render_template("login.html", error="Unauthorized role")

        # SESSION START
        session["username"] = user["username"]
        session["main_role"] = session.get("main_role", user["role"])
        session["role"] = user["role"]
        session.permanent = True

        # ===== STUDENT LOGIN FIX =====
        if user["role"] == "student":

            conn = get_pg()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT id, enrollment_no, class_id
                FROM students
                WHERE username=%s
            """,(username,))

            student_data = cur.fetchone()

            cur.close()
            conn.close()

            if not student_data:
                return "Student record missing"

            session["student_id"] = student_data["id"]
            session["enrollment_no"] = student_data["enrollment_no"]
            session["class_id"] = student_data["class_id"]

            return redirect("/student")

        elif user["role"] == "teacher":
            return redirect("/teacher")

        elif user["role"] == "admin":
            return redirect("/admin/portals")

        elif user["role"] == "director":
            return redirect("/admin")

        elif user["role"] == "accounts":
            return redirect("/accounts")

        elif user["role"] == "scholarship":
            return redirect("/scholarship")
        
        elif user["role"] == "canteen":
            return redirect("/admin_canteen")
        
        elif user["role"] == "canteen-dashboard":
            return redirect("/canteen-dashboard")

        elif user["role"] == "department":
            return redirect("/department")
        
        elif user["role"] == "registrar":
            return redirect("/registrar")

        elif user["role"] == "hod":
            return redirect("/hod")
        
        elif user["role"] == "library":
            return redirect("/library")
        
        elif user["role"] == "hr":
            return redirect("/hr")

        elif user["role"] == "principal":
            return redirect("/principal")

        elif user["role"] == "vice_principal":
            return redirect("/vice_principal")

    return render_template("login.html", role=role_from_url)


# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =====================
# ADMIN PORTALS
# =====================
@app.route("/admin/portals")
def admin_portals():

    print("SESSION ROLE =", session.get("role"))

    if session.get("role") != "admin":
        return redirect("/login")

    return render_template("dashboards/admin/admin_portals.html")

# =====================
# ADMIN SWITCH (CARDS CLICK)
# =====================
@app.route("/admin/switch/<role>")
def admin_switch(role):
    if session.get("role") != "admin":
        return redirect("/login")

    return redirect(f"/login?role={role}")

# =====================
# ADMIN DASHBOARD
# =====================
@app.route("/admin")
def admin():
    if session.get("role") not in ["admin", "director"]:
        return redirect("/login")
    return render_template("dashboards/admin.html")

# =====================
# ADMIN USERS
# =====================
@app.route("/admin/users")
def admin_users():
    if session.get("role") not in ["admin", "director"]:
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT username, role FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("dashboards/admin/admin_users.html", users=users)

# =====================
# ADMIN DEPARTMENTS
# =====================
@app.route("/admin/departments")
def admin_departments():
    if session.get("role") not in ["admin", "director"]:
        return redirect("/login")
    return render_template("dashboards/admin/admin_departments.html")

# =====================
# DUMMY ROUTES (404 FIX)
# =====================
@app.route("/admin/attendance")
def admin_attendance():
    return "<h2>Attendance Module (Coming Soon)</h2>"

@app.route("/admin/reports")
def admin_reports():
    return "<h2>Reports Module (Coming Soon)</h2>"

# =====================
# ROLE PAGES
# =====================
def role_page(role, template):

    # login check
    if "role" not in session:
        return redirect("/login")

    # wrong role access block
    if session["role"] != role:
        return redirect("/")

    return render_template(template)


@app.route("/accounts")
def accounts(): return role_page("accounts", "dashboards/admin/accounts.html")

@app.route("/scholarship")
def scholarship(): return role_page("scholarship", "dashboards/admin/scholarship.html")

@app.route("/hod")
def hod():

    if session.get("role") != "hod":
        return redirect("/login")

    return render_template("dashboards/hod/hod.html")


@app.route("/principal")
def principal(): return role_page("principal", "dashboards/admin/principal.html")

@app.route("/vice_principal")
def vice_principal(): return role_page("vice_principal", "dashboards/admin/vice_principal.html")

@app.route("/teacher")
def teacher():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    username = session["username"]

    # ✅ CHECK IF TEACHER EXISTS
    cur.execute("""
        SELECT * FROM teachers WHERE username=%s
    """,(username,))
    
    teacher = cur.fetchone()

    # ✅ IF NOT EXISTS → CREATE
    if not teacher:
        cur.execute("""
            INSERT INTO teachers(username, name)
            VALUES(%s,%s)
        """,(username, username))
        conn.commit()

        # Re-fetch after insert
        cur.execute("""
            SELECT * FROM teachers WHERE username=%s
        """,(username,))
        teacher = cur.fetchone()

    # (Optional) load classes if needed
    cur.execute("""
        SELECT class_name
        FROM teacher_classes
        WHERE teacher_username=%s
    """,(username,))
    classes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher.html",
        classes=classes,
        profile=teacher   # 👈 IMPORTANT
    )

@app.route("/student")
def student(): return role_page("student", "dashboards/student.html")
# =====================
# ADMIN – CREATE USER
# =====================
@app.route("/admin/create-user", methods=["POST"])
def admin_create_user():
    if session.get("role") not in ["admin", "director"]:
        return redirect("/login")

    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    hashed_password = generate_password_hash(password)

    conn = get_pg()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
            """,
            (username, hashed_password, role)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return f"Error: {e}"

    cur.close()
    conn.close()

    return redirect("/admin/users")

# =====================
# ADMIN – LOCK USER
# =====================
from flask import jsonify

@app.route("/admin/lock/<username>", methods=["POST"])
def admin_lock_user(username):
    if session.get("role") != "admin":
        return jsonify(success=False), 403

    conn = get_pg()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET locked = TRUE WHERE username = %s",
        (username,)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(success=True)

@app.route("/admin/unlock/<username>", methods=["POST"])
def admin_unlock_user(username):
    if session.get("role") != "admin":
        return jsonify(success=False), 403

    conn = get_pg()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET locked = FALSE, attempts = 0 WHERE username = %s",
        (username,)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify(success=True)


# =====================
# STUDENT MODULES
# =====================

@app.route("/student/profile")
def student_profile():
    if session.get("role") != "student":
        return redirect("/login?role=student")
    return render_template("dashboards/student/profile.html")

import calendar
from datetime import datetime
from flask import request, session, redirect, render_template
from psycopg2.extras import RealDictCursor


@app.route("/student/attendance")
def student_attendance():

    if session.get("role") != "student":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    student_id = session["student_id"]

    # ================= SELECTED MONTH =================

    selected_month = request.args.get("month")

    if selected_month:
        year, month = selected_month.split("-")
        year = int(year)
        month = int(month)
    else:
        today = datetime.today()
        year = today.year
        month = today.month
        selected_month = f"{year}-{str(month).zfill(2)}"

    # ================= DATE RECORDS =================

    cur.execute("""
        SELECT date, status
        FROM attendance
        WHERE student_id=%s
        AND EXTRACT(YEAR FROM date)=%s
        AND EXTRACT(MONTH FROM date)=%s
        ORDER BY date
    """,(student_id,year,month))

    records = cur.fetchall()

    # ================= CALENDAR LOOKUP DICT =================

    attendance_dict = {}

    for r in records:
        attendance_dict[r["date"].day] = r["status"]

    # ================= FULL CALENDAR GRID =================

    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    calendar_data = cal.monthdayscalendar(year,month)

    # ================= OVERALL STATS =================

    cur.execute("""
        SELECT
            COUNT(*) AS total_days,
            COUNT(CASE WHEN status='present' THEN 1 END) AS present_days,
            COUNT(CASE WHEN status='absent' THEN 1 END) AS absent_days
        FROM attendance
        WHERE student_id=%s
    """,(student_id,))

    stats = cur.fetchone()

    total = stats["total_days"] or 0
    present = stats["present_days"] or 0
    absent = stats["absent_days"] or 0

    percentage = round((present/total)*100,2) if total>0 else 0

    # ================= MONTHLY TABLE =================

    cur.execute("""
        SELECT
            TO_CHAR(date,'Month') AS month,
            COUNT(*) AS total_days,
            COUNT(CASE WHEN status='present' THEN 1 END) AS present_days,
            COUNT(CASE WHEN status='absent' THEN 1 END) AS absent_days
        FROM attendance
        WHERE student_id=%s
        GROUP BY month
        ORDER BY MIN(date)
    """,(student_id,))

    monthly = cur.fetchall()

    # ================= MONTH DROPDOWN =================

    cur.execute("""
        SELECT DISTINCT TO_CHAR(date,'YYYY-MM') AS month
        FROM attendance
        WHERE student_id=%s
        ORDER BY month DESC
    """,(student_id,))

    months = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/student/attendance.html",
        records=records,
        monthly=monthly,
        percentage=percentage,
        total=total,
        present=present,
        absent=absent,
        calendar_data=calendar_data,
        attendance=attendance_dict,
        selected_month=selected_month,
        months=months
    )


@app.route("/student/subjects")
def student_subjects():

    if session.get("role") != "student":
        return redirect("/login")

    class_id = session.get("class_id")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT *
        FROM subjects
        WHERE class_id=%s
        ORDER BY id DESC
    """,(class_id,))

    subjects = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/student/subjects.html",
        subjects=subjects
    )

@app.route("/student/materials")
def student_materials():

    if session.get("role") != "student":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT sm.*, c.class_name
        FROM study_materials sm
        JOIN classes c ON sm.class_id = c.id
        ORDER BY sm.id DESC
    """)

    materials = cur.fetchall()

    return render_template("dashboards/student/materials.html",
                           materials=materials)


@app.route("/student/assignments")
def student_assignments():

    if session.get("role") != "student":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
                SELECT *
                FROM assignments
                WHERE class_id=%s
                ORDER BY id DESC
                """,(session["class_id"],))


    assignments = cur.fetchall()

    return render_template(
        "dashboards/student/assignments.html",
        assignments=assignments
    )

@app.route("/submit-assignment/<int:id>", methods=["POST"])
def submit_assignment(id):

    file = request.files.get("file")

    filename = secure_filename(file.filename)

    file.save(os.path.join("static/uploads", filename))

    # save submission into DB here

    return redirect("/student/assignments")

@app.route("/student/leaderboard")
def student_leaderboard():
    if session.get("role") != "student":
        return redirect("/login?role=student")
    return render_template("dashboards/student/leaderboard.html")


@app.route("/student/certificates")
def student_certificates():
    if session.get("role") != "student":
        return redirect("/login?role=student")
    return render_template("dashboards/student/certificates.html")


@app.route("/student/library")
def student_library():
    if session.get("role") != "student":
        return redirect("/login?role=student")
    return render_template("dashboards/student/library.html")


@app.route("/student/fees")
def student_fees():
    if session.get("role") != "student":
        return redirect("/login?role=student")
    return render_template("dashboards/student/fees.html")


@app.route("/student/notices")
def student_notices():

    if session.get("role") != "student":
        return redirect("/login")

    student = session["username"]
    student_class = session["class_id"]

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT n.*,
        CASE WHEN nr.id IS NULL THEN TRUE ELSE FALSE END AS unread

        FROM notices n

        LEFT JOIN notice_reads nr
        ON n.id = nr.notice_id AND nr.username=%s

        WHERE n.class_name=%s
        ORDER BY n.is_pinned DESC, n.id DESC
    """,(student, student_class))

    notices = cur.fetchall()

    return render_template(
        "dashboards/student/student_notices.html",
        notices=notices
    )


@app.route("/student/settings")
def student_settings():
    if session.get("role") != "student":
        return redirect("/login?role=student")
    return render_template("dashboards/student/settings.html")

@app.route("/student/marks")
def student_marks():

    if session.get("role") != "student":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM marks
        WHERE student_id=%s
        ORDER BY id DESC
    """,(session["username"],))

    marks = cur.fetchall()

    return render_template("dashboards/student/student_marks.html", marks=marks)


from datetime import date

@app.route("/student/dashboard")
def student_dashboard():

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    student_class = session["class"]   # login ke time save hona chahiye

    cur.execute("""
        SELECT * FROM assignments
        WHERE class_name=%s
        ORDER BY id DESC
    """,(student_class,))

    assignments = cur.fetchall()

    return render_template("student_dashboard.html",
                           assignments=assignments)


@app.route("/teacher/attendance", methods=["GET","POST"])
def teacher_attendance():
    if session.get("role") != "teacher":
        return redirect("/login")

    class_id = request.args.get("class_id")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    students = []
    if class_id:
        cur.execute("""
            SELECT id, username
            FROM students
            WHERE class_id=%s
        """,(class_id,))
        students = cur.fetchall()

    return render_template(
        "dashboards/teacher/teacher_attendance.html",
        classes=classes,
        students=students,
        selected_class=class_id
    )

from werkzeug.security import generate_password_hash

@app.route("/teacher/profile", methods=["GET","POST"])
def teacher_profile():

    if session.get("role") != "teacher":
        return redirect("/login")

    username = session.get("username")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ================= SAVE =================
    if request.method == "POST":

        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        address = request.form.get("address")

        cur.execute("""
            UPDATE teachers
            SET name=%s,
                surname=%s,
                email=%s,
                address=%s
            WHERE username=%s
        """,(name, surname, email, address, username))

        conn.commit()

        # 🔥 VERY IMPORTANT (Reload data again)
        return redirect("/teacher/profile?updated=1")


    # ================= LOAD DATA =================
    cur.execute("""
        SELECT name, surname, email, address, photo
        FROM teachers
        WHERE username=%s
    """,(username,))

    teacher = cur.fetchone()

    print("Loaded teacher:", teacher)   # DEBUG

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher/teacher_profile.html",
        teacher=teacher
    )

from flask import render_template, request, redirect, session
from psycopg2.extras import RealDictCursor
from datetime import date

@app.route("/teacher/students")
def teacher_students():

    class_id = request.args.get("class_id")
    
    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # classes dropdown
    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    students = []

    if class_id:

                cur.execute("""
        SELECT
            s.id,
            s.enrollment_no,
            s.username,
            COALESCE(
                ROUND(
                    (COUNT(CASE WHEN a.status='present' THEN 1 END)::decimal
                    / NULLIF(COUNT(a.id),0)) * 100
                ,2)
            ,0) AS attendance_percentage

        FROM students s

        LEFT JOIN attendance a
        ON a.student_id = s.id

        WHERE s.class_id = %s

        GROUP BY s.id, s.enrollment_no, s.username

        ORDER BY s.id;
        """,(class_id,))

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher/teacher_students.html",
        classes=classes,
        students=students,
        selected_class=class_id
    )


@app.route("/teacher/mark-attendance", methods=["POST"])
def save_attendance():

    if session.get("role") != "teacher":
        return redirect("/login")

    class_id = request.form.get("class_id")
    date = request.form.get("date")

    if not class_id or not date:
        return "Class or Date missing"

    # ✅ FIRST connection banana hai
    conn = get_pg()
    cur = conn.cursor()

    # students of class
    cur.execute(
        "SELECT id, username FROM students WHERE class_id = %s",
        (class_id,)
    )

    students = cur.fetchall()

    for student_id, username in students:

        status = request.form.get(f"status_{student_id}")

        if status:

            # ✅ FINAL INSERT
            cur.execute("""
                INSERT INTO attendance
                (student, student_id, date, status, teacher_username)
                VALUES (%s,%s,%s,%s,%s)
            """, (
                username,
                student_id,
                date,
                status,
                session["username"]
            ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/teacher/students?class_id={class_id}")


@app.route("/teacher/add-student", methods=["POST"])
def add_student():
    username = request.form["username"]
    class_id = request.form["class_id"]

    conn = get_pg()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO students (username, class_id) VALUES (%s,%s)",
        (username, class_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/teacher/students?class_id=" + class_id)

import pandas as pd
from flask import request, redirect

@app.route("/teacher/upload-students", methods=["POST"])
def upload_students():

    if session.get("role") != "teacher":
        return redirect("/login")

    class_id = request.form.get("class_id")
    file = request.files.get("file")

    if not class_id:
        return "Class not selected", 400

    if not file:
        return "No file uploaded", 400

    import pandas as pd

    df = pd.read_excel(file)

    # ✅ column normalize
    df.columns = df.columns.str.strip().str.lower()

    print("DEBUG COLUMNS =", df.columns)

    conn = get_pg()
    cur = conn.cursor()

    # ✅ LOOP FIX (tumhara indentation galat tha)
    for _, row in df.iterrows():

        enrollment_no = str(row["enrollment_id"]).strip()   # ✅ spelling FIX
        username = str(row["username"]).strip()

        cur.execute("""
            INSERT INTO students (enrollment_no, username, class_id)
            VALUES (%s,%s,%s)
        """,(enrollment_no, username, class_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/teacher/students?class_id={class_id}")


@app.route("/teacher/upload-image", methods=["POST"])
def upload_image_ocr():
    if session.get("role") != "teacher":
        return redirect("/login")

    image = request.files["image"]
    class_id = request.form["class_id"]

    img = Image.open(image)

    extracted_text = pytesseract.image_to_string(img)

    return render_template(
        "dashboards/teacher/ocr_preview.html",
        text=extracted_text,
        class_id=class_id
    )

@app.route("/teacher/save-ocr", methods=["POST"])
def save_ocr_students():
    if session.get("role") != "teacher":
        return redirect("/login")

    text = request.form["text"]
    class_id = request.form["class_id"]

    students = text.splitlines()

    conn = get_pg()
    cur = conn.cursor()

    for s in students:
        s = s.strip()
        if s:
            cur.execute(
                "INSERT INTO students (username, class_id) VALUES (%s, %s)",
                (s, class_id)
            )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/teacher/students?class_id={class_id}")

@app.route("/teacher/attendance-percentage")
def attendance_percentage():

    if session.get("role") != "teacher":
        return redirect("/login")

    class_id = request.args.get("class_id")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # all classes
    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    data = []

    if class_id:
        cur.execute("""
            SELECT 
                s.id,
                s.username,
                COUNT(a.id) AS total_days,
                COUNT(CASE WHEN a.status='present' THEN 1 END) AS present_days
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            WHERE s.class_id = %s
            GROUP BY s.id, s.username
        """, (class_id,))

        rows = cur.fetchall()

        for r in rows:
            total = r["total_days"]
            present = r["present_days"]
            percent = round((present / total) * 100, 2) if total > 0 else 0

            data.append({
                "id": r["id"],
                "username": r["username"],
                "total": total,
                "present": present,
                "percent": percent
            })

    cur.close()
    conn.close()

    return render_template(
        "attendance_percentage.html",
        classes=classes,
        selected_class=class_id,
        data=data
    )

@app.route("/teacher/edit-student", methods=["POST"])
def edit_student():

    if session.get("role") != "teacher":
        return redirect("/login")

    student_id = request.form["student_id"]
    username = request.form["username"]
    class_id = request.form["class_id"]

    conn = get_pg()
    cur = conn.cursor()

    cur.execute(
        "UPDATE students SET username=%s WHERE id=%s",
        (username, student_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/teacher/students?class_id={class_id}")

@app.route("/teacher/delete-student", methods=["POST"])
def delete_student():

    if session.get("role") != "teacher":
        return redirect("/login")

    student_id = request.form["student_id"]
    class_id = request.form["class_id"]

    conn = get_pg()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM students WHERE id=%s",
        (student_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/teacher/students?class_id={class_id}")

@app.route("/teacher/delete-class-students", methods=["POST"])
def delete_class_students():

    if session.get("role") != "teacher":
        return redirect("/login")

    class_id = request.form["class_id"]

    conn = get_pg()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM students WHERE class_id=%s",
        (class_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/teacher/students?class_id={class_id}")

from werkzeug.utils import secure_filename

@app.route("/teacher/materials", methods=["GET","POST"])
def teacher_materials():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # class dropdown
    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    if request.method == "POST":

        title = request.form.get("title")
        subject = request.form.get("subject")
        class_id = request.form.get("class_id")
        file = request.files.get("file")

        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join("static/uploads", filename))

        cur.execute("""
            INSERT INTO study_materials
            (title, subject, file_path, teacher_username, class_id)
            VALUES (%s,%s,%s,%s,%s)
        """,(title,subject,filename,session["username"],class_id))

        conn.commit()

    # materials fetch (IMPORTANT — missing tha)
    cur.execute("SELECT * FROM study_materials ORDER BY id DESC")
    materials = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher/teacher_study_material.html",
        materials=materials,
        classes=classes
    )

@app.route("/teacher/delete_material/<int:id>", methods=["POST"])
def delete_material(id):

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # file name fetch
    cur.execute("SELECT file_path FROM study_materials WHERE id=%s",(id,))
    material = cur.fetchone()

    if material:
        filepath = os.path.join("static/uploads", material["file_path"])

        if os.path.exists(filepath):
            os.remove(filepath)

    # delete db record
    cur.execute("DELETE FROM study_materials WHERE id=%s",(id,))
    conn.commit()

    return redirect("/teacher/materials")

@app.route("/teacher/assignments", methods=["GET","POST"])
def teacher_assignments():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ADD ASSIGNMENT
    if request.method == "POST":

        title = request.form.get("title")
        subject = request.form.get("subject")
        description = request.form.get("description")
        deadline = request.form.get("deadline")

        file = request.files.get("file")

        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join("static/uploads", filename))

        cur.execute("""
            INSERT INTO assignments
            (title,subject,description,file_path,teacher_username,deadline)
            VALUES (%s,%s,%s,%s,%s,%s)
        """,(title,subject,description,filename,
             session["username"],deadline))

        conn.commit()

    # FETCH ALL
    cur.execute("SELECT * FROM assignments ORDER BY id DESC")
    assignments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher/teacher_assignments.html",
        assignments=assignments
    )



@app.route("/teacher/delete_assignment/<int:id>", methods=["POST"])
def delete_assignment(id):

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("DELETE FROM assignments WHERE id=%s",(id,))
    conn.commit()

    return redirect("/teacher/assignments")

@app.route("/teacher/submissions/<int:id>")
def view_submissions(id):

    conn=get_pg()
    cur=conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM assignment_submissions
        WHERE assignment_id=%s
    """,(id,))

    submissions=cur.fetchall()

    return render_template("teacher_submissions.html",
                           submissions=submissions)

@app.route("/teacher/marks", methods=["GET","POST"])
def teacher_marks():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # class filter
    class_name = request.args.get("class")

    # ADD MARKS
    if request.method == "POST":

        student_name = request.form.get("student_name")
        subject = request.form.get("subject")
        marks = request.form.get("marks")
        class_name = request.form.get("class_name")

        # AUTO GRADE
        marks = int(marks)

        if marks >= 90:
            grade = "A+"
        elif marks >= 75:
            grade = "A"
        elif marks >= 60:
            grade = "B"
        elif marks >= 40:
            grade = "C"
        else:
            grade = "Fail"

        cur.execute("""
            INSERT INTO marks
            (student_name, subject, marks, grade, class_name, teacher_username)
            VALUES (%s,%s,%s,%s,%s,%s)
        """,(student_name, subject, marks, grade,
             class_name, session["username"]))

        conn.commit()

    # FETCH MARKS (classwise)
    if class_name:
        cur.execute("""
            SELECT * FROM marks
            WHERE class_name=%s
            ORDER BY id DESC
        """,(class_name,))
    else:
        cur.execute("SELECT * FROM marks ORDER BY id DESC")

    marks = cur.fetchall()

    return render_template(
        "dashboards/teacher/teacher_marks.html",
        marks=marks,
        selected_class=class_name
    )


@app.route("/teacher/delete-mark/<int:id>", methods=["POST"])
def delete_mark(id):

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("DELETE FROM marks WHERE id=%s",(id,))
    conn.commit()

    return redirect("/teacher/marks")

@app.route("/leaderboard")
def leaderboard():

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT student_name,
               class_name,
               ROUND(AVG(marks),2) AS avg_marks
        FROM marks
        GROUP BY student_name, class_name
        ORDER BY avg_marks DESC
        LIMIT 10
    """)

    toppers = cur.fetchall()

    return render_template("leaderboard.html", toppers=toppers)

@app.route("/teacher/analytics")
def teacher_analytics():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT subject, marks
        FROM marks
        WHERE teacher_username=%s
    """,(session["username"],))

    data = cur.fetchall()

    # 👉 VERY IMPORTANT
    subjects = [row["subject"] for row in data]
    marksValues = [row["marks"] for row in data]

    return render_template(
        "dashboards/teacher/teacher_analytics.html",
        subjects=subjects,
        marksValues=marksValues
    )

@app.route("/teacher/notices", methods=["GET","POST"])
def teacher_notices():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    teacher = session["username"]

    # 👉 Teacher classes (Director assign)
    cur.execute("""
        SELECT class_name FROM teacher_classes
        WHERE teacher_username=%s
    """,(teacher,))

    classes = cur.fetchall()

    if request.method == "POST":

        title = request.form.get("title")
        message = request.form.get("message")
        class_name = request.form.get("class_name")

        important = True if request.form.get("important") else False
        pinned = True if request.form.get("pinned") else False

        cur.execute("""
            INSERT INTO notices
            (title,message,class_name,created_by,role,is_important,is_pinned)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,(title,message,class_name,teacher,"teacher",important,pinned))

        conn.commit()

    cur.execute("""
        SELECT * FROM notices
        WHERE created_by=%s
        ORDER BY is_pinned DESC, id DESC
    """,(teacher,))

    notices = cur.fetchall()

    return render_template(
        "dashboards/teacher/teacher_notices.html",
        notices=notices,
        classes=classes
    )

@app.route("/notice/read/<int:id>")
def mark_notice_read(id):

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO notice_reads(notice_id, username)
        VALUES(%s,%s)
    """,(id, session["username"]))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/student/notices")


@app.route("/teacher/subject")
def teacher_subjects():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT s.*, c.class_name
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        WHERE faculty=%s
    """,(session["username"],))

    subjects = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher/teacher_subject.html",
        subjects=subjects
    )


@app.route("/teacher/add-subject", methods=["POST"])
def teacher_add_subject():

    if session.get("role") != "teacher":
        return redirect("/login")

    subject_name = request.form["subject_name"]
    credits = request.form["credits"]
    subject_type = request.form["type"]
    class_id = request.form["class_id"]

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO subjects
        (subject_name, faculty, credits, type, class_id)
        VALUES (%s,%s,%s,%s,%s)
    """,(
        subject_name,
        session["username"],
        credits,
        subject_type,
        class_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/teacher/subject")

#================
# HOD MODULES
#================
@app.route("/hod/teachers")
def hod_teachers():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT username
        FROM users
        WHERE role='teacher'
        ORDER BY username
    """)

    teachers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboards/hod/teacher.html",
                           teachers=teachers)

@app.route("/hod/delete-teacher/<username>", methods=["POST"])
def hod_delete_teacher(username):

    if session.get("role") not in ["hod","director"]:
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE username=%s AND role='teacher'",
        (username,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/hod/teachers")

@app.route("/hod/add-teacher", methods=["POST"])
def hod_add_teacher():

    if session.get("role") not in ["hod","director"]:
        return redirect("/login")

    username = request.form["username"]
    password = request.form["password"]

    hashed_password = generate_password_hash(password)

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (username,password,role)
        VALUES (%s,%s,'teacher')
    """,(username,hashed_password))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/hod/teachers")

@app.route("/hod/assign-class", methods=["GET","POST"])
def assign_class():

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE role='teacher'")
    teachers = cur.fetchall()

    if request.method == "POST":

        teacher = request.form["teacher"]
        class_name = request.form["class_name"]

        # Duplicate prevent
        cur.execute("""
            INSERT INTO teacher_class_assign (teacher_username,class_name)
            SELECT %s,%s
            WHERE NOT EXISTS (
                SELECT 1 FROM teacher_class_assign
                WHERE teacher_username=%s AND class_name=%s
            )
        """,(teacher,class_name,teacher,class_name))

        conn.commit()

    cur.close()
    conn.close()

    return render_template("dashboards/hod/assign_class.html", teachers=teachers)


@app.route("/teacher/classes")
def teacher_classes():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn=get_pg()
    cur=conn.cursor()

    cur.execute("""
        SELECT class_name
        FROM teacher_classes
        WHERE teacher_username=%s
    """,(session["username"],))

    classes=cur.fetchall()

    return render_template(
        "dashboards/teacher/teacher_classes.html",
        classes=classes
    )

@app.route("/hod/profile", methods=["GET","POST"])
def hod_profile():

    if session.get("role") != "hod":
        return redirect("/login")

    username = session.get("username")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # SAVE
    if request.method == "POST":

        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        address = request.form.get("address")

        cur.execute("""
            UPDATE hod
            SET name=%s,
                surname=%s,
                email=%s,
                address=%s
            WHERE username=%s
        """,(name, surname, email, address, username))

        conn.commit()

        return redirect("/hod/profile?updated=1")

    # LOAD DATA
    cur.execute("""
        SELECT name, surname, email, address, photo
        FROM hod
        WHERE username=%s
    """,(username,))

    hod = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/hod_profile.html",
        hod=hod
    )

# ======================
# HOD CLASSROOM ACTIVITY
# ======================

@app.route("/hod/classroom-activity")
def hod_classroom_activity():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Total Classes
    cur.execute("SELECT COUNT(*) FROM classes")
    total_classes = cur.fetchone()["count"]

    # Total Teachers
    cur.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
    total_teachers = cur.fetchone()["count"]

    # Total Students
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()["count"]

    # Active Online Sessions
    cur.execute("""
        SELECT COUNT(*)
        FROM classroom_sessions
        WHERE schedule_time >= NOW() - INTERVAL '1 hour'
    """)
    live_sessions = cur.fetchone()["count"]

    # Attendance Today
    cur.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = CURRENT_DATE
    """)
    today_attendance = cur.fetchone()["count"]

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/classroom_activity.html",
        total_classes=total_classes,
        total_teachers=total_teachers,
        total_students=total_students,
        live_sessions=live_sessions,
        today_attendance=today_attendance
    )

# ======================
# HOD STUDENT ATTENDANCE
# ======================

@app.route("/hod/student-attendance")
def hod_student_attendance():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Overall attendance stats
    cur.execute("""
        SELECT 
            COUNT(*) AS total_records,
            COUNT(CASE WHEN status='present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN status='absent' THEN 1 END) AS absent_count
        FROM attendance
    """)

    stats = cur.fetchone()

    # Class wise attendance
    cur.execute("""
        SELECT c.class_name,
               COUNT(a.id) AS total,
               COUNT(CASE WHEN a.status='present' THEN 1 END) AS present
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN classes c ON s.class_id = c.id
        GROUP BY c.class_name
        ORDER BY c.class_name
    """)

    class_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/student_attendance.html",
        stats=stats,
        class_data=class_data
    )

# ======================
# HOD STUDENT INFO
# ======================

@app.route("/hod/student-info")
def hod_student_info():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT 
            s.id,
            s.username,
            s.enrollment_no,
            c.class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY s.id DESC
    """)

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/student_info.html",
        students=students
    )

# ======================
# HOD CLASSROOM LIST (Improved)
# ======================

@app.route("/hod/classrooms")
def hod_classrooms():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        
    SELECT 
        c.class_name,
        COUNT(DISTINCT s.id) AS total_students,
        STRING_AGG(DISTINCT t.teacher_username, ', ') AS teachers
    FROM classes c
    LEFT JOIN students s ON s.class_id = c.id
    LEFT JOIN teacher_class_assign t ON c.class_name = t.class_name
    GROUP BY c.class_name
    ORDER BY c.class_name
""")
    classrooms = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/classrooms.html",
        classrooms=classrooms
    )

@app.route("/hod/material")
def hod_material():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor()

    selected_class = request.args.get("class")
    selected_subject = request.args.get("subject")

    query = """
    SELECT 
        c.class_name,
        m.subject,
        m.title,
        m.file_path,
        m.teacher_username
    FROM study_materials m
    LEFT JOIN classes c ON m.class_id = c.id
    WHERE 1=1
    """

    values = []

    if selected_class:
        query += " AND c.class_name = %s"
        values.append(selected_class)

    if selected_subject:
        query += " AND m.subject = %s"
        values.append(selected_subject)

    query += " ORDER BY c.class_name, m.subject"

    cur.execute(query, values)
    materials = cur.fetchall()

    # Dropdown data
    cur.execute("SELECT DISTINCT class_name FROM classes")
    classes = cur.fetchall()

    cur.execute("SELECT DISTINCT subject FROM study_materials")
    subjects = cur.fetchall()

    # ✅ CLOSE cursor & connection
    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/material.html",
        materials=materials,
        classes=classes,
        subjects=subjects,
        selected_class=selected_class,
        selected_subject=selected_subject
    )

from flask import send_from_directory

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route("/hod/staff-info")
def hod_staff_info():

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            u.username,
            tp.subject,
            c.class_name,
            tp.degree,
            tp.photo
        FROM users u
        LEFT JOIN teacher_profiles tp 
            ON u.id = tp.teacher_id
        LEFT JOIN classes c 
            ON tp.class_id = c.id
        WHERE u.role = 'teacher'
        ORDER BY u.username
    """)

    teachers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/staff_info.html",
        teachers=teachers
    )

# ======================
# HOD MANAGE DEVICES
# ======================

@app.route("/hod/manage-devices")
def hod_manage_devices():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT device_name, device_type, status, assigned_class
        FROM devices
        ORDER BY device_name
    """)

    devices = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/manage_devices.html",
        devices=devices
    )

# ======================
# HOD MARKS ANALYTICS
# ======================

@app.route("/hod/marks-analytics")
def hod_marks_analytics():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Subject average
    cur.execute("""
        SELECT subject, ROUND(AVG(marks),2) 
        FROM marks
        GROUP BY subject
        ORDER BY subject
    """)
    data = cur.fetchall()

    # Top 5 toppers
    cur.execute("""
        SELECT student_name,
               ROUND(AVG(marks),2) AS avg_marks
        FROM marks
        GROUP BY student_name
        ORDER BY avg_marks DESC
        LIMIT 5
    """)
    toppers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/marks_analytics.html",
        data=data,
        toppers=toppers
    )

@app.route("/hod/attendance-analytics")
def hod_attendance_analytics():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Student-wise attendance percentage
    cur.execute("""
        SELECT student,
               ROUND(
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)
                   *100.0 / COUNT(*), 2
               ) AS attendance_percentage
        FROM attendance
        GROUP BY student
        ORDER BY student
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/attendance_analytics.html",
        data=data
    )

@app.route("/hod/student-leaderboard")
def hod_student_leaderboard():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Top students based on average marks
    cur.execute("""
        SELECT student_name,
               ROUND(AVG(marks),2) AS avg_marks
        FROM marks
        GROUP BY student_name
        ORDER BY avg_marks DESC
        LIMIT 10
    """)

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/student_leaderboard.html",
        students=students
    )
# ======================
# HOD WORKLOAD
# ======================

@app.route("/hod/workload")
def hod_workload():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT teacher_username,
        COUNT(*) AS total_classes,
        STRING_AGG(class_name, ', ') AS classes
        FROM teacher_class_assign
        GROUP BY teacher_username
        ORDER BY teacher_username
    """)

    workload = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/workload.html",
        workload=workload
    )


# ======================
# DELETE ASSIGNED CLASS
# ======================

@app.route("/hod/delete-assigned-class", methods=["POST"])
def delete_assigned_class():

    print("SESSION DEBUG:", session)

    if session.get("role") != "hod":
        print("NOT HOD LOGIN")
        return redirect("/login")

    teacher = request.form.get("teacher")
    class_name = request.form.get("class_name")

    print("DELETE REQUEST:", teacher, class_name)

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM teacher_class_assign
        WHERE teacher_username=%s
        AND class_name=%s
    """,(teacher,class_name))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/hod/workload")

#====Hod Academic====#

@app.route("/hod/academic")
def hod_academic():

    if session.get("role") != "hod":
        return redirect("/login")

    return render_template("dashboards/hod/academic.html")

@app.route("/hod/manage-classes")
def manage_classes():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT teacher_username, class_name
        FROM teacher_class_assign
        ORDER BY teacher_username
    """)

    classes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/manage_classes.html",
        classes=classes
    )

@app.route("/hod/material-monitor")
def material_monitor():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT title, subject, teacher_username
        FROM study_materials
        ORDER BY id DESC
    """)

    materials = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/material_monitor.html",
        materials=materials
    )

@app.route("/hod/assignment-overview")
def assignment_overview():

    if session.get("role") != "hod":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT title, subject, teacher_username, deadline
        FROM assignments
        ORDER BY id DESC
    """)

    assignments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hod/assignment_overview.html",
        assignments=assignments
    )

#=====Department====#

@app.route("/department-login", methods=["POST"])
def department_login():

    if request.form["password"] == "admin123":
        session["department"] = True
        return redirect("/department")

    return redirect("/login")

@app.route("/department")
def department_dashboard():

    if session.get("role") != "department":
        return redirect("/login")

    sections = get_pg().cursor(cursor_factory=RealDictCursor)

    hero_media = HeroMedia.query.all()

    return render_template(
        "dashboards/department/department.html",
        hero_media=hero_media
    )

@app.route("/upload-hero-media", methods=["POST"])
def upload_hero():

    if session.get("role") != "department":
        return redirect("/login")

    files = request.files.getlist("media")

    for file in files:

        if file.filename == "":
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)

        file_type = "image"

        if filename.lower().endswith(("mp4","webm","mov")):
            file_type = "video"

        hero = HeroMedia(
            file_name = filename,
            type = file_type
        )

        db.session.add(hero)

    db.session.commit()

    return redirect("/department")

@app.route("/delete-hero/<int:id>", methods=["POST"])
def delete_hero(id):

    if session.get("role") != "department":
        return redirect("/login")

    media = HeroMedia.query.get(id)

    if media:

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], media.file_name)

        if os.path.exists(filepath):
            os.remove(filepath)

        db.session.delete(media)
        db.session.commit()

    return redirect("/department")

@app.route("/delete-all-hero", methods=["POST"])
def delete_all_hero():

    if session.get("role") != "department":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # all media fetch
    cur.execute("SELECT file_name FROM hero_media")
    media_list = cur.fetchall()

    # delete files from folder
    for media in media_list:

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], media["file_name"])

        if os.path.exists(filepath):
            os.remove(filepath)

    # delete database records
    cur.execute("DELETE FROM hero_media")

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/department")

#===============#
#  placement    #
#===============#
from flask import render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/placement", methods=["GET","POST"])
def placement_admin():

    if request.method == "POST":

        student_name = request.form.get("student_name")
        company_name = request.form.get("company_name")
        ctc = request.form.get("ctc")
        description = request.form.get("description")

        student_img = request.files.get("student_image")
        company_logo = request.files.get("company_logo")

        if not student_name or not company_name:
            return "Required fields missing"

        student_filename = secure_filename(student_img.filename)
        company_filename = secure_filename(company_logo.filename)

        student_img.save(os.path.join(app.config["UPLOAD_FOLDER"], student_filename))
        company_logo.save(os.path.join(app.config["UPLOAD_FOLDER"], company_filename))

        new_student = PlacementStudent(
            student_name=student_name,
            student_image=student_filename,
            company_name=company_name,
            company_logo=company_filename,
            ctc=ctc,
            description=description
        )

        db.session.add(new_student)
        db.session.commit()

        return redirect("/placement")

    students = PlacementStudent.query.all()
    return render_template("dashboards/department/placement.html", students=students)

@app.route("/create-db")
def create_db():

    with app.app_context():
        db.create_all()

    return "DB CREATED"

# DELETE SINGLE
@app.route("/delete-placement/<int:id>", methods=["POST"])
def delete_placement(id):

    student = PlacementStudent.query.get(id)

    if student:

        # delete files
        student_path = os.path.join(app.config["UPLOAD_FOLDER"], student.student_image)
        company_path = os.path.join(app.config["UPLOAD_FOLDER"], student.company_logo)

        if os.path.exists(student_path):
            os.remove(student_path)

        if os.path.exists(company_path):
            os.remove(company_path)

        db.session.delete(student)
        db.session.commit()

    return redirect("/placement")


# DELETE ALL
@app.route("/delete-all-placement", methods=["POST"])
def delete_all_placement():

    students = PlacementStudent.query.all()

    for s in students:

        student_path = os.path.join(app.config["UPLOAD_FOLDER"], s.student_image)
        company_path = os.path.join(app.config["UPLOAD_FOLDER"], s.company_logo)

        if os.path.exists(student_path):
            os.remove(student_path)

        if os.path.exists(company_path):
            os.remove(company_path)

        db.session.delete(s)

    db.session.commit()

    return redirect("/placement")

from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload-placement", methods=["POST"])
def upload_placement():

    student_name = request.form["student_name"]
    company_name = request.form["company"]
    ctc = request.form["ctc"]

    file = request.files["image"]
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    logo = request.files.get('company_logo')

    logo_name = None
    if logo:
        logo_name = secure_filename(logo.filename)
        logo.save(os.path.join('static/recruiters', logo_name))

    new_student = PlacementStudent(
        student_name=student_name,
        company_name=company_name,
        ctc=ctc,
        student_image=filename,
        company_logo=logo_name
    )

    db.session.add(new_student)
    db.session.commit()

    return redirect("/homepageplacement")


RECRUITER_FOLDER = os.path.join(app.root_path, "static", "recruiters")
os.makedirs(RECRUITER_FOLDER, exist_ok=True)


@app.route('/upload_recruiter', methods=['POST'])
def upload_recruiter():

    company_name = request.form.get("company_name")
    file = request.files.get("company_logo")

    filename = secure_filename(file.filename)
    file.save(os.path.join(RECRUITER_FOLDER, filename))

    new_recruiter = Recruiter(
        company_name=company_name,
        company_logo=filename
    )

    db.session.add(new_recruiter)
    db.session.commit()

    return redirect("/homepageplacement")

@app.route("/placementhome")
def placementhome():

    placements = PlacementStudent.query.all()
    recruiters = Recruiter.query.all()
    student = PlacementStudent.query.all()

    return render_template(
        "homepage/placementhome.html",
        placements=placements,
        recruiters=recruiters,
        student=student
    )

@app.route("/delete-home-placement/<int:id>", methods=["POST"])
def delete_home_placement(id):

    student = PlacementStudent.query.get_or_404(id)

    # image delete safely
    if student.student_image:

        path = os.path.join(app.root_path, "static", "uploads", student.student_image)

        if os.path.exists(path):
            os.remove(path)

    # delete DB record
    db.session.delete(student)
    db.session.commit()

    # ⭐ SAME PAGE PAR WAPAS
    return redirect("/homepageplacement")

@app.route("/delete-all-home-placement", methods=["POST"])
def delete_all_home_placement():

    students = PlacementStudent.query.all()

    for s in students:

        if s.student_image:

            path = os.path.join(app.root_path, "static", "uploads", s.student_image)

            if os.path.exists(path):
                os.remove(path)

        db.session.delete(s)

    db.session.commit()

    # ⭐ SAME PAGE PAR RETURN
    return redirect("/homepageplacement")


@app.route("/homepageplacement")
def homepageplacement():

    placements = PlacementStudent.query.all()
    recruiters = Recruiter.query.all()

    return render_template(
        "dashboards/department/homepageplacement.html",
        placements=placements,
        recruiters=recruiters
    )

@app.route("/delete-recruiter/<int:id>", methods=["POST"])
def delete_recruiter(id):

    recruiter = Recruiter.query.get(id)

    if recruiter:

        path = os.path.join("static/recruiters", recruiter.company_logo)

        if os.path.exists(path):
            os.remove(path)

        db.session.delete(recruiter)
        db.session.commit()

    return redirect("/homepageplacement")

@app.route("/delete-all-recruiters", methods=["POST"])
def delete_all_recruiters():

    recruiters = Recruiter.query.all()

    for r in recruiters:

        path = os.path.join("static/recruiters", r.company_logo)

        if os.path.exists(path):
            os.remove(path)

        db.session.delete(r)

    db.session.commit()

    return redirect("/homepageplacement")

@app.route("/recruiters")
def all_recruiters():

    recruiters = Recruiter.query.all()

    return render_template(
        "homepage/all_recruiters.html",
        recruiters=recruiters
    )

import random
from flask import session, request, redirect, render_template
from flask_mail import Message

@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        conn = get_pg()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # ✅ FORM email use करो (session नहीं)
        cur.execute("""
        SELECT username FROM teachers WHERE email=%s
        """,(email,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return "Email not found"

        # Generate OTP
        otp = str(random.randint(100000,999999))

        session["reset_otp"] = otp
        session["reset_email"] = email

        # ✅ OTP expiry (5 minutes)
        session["otp_expiry"] = (datetime.now() + timedelta(minutes=5)).timestamp()

        # Send mail
        msg = Message(
            "Password Reset OTP",
            recipients=[email]
        )

        msg.body = f"Your OTP is: {otp}"

        mail.send(msg)

        return redirect("/verify-otp")

    return render_template("forgot_password.html")

from datetime import datetime

@app.route("/verify-otp", methods=["GET","POST"])
def verify_otp():

    if request.method == "POST":

        user_otp = request.form.get("otp")

        # ✅ Check expiry
        expiry_time = session.get("otp_expiry")

        if not expiry_time or datetime.now().timestamp() > expiry_time:
            return "OTP Expired"

        # ✅ Check OTP
        if user_otp != session.get("reset_otp"):
            return "Invalid OTP"

        return redirect("/reset-password")

    return render_template("verify_otp.html")


@app.route("/reset-password", methods=["GET","POST"])
def reset_password():

    if request.method == "POST":

        new_password = request.form.get("new_password")

        hashed = generate_password_hash(new_password)

        conn = get_pg()
        cur = conn.cursor()

        # get username from teachers
        cur.execute("""
            SELECT username FROM teachers WHERE email=%s
        """,(session.get("reset_email"),))

        user = cur.fetchone()

        if not user:
            return "User not found"

        username = user[0]

        # update LOGIN table password
        cur.execute("""
            UPDATE users
            SET password=%s
            WHERE username=%s
        """,(hashed, username))

        conn.commit()

        cur.close()
        conn.close()

        session.pop("reset_otp",None)
        session.pop("reset_email",None)

        return redirect("/login")

    return render_template("reset_password.html")

@app.route("/eligibility")
def eligibility():
    return render_template("homepage/eligibility.html")

@app.route("/prospectus")
def prospectus():
    return render_template("prospectus.html")

@app.route("/apply", methods=["GET","POST"])
def apply():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        state = request.form.get("state")
        city = request.form.get("city")
        course = request.form.get("course")

        conn = get_pg()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO admission_applications
            (full_name, email, mobile, state, city, course, status)
            VALUES (%s,%s,%s,%s,%s,%s,'pending')
        """,(full_name,email,mobile,state,city,course))

        conn.commit()
        cur.close()
        conn.close()

        # ✅ ONLY success page
        return redirect("/apply-success")

    return render_template("dashboards/admission/apply.html")

@app.route("/apply-success")
def apply_success():
    return render_template("dashboards/admission/apply_success.html")
# =====================
# ADMISSION CELL DASHBOARD
# =====================

@app.route("/admission")
def admission_cell():

    # login protection
    if session.get("role") != "admin":
        return redirect("/login")

    return render_template("dashboards/admission/admission.html")

@app.route("/admission/new-applications")
def new_applications():

    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM admission_applications
        WHERE status='pending'
        ORDER BY id DESC
    """)

    applications = cur.fetchall()

    return render_template(
        "dashboards/admission/new_applications.html",
        applications=applications
    )

@app.route("/admission/approve")
def approve_admissions():

    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM admission_applications
        WHERE status='pending'
    """)

    applications = cur.fetchall()

    return render_template(
        "dashboards/admission/approve.html",
        applications=applications
    )

@app.route("/admission/action/<int:id>/<action>", methods=["POST"])
def admission_action(id, action):

    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor()

    status = "approved" if action == "approve" else "rejected"

    cur.execute("""
        UPDATE admission_applications
        SET status=%s
        WHERE id=%s
    """,(status,id))

    conn.commit()

    return redirect("/admission/approve")

# ===== ABOUT SECTION PAGES =====

@app.route("/the-university")
def the_university():
    return render_template("about/the_university.html")

@app.route("/heritage")
def heritage():
    return render_template("about/heritage.html")

@app.route("/leadership")
def leadership():
    return render_template("about/leadership.html")

@app.route("/director-message")
def director_message():
    return render_template("about/director_message.html")

@app.route("/dean-message")
def dean_message():
    return render_template("about/dean_message.html")

@app.route("/awards")
def awards():
    return render_template("about/awards.html")

@app.route("/approvals")
def approvals():
    return render_template("about/approvals.html")

@app.route("/mandatory-disclosure")
def mandatory_disclosure():
    return render_template("about/mandatory_disclosure.html")

@app.route("/vision")
def vision():
    return render_template("about/vision.html")

@app.route("/core-values")
def core_values():
    return render_template("about/core_values.html")

@app.route("/governance")
def governance():
    return render_template("about/governance.html")

@app.route("/faculties")
def faculties():
    return render_template("about/faculties.html")

@app.route("/committees")
def committees():
    return render_template("about/committees.html")

@app.route("/regulations")
def regulations():
    return render_template("about/regulations.html")

@app.route("/act")
def act():
    return render_template("about/act.html")

@app.route("/development-plan")
def development_plan():
    return render_template("about/development_plan.html")

@app.route("/collaboration")
def collaboration():
    return render_template("about/collaboration.html")

#====================
# Schedules & Timetable
#====================

from werkzeug.utils import secure_filename
import os

@app.route("/teacher/schedule", methods=["GET","POST"])
def teacher_schedule():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    teacher = session["username"]

    # 🔥 Only assigned classes
    cur.execute("""
        SELECT c.id, c.class_name
        FROM classes c
        JOIN teacher_class_assign t
        ON c.class_name = t.class_name
        WHERE t.teacher_username=%s
    """,(teacher,))

    classes = cur.fetchall()

    # ================= UPLOAD =================
    if request.method == "POST":

        class_id = request.form.get("class_id")
        file = request.files.get("timetable")

        if file and file.filename != "":

            filename = secure_filename(file.filename)
            filepath = os.path.join("static/uploads", filename)
            file.save(filepath)

            # 🔥 Delete old timetable of that class
            cur.execute("""
                SELECT image_path FROM timetable_images
                WHERE class_id=%s
            """,(class_id,))
            old = cur.fetchone()

            if old:
                old_path = os.path.join("static/uploads", old["image_path"])
                if os.path.exists(old_path):
                    os.remove(old_path)

                cur.execute("""
                    DELETE FROM timetable_images
                    WHERE class_id=%s
                """,(class_id,))

            # Insert new
            cur.execute("""
                INSERT INTO timetable_images
                (class_id, image_path, uploaded_by)
                VALUES (%s,%s,%s)
            """,(class_id, filename, teacher))

            conn.commit()

    # ================= FETCH EXISTING =================
    cur.execute("""
        SELECT t.id, t.image_path, c.class_name
        FROM timetable_images t
        JOIN classes c ON t.class_id = c.id
        WHERE t.uploaded_by=%s
        ORDER BY t.id DESC
    """,(teacher,))

    timetables = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/teacher/teacher_schedule.html",
        classes=classes,
        timetables=timetables
    )

@app.route("/teacher/delete-timetable/<int:id>", methods=["POST"])
def delete_timetable(id):

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT image_path FROM timetable_images
        WHERE id=%s
    """,(id,))

    data = cur.fetchone()

    if data:
        path = os.path.join("static/uploads", data["image_path"])
        if os.path.exists(path):
            os.remove(path)

        cur.execute("DELETE FROM timetable_images WHERE id=%s",(id,))
        conn.commit()

    cur.close()
    conn.close()

    return redirect("/teacher/schedule")

@app.route("/student/timetable")
def student_timetable():

    if session.get("role") != "student":
        return redirect("/login")

    class_id = session.get("class_id")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT image_path
        FROM timetable_images
        WHERE class_id=%s
        ORDER BY id DESC
        LIMIT 1
    """,(class_id,))

    timetable = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/student/timetable.html",
        timetable=timetable
    )

# =====================
# Test
# =====================
@app.route("/teacher/Test", methods=["GET","POST"])
def teacher_test():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    if request.method == "POST":

        title = request.form.get("title")
        class_id = request.form.get("class_id")
        deadline = request.form.get("deadline")

        file = request.files.get("file")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join("static/uploads", filename))

        cur.execute("""
            INSERT INTO tests
            (title,class_id,deadline,file_path,teacher_username)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING id
        """,(title,class_id,deadline,filename,session["username"]))

        test_id = cur.fetchone()["id"]

        questions = request.form.getlist("question[]")
        opt1 = request.form.getlist("opt1[]")
        opt2 = request.form.getlist("opt2[]")
        opt3 = request.form.getlist("opt3[]")
        opt4 = request.form.getlist("opt4[]")
        correct = request.form.getlist("correct[]")

        for i in range(len(questions)):
            cur.execute("""
                INSERT INTO test_questions
                (test_id,question,option1,option2,option3,option4,correct_answer)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,(test_id,questions[i],opt1[i],opt2[i],opt3[i],opt4[i],correct[i]))

        conn.commit()

    cur.execute("SELECT * FROM tests WHERE teacher_username=%s",(session["username"],))
    tests = cur.fetchall()

    return render_template(
    "dashboards/teacher/teacher_test.html",
    classes=classes,
    tests=tests,
    current_time=datetime.now()
)

@app.route("/teacher/delete-test/<int:id>", methods=["POST"])
def delete_teacher_test(id):

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("DELETE FROM test_questions WHERE test_id=%s",(id,))
    cur.execute("DELETE FROM tests WHERE id=%s",(id,))

    conn.commit()

    return redirect("/teacher/Test")

from datetime import datetime

@app.route("/student/tests")
def student_tests():

    if session.get("role") != "student":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT *
        FROM tests
        WHERE class_id=%s
        ORDER BY id DESC
    """,(session["class_id"],))

    tests = cur.fetchall()

    return render_template(
        "dashboards/student/tests.html",
        tests=tests,
        current_time=datetime.now()
    )

@app.route("/student/start-test/<int:test_id>", methods=["GET","POST"])
def student_start_test(test_id):

    if session.get("role") != "student":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM tests WHERE id=%s",(test_id,))
    test = cur.fetchone()

    cur.execute("""
        SELECT * FROM test_questions
        WHERE test_id=%s
    """,(test_id,))
    questions = cur.fetchall()

    if request.method == "POST":

        cur.execute("""
            INSERT INTO test_submissions
            (test_id, student_id)
            VALUES (%s,%s)
        """,(test_id, session["student_id"]))

        conn.commit()

        return redirect("/student/tests")

    return render_template(
        "dashboards/student/start_test.html",
        test=test,
        questions=questions
    )

@app.route("/teacher/test-submissions/<int:test_id>")
def teacher_test_submissions(test_id):

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT s.id, s.username, ts.submitted_at
        FROM students s
        LEFT JOIN test_submissions ts
        ON ts.student_id = s.id
        AND ts.test_id=%s
    """,(test_id,))

    students = cur.fetchall()

    return render_template(
        "dashboards/teacher/test_submissions.html",
        students=students
    )

# =====================
# Online Classes (Zoom Integration)
# =====================
from datetime import datetime

@app.route("/teacher/online", methods=["GET","POST"])
def teacher_online():

    if session.get("role") != "teacher":
        return redirect("/login")

    conn=get_pg()
    cur=conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM classes")
    classes=cur.fetchall()

    if request.method=="POST":

        title=request.form.get("title")
        class_id=request.form.get("class_id")
        type=request.form.get("type")
        schedule_time=request.form.get("schedule_time")
        meeting_link=request.form.get("meeting_link")
        video_link=request.form.get("video_link")

        cur.execute("""
        INSERT INTO classroom_sessions
        (title,class_id,type,schedule_time,meeting_link,video_link,teacher_username)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,(title,class_id,type,schedule_time,meeting_link,video_link,session["username"]))

        conn.commit()

    cur.execute("SELECT * FROM classroom_sessions WHERE teacher_username=%s",
                (session["username"],))

    sessions=cur.fetchall()

    return render_template(
        "dashboards/teacher/teacher_online.html",
        classes=classes,
        sessions=sessions
    )

@app.route("/teacher/delete-session/<int:id>", methods=["POST"])
def delete_session(id):

    conn=get_pg()
    cur=conn.cursor()

    cur.execute("DELETE FROM classroom_sessions WHERE id=%s",(id,))
    conn.commit()

    return redirect("/teacher/online")

@app.route("/student/classroom")
def student_classroom():

    if session.get("role") != "student":
        return redirect("/login")

    conn=get_pg()
    cur=conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT *
        FROM classroom_sessions
        WHERE class_id=%s
        ORDER BY schedule_time ASC
    """,(session["class_id"],))

    sessions=cur.fetchall()

    now=datetime.now()

    for s in sessions:

        if s["schedule_time"]:
            diff=(s["schedule_time"]-now).total_seconds()

            if -3600 < diff < 3600:
                s["auto_status"]="live"
            elif diff>0:
                s["auto_status"]="upcoming"
            else:
                s["auto_status"]="recorded"
        else:
            s["auto_status"]=s["type"]

    return render_template(
        "dashboards/student/super_classroom.html",
        sessions=sessions
    )

@app.route("/student/mark-attendance/<int:id>", methods=["POST"])
def mark_attendance(id):

    conn=get_pg()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO class_attendance(session_id,student_id)
    VALUES (%s,%s)
    """,(id,session["student_id"]))

    conn.commit()

    return "",204

# =====================
# HR Department - Material Monitoring & Assignment Overview
# =====================
@app.route("/hr")
def hr_dashboard():

    if session.get("role") != "hr":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT COUNT(*) FROM employees")
    total_staff = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM leaves WHERE status='Pending'")
    pending_leaves = cur.fetchone()["count"]

    cur.execute("SELECT SUM(salary) FROM payroll")
    total_salary = cur.fetchone()["sum"] or 0

    return render_template(
        "dashboards/hr/hr_dashboard.html",
        total_staff=total_staff,
        pending_leaves=pending_leaves,
        total_salary=total_salary
    )
@app.route("/hr/teachers")
def hr_teachers():

    if session.get("role") != "hr":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT username
        FROM users
        WHERE role='teacher'
        ORDER BY username
    """)

    teachers = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboards/hr/teacher.html",
                           teachers=teachers)

@app.route("/hr/employees", methods=["GET","POST"])
def hr_employees():

    if session.get("role") != "hr":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT username
        FROM users
        WHERE role='teacher'
        ORDER BY username
    """)
    
    # ADD EMPLOYEE
    if request.method == "POST":

        name = request.form.get("name")
        department = request.form.get("department")
        designation = request.form.get("designation")
        salary = request.form.get("salary")

        cur.execute("""
        INSERT INTO employees (name,department,designation,salary)
        VALUES (%s,%s,%s,%s)
        """,(name,department,designation,salary))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/hr/employees")

    # FETCH ALL
    cur.execute("SELECT * FROM employees ORDER BY id DESC")
    employees = cur.fetchall()
    teachers = cur.fetchall()
    return render_template("dashboards/hr/employees.html", employees=employees)

# ===============================
# HR LEAVES MANAGEMENT
# ===============================
# =============================
# EMAIL SETTINGS
# =============================

EMAIL = "collegeportal52@gmail.com"
PASSWORD = "gmwdsbpfbhjwqvph"   # space ke bina

# =============================
# SEND STATUS EMAIL FUNCTION
# =============================

def send_status_email(to_email, status):

    try:

        subject = "Leave Status Update"

        body = f"""
Dear Teacher,

Your leave request has been {status.upper()} by HR.

Thanks
EduStack University
"""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL
        msg["To"] = to_email

        print("Sending mail to:", to_email)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)

        server.send_message(msg)
        server.quit()

        print("MAIL SENT SUCCESS")

    except Exception as e:
        print("MAIL ERROR:", e)

# =============================
# HR LEAVE LIST PAGE
# =============================

@app.route("/hr/leaves")
def hr_leaves():

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM hr_email_leaves
        ORDER BY id DESC
    """)

    email_leaves = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/hr/leaves.html",
        email_leaves=email_leaves
    )

# =============================
# APPROVE EMAIL LEAVE
# =============================

@app.route("/hr/email-leave/approve/<int:id>")
def approve_email_leave(id):

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        UPDATE hr_email_leaves
        SET status='approved'
        WHERE id=%s
        RETURNING teacher_email
    """,(id,))
    print("APPROVE CLICKED")
    data = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    
    if data:
        send_status_email(data["teacher_email"], "approved")
        print("Sending mail to:", data["teacher_email"])
    return redirect("/hr/leaves")

# =============================
# REJECT EMAIL LEAVE
# =============================

@app.route("/hr/email-leave/reject/<int:id>")
def reject_email_leave(id):

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        UPDATE hr_email_leaves
        SET status='rejected'
        WHERE id=%s
        RETURNING teacher_email
    """,(id,))
    print("REJECT CLICKED")
    data = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    if data:
        send_status_email(data["teacher_email"], "rejected")

    return redirect("/hr/leaves")

@app.route("/hr/payroll", methods=["GET","POST"])
def hr_payroll():

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == "POST":
        emp_id = request.form.get("employee_id")
        month = request.form.get("month")
        salary = request.form.get("salary")

        cur.execute("""
        INSERT INTO payroll (employee_id,month,salary)
        VALUES (%s,%s,%s)
        """,(emp_id,month,salary))
        conn.commit()

    cur.execute("""
    SELECT p.*, e.name
    FROM payroll p
    JOIN employees e ON p.employee_id = e.id
    ORDER BY p.id DESC
    """)

    payroll = cur.fetchall()

    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()

    return render_template("dashboards/hr/payroll.html",
                           payroll=payroll,
                           employees=employees)

@app.route("/hr/salary-structure", methods=["POST"])
def salary_structure():

    emp_id = request.form.get("employee_id")
    basic = int(request.form.get("basic"))
    allowance = int(request.form.get("allowance"))
    deduction = int(request.form.get("deduction"))

    net_salary = basic + allowance - deduction

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO payroll (employee_id, month, salary)
    VALUES (%s,%s,%s)
    """,(emp_id,"Current Month",net_salary))

    conn.commit()

    return redirect("/hr/payroll")

@app.route("/hr/email-leave/delete/<int:id>")
def delete_email_leave(id):

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("DELETE FROM hr_email_leaves WHERE id=%s",(id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/hr/leaves")

@app.route("/hr/salary-slip/<int:emp_id>")
def salary_slip(emp_id):

    import psycopg2
    from flask import send_file
    from reportlab.platypus import SimpleDocTemplate, Table
    from reportlab.platypus import TableStyle
    from reportlab.lib import colors
    import os

    # ✅ DATABASE CONNECT YAHI KARNA HAI
    conn = psycopg2.connect(
        database="college_portal",
        user="postgres",
        password="college@123"
    )

    cur = conn.cursor()
    cur.execute("SELECT id, name, department, salary FROM employees WHERE id=%s",(emp_id,))
    emp = cur.fetchone()

    if not emp:
        return "Employee not found"
    print(emp)
    # salary calc
    basic = float(emp[3] or 0)
    hra = basic * 0.20
    bonus = basic * 0.10
    pf = basic * 0.12
    net = basic + hra + bonus - pf

    filename = f"salary_slip_{emp_id}.pdf"
    filepath = os.path.join("static", filename)

    doc = SimpleDocTemplate(filepath)

    data = [
        ["Employee Name", emp[1]],
        ["Department", emp[2]],
        ["Basic Salary", f"₹ {basic}"],
        ["HRA", f"₹ {hra}"],
        ["Bonus", f"₹ {bonus}"],
        ["PF", f"₹ {pf}"],
        ["Net Salary", f"₹ {net}"]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black),
    ]))

    doc.build([table])

    cur.close()
    conn.close()

    return send_file(filepath, as_attachment=True)

@app.route("/hr/attendance")
def hr_attendance():
    return render_template("dashboards/hr/hr_attendance.html")

@app.route("/hr/recruitment")
def hr_recruitment():

    conn = psycopg2.connect(
        database="college_portal",
        user="postgres",
        password="college@123"
    )

    cur = conn.cursor()

    cur.execute("SELECT id,name,position,status FROM recruitment ORDER BY id")

    data = cur.fetchall()

    cur.close()
    conn.close()

    # convert tuple -> dict
    candidates = []

    for d in data:
        candidates.append({
            "id": d[0],
            "name": d[1],
            "position": d[2],
            "status": d[3]
        })

    return render_template("dashboards/hr/hr_recruitement.html", candidates=candidates)

# ==================
# Registrar's Office - Student Records & Graduation Tracking
# ==================

@app.route("/registrar")
def registrar_dashboard():

    # role security
    if session.get("role") != "registrar":
        return redirect("/login")

    return render_template("dashboards/registrar/registrar_dashboard.html")

from flask import jsonify
import psycopg2

@app.route("/registrar/student-search")
def student_search_page():
    return render_template("dashboards/registrar/student_search.html")

from flask import request, jsonify
from psycopg2.extras import RealDictCursor

@app.route("/registrar/search")
def live_student_search():

    if session.get("role") != "registrar":
        return jsonify([])

    q = request.args.get("q","")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            s.id,
            s.username AS name,
            c.class_name AS course
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE LOWER(s.username) LIKE LOWER(%s)
        ORDER BY s.id DESC
        LIMIT 20
    """, (f"%{q}%",))

    students = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(students)

from reportlab.pdfgen import canvas
from flask import send_file
import os

@app.route("/registrar/generate-id/<int:student_id>")
def generate_id_cards(student_id):

    file_path = f"static/idcards/id_{student_id}.pdf"

    c = canvas.Canvas(file_path)

    c.drawString(100,750,"EDUSTACK UNIVERSITY")
    c.drawString(100,720,f"Student ID: {student_id}")
    c.drawString(100,690,"Name: Demo Student")
    c.drawString(100,660,"Course: CSE")

    c.save()

    return send_file(file_path, as_attachment=True)

@app.route("/registrar/generate-certificate/<int:student_id>")
def generate_certificate(student_id):

    file_path = f"static/certificates/cert_{student_id}.pdf"

    c = canvas.Canvas(file_path)

    c.drawString(200,750,"CERTIFICATE OF COMPLETION")
    c.drawString(100,700,"This is to certify that")
    c.drawString(100,670,f"Student ID {student_id}")
    c.drawString(100,640,"has successfully completed the course.")

    c.save()

    return send_file(file_path, as_attachment=True)

import matplotlib.pyplot as plt

@app.route("/registrar/analytics")
def registrar_analytics():

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor()

    # ================= TOTAL STUDENTS =================
    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()[0]

    # ================= TOTAL CLASSES =================
    cur.execute("SELECT COUNT(*) FROM classes")
    total_classes = cur.fetchone()[0]

    # ================= AVG CGPA (FIXED FOR POSTGRESQL) =================
    cur.execute("""
        SELECT COALESCE(ROUND(AVG(cgpa)::numeric,2),0)
        FROM academic_records
    """)
    avg_cgpa = cur.fetchone()[0]

    # ================= TOTAL FACULTY (Dummy for now) =================
    total_faculty = 12

    # ================= STUDENTS PER CLASS (CHART DATA) =================
    cur.execute("""
        SELECT c.class_name, COUNT(*)
        FROM students s
        JOIN classes c ON s.class_id = c.id
        GROUP BY c.class_name
        ORDER BY c.class_name
    """)

    rows = cur.fetchall()

    class_labels = [r[0] for r in rows]
    class_data = [r[1] for r in rows]

    # ================= CGPA CHART (Demo) =================
    cgpa_labels = ["0-6", "6-8", "8-10"]
    cgpa_data = [10, 20, 15]  # demo data

    cur.close()
    conn.close()

    return render_template(
        "dashboards/registrar/analytics.html",
        total_students=total_students,
        total_classes=total_classes,
        avg_cgpa=avg_cgpa,
        total_faculty=total_faculty,
        class_labels=class_labels,
        class_data=class_data,
        cgpa_labels=cgpa_labels,
        cgpa_data=cgpa_data
    )

@app.route("/registrar/student-records", methods=["GET","POST"])
def registrar_students():

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    if request.method == "POST":

        try:
            add_student(
                cur,
                request.form["username"],
                request.form["enrollment_no"],
                request.form["class_id"],
                request.form["password"]
            )

            conn.commit()
            return redirect("/registrar/student-records")

        except Exception as e:
            conn.rollback()
            print("Error:", e)

    cur.execute("""
        SELECT s.*, c.class_name
        FROM students s
        JOIN classes c ON s.class_id = c.id
        ORDER BY s.id DESC
    """)

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/registrar/student_records.html",
        students=students,
        classes=classes
    )

@app.route("/registrar/delete-student/<int:id>", methods=["POST"])
def delete_registrar_student(id):

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor()

    # username fetch
    cur.execute("SELECT username FROM students WHERE id=%s",(id,))
    user = cur.fetchone()

    if user:
        # delete login first
        cur.execute("DELETE FROM users WHERE username=%s",(user[0],))

    # delete student record
    cur.execute("DELETE FROM students WHERE id=%s",(id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/registrar/student-records")

from werkzeug.security import generate_password_hash

def add_student(cur, username, enrollment_no, class_id, password):

    # ===== DUPLICATE CHECK =====
    cur.execute("SELECT id FROM users WHERE username=%s",(username,))
    if cur.fetchone():
        raise Exception("Username already exists")

    cur.execute("SELECT id FROM students WHERE enrollment_no=%s",(enrollment_no,))
    if cur.fetchone():
        raise Exception("Enrollment already exists")

    # ===== PASSWORD HASH =====
    hashed_password = generate_password_hash(password)

    # ===== CREATE LOGIN =====
    cur.execute("""
        INSERT INTO users (username,password,role)
        VALUES (%s,%s,'student')
    """,(username,hashed_password))

    # ===== CREATE STUDENT RECORD =====
    cur.execute("""
        INSERT INTO students
        (username,enrollment_no,class_id)
        VALUES (%s,%s,%s)
    """,(username,enrollment_no,class_id))

@app.route("/registrar/enrollment")
def registrar_enrollment():

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) FROM classes")
    total_classes = cur.fetchone()["count"]

    cur.execute("""
        SELECT s.*, c.class_name
        FROM students s
        JOIN classes c ON s.class_id=c.id
        ORDER BY s.id DESC
        LIMIT 5
    """)

    recent_students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/registrar/enrollment.html",
        total_students=total_students,
        total_classes=total_classes,
        recent_count=len(recent_students),
        recent_students=recent_students
    )

from reportlab.pdfgen import canvas
from datetime import datetime
import os

@app.route("/registrar/certificates", methods=["GET","POST"])
def registrar_certificates():

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # student list
    cur.execute("SELECT id, username FROM students ORDER BY id DESC")
    students = cur.fetchall()

    if request.method == "POST":

        student_id = request.form.get("student_id")
        cert_type = request.form.get("certificate_type")

        # save record
        cur.execute("""
            INSERT INTO certificates(student_id, certificate_type)
            VALUES(%s,%s)
        """,(student_id, cert_type))

        conn.commit()

        # ===== PDF GENERATE =====

        file_path = f"static/certificates/cert_{student_id}.pdf"

        c = canvas.Canvas(file_path)

        c.setFont("Helvetica-Bold",18)
        c.drawString(150,750,"EDUSTACK UNIVERSITY")

        c.setFont("Helvetica",14)
        c.drawString(100,700,"Certificate of Achievement")

        c.drawString(100,660,f"Student ID: {student_id}")
        c.drawString(100,630,f"Type: {cert_type}")
        c.drawString(100,600,f"Issue Date: {datetime.now()}")

        c.save()

    # certificate history
    cur.execute("""
        SELECT c.*, s.username
        FROM certificates c
        JOIN students s ON c.student_id = s.id
        ORDER BY c.id DESC
    """)

    certs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "dashboards/registrar/certificates.html",
        students=students,
        certs=certs
    )

import qrcode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table
from reportlab.lib.units import inch
import os

@app.route("/registrar/id-cards")
def registrar_id_cards():

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM students ORDER BY username")
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("dashboards/registrar/id_cards.html", students=students)


@app.route("/registrar/generate-id/<int:id>")
def generate_id(id):

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM students WHERE id=%s",(id,))
    student = cur.fetchone()

    cur.close()
    conn.close()

    # QR Generate
    qr = qrcode.make(f"http://127.0.0.1:5000/verify/{id}")
    qr_path = f"static/qrs/qr_{id}.png"
    qr.save(qr_path)

    # PDF Generate
    pdf_path = f"static/idcards/id_{id}.pdf"
    doc = SimpleDocTemplate(pdf_path)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>EDUSTACK UNIVERSITY</b>", styles["Title"]))
    elements.append(Spacer(1,12))

    data = [
        ["Name", student["username"]],
        ["Enrollment", student["enrollment_no"]],
        ["Father Name", student.get("father_name","")],
        ["DOB", str(student.get("dob",""))],
        ["Contact", student.get("contact","")]
    ]

    table = Table(data, colWidths=[2*inch,3*inch])
    table.setStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ])

    elements.append(table)
    elements.append(Spacer(1,20))
    elements.append(Image(qr_path,2*inch,2*inch))

    doc.build(elements)

    return redirect(f"/static/idcards/id_{id}.pdf")

from werkzeug.utils import secure_filename

@app.route("/registrar/upload-photo/<int:id>", methods=["POST"])
def upload_student_photo(id):

    if session.get("role") != "registrar":
        return redirect("/login")

    file = request.files.get("photo")

    if file and file.filename != "":

        filename = secure_filename(file.filename)
        path = os.path.join("static/uploads", filename)
        file.save(path)

        conn = get_pg()
        cur = conn.cursor()

        # photo db me save
        cur.execute("""
            UPDATE students
            SET photo=%s
            WHERE id=%s
        """,(filename,id))

        conn.commit()
        cur.close()
        conn.close()

    return redirect("/registrar/id-cards")

@app.route("/registrar/academic-records")
def academic_records():

    if session.get("role") != "registrar":
        return redirect("/login")

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT
                s.username,
                s.enrollment_no,
                c.class_name,
                a.semester,
                a.cgpa
            FROM students s
            JOIN classes c ON s.class_id = c.id
            LEFT JOIN academic_records a
                ON s.id = a.student_id
            ORDER BY s.id DESC
        """)

        records = cur.fetchall()

    except Exception as e:
        print("DB ERROR:", e)
        records = []

    finally:
        cur.close()
        conn.close()

    return render_template(
        "dashboards/registrar/academic_records.html",
        records=records
    )

@app.route("/Undergraduate")
def undergraduate():
    return render_template("academics/undergraduate.html")

@app.route("/Postgraduate")
def postgraduate():
    return render_template("academics/postgraduate.html")

@app.route("/examinations")
def examinations():
    return render_template("academics/examinations.html")

@app.route("/time-table")
def time_table():
    return render_template("academics/time_table.html")

@app.route("/notices")
def notices():
    return render_template("academics/notices.html")

@app.route("/academic-calendar")
def academic_calendar():
    return render_template("academics/academic_calendar.html")

@app.route("/code-of-conduct")
def code_of_conduct():
    return render_template("academics/code_of_conduct.html")

@app.route("/IQAC")
def iqac():
    return render_template("academics/iqac.html")

@app.route("/library")
def library():
    return render_template("academics/library.html")

@app.route("/faculty-staff")
def faculty_staff():
    return render_template("academics/faculty_staff.html")


@app.route("/Timelapse")
def timelapse():
    return render_template("facilities/timelapse.html")

@app.route("/Newsletter")
def newsletter():
    return render_template("facilities/newsletter.html")

@app.route("/Sports")
def sports():
    return render_template("facilities/sports.html")

@app.route("/e-learning")
def e_learning():
    return render_template("facilities/e_learning.html")

@app.route("/chapter-association")
def chapter_association():
    return render_template("facilities/chapter_association.html")

@app.route("/clubs")
def clubs():
    return render_template("facilities/clubs.html")

@app.route("/research-innovation")
def research_innovation():
    return render_template("facilities/research_innovation.html")

@app.route("/transport-facilities")
def transport_facilities():
    return render_template("facilities/transport_facilities.html")

@app.route("/wifi-campus")
def wifi_campus():
    return render_template("facilities/wifi_campus.html")

@app.route("/canteen")
def canteen():
    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM canteen_menu WHERE is_available=TRUE")
    menu = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("facilities/canteen.html", menu=menu)


@app.route("/place-order", methods=["POST"])
def place_order():
    conn = get_pg()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(MAX(token_number),0)+1 FROM canteen_orders")
    token = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO canteen_orders(student_name,item_name,token_number)
        VALUES (%s,%s,%s)
    """,(request.form["student_name"],request.form["item_name"],token))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/canteen")


@app.route("/token-display")
def token_display():
    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM canteen_orders ORDER BY token_number DESC LIMIT 10")
    orders = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("token_display.html", orders=orders)


@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    conn = get_pg()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO canteen_feedback(student_name,rating,message)
        VALUES (%s,%s,%s)
    """,(request.form["student_name"],request.form["rating"],request.form["message"]))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/canteen")

from flask import render_template, request, redirect
from psycopg2.extras import RealDictCursor

@app.route("/admin-canteen")
def admin_canteen():
    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM canteen_menu ORDER BY id DESC")
    menu = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin_canteen.html", menu=menu)

@app.route("/add-menu-item", methods=["POST"])
def add_menu_item():
    item_name = request.form.get("item_name")
    price = request.form.get("price")

    if not item_name or not price:
        return redirect("/admin-canteen")

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO canteen_menu (item_name, price)
        VALUES (%s, %s)
    """, (item_name, price))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/admin-canteen")

@app.route("/canteen-dashboard")
def canteen_dashboard():

    conn = get_pg()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM orders
        WHERE status='pending'
        ORDER BY id DESC
    """)

    orders = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("canteen_dashboard.html", orders=orders)

@app.route("/mark-ready", methods=["POST"])
def mark_ready():

    order_id = request.form.get("id")

    conn = get_pg()
    cur = conn.cursor()

    cur.execute("UPDATE orders SET status='ready' WHERE id=%s", (order_id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/canteen-dashboard")
import qrcode

img = qrcode.make("http://yourdomain.com/canteen")
img.save("static/qr_canteen.png")

@app.route('/cse')
def cse():
    return render_template('courses/cse.html')

@app.route('/it')
def it():
    return render_template('courses/it.html')

@app.route('/ece')
def ece():
    return render_template('courses/ece.html')

@app.route('/mech')
def mech():
    return render_template('courses/mech.html')

@app.route('/civil')
def civil():
    return render_template('courses/civil.html')

@app.route('/management')
def management():
    return render_template('courses/management.html')

# ======================
# Department Routes
# ======================
# =========================
# DEPARTMENT ROUTES
# =========================

# CSE
@app.route("/computer")
def computer():
    return render_template("homepage/computer.html")


# IT
@app.route("/information")
def information():
    return render_template("homepage/information.html")


# ECE
@app.route("/electronics")
def electronics():
    return render_template("homepage/electronics.html")


# Mechanical
@app.route("/mechanical")
def mechanical():
    return render_template("homepage/mechanical.html")


# Civil
@app.route("/civileng")
def civileng():
    return render_template("homepage/civileng.html")


# Management
@app.route("/manage")
def manage():
    return render_template("homepage/manage.html")

# ======================
# FOOTER ROUTES
# ======================

@app.route("/alumni")
def alumni():
    return render_template("footer/alumni.html")

@app.route("/vidya-lakshmi")
def vidya_lakshmi():
    return render_template("footer/vidya_lakshmi.html")

@app.route("/pragati")
def pragati():
    return render_template("footer/pragati.html")

@app.route("/grievances")
def grievances():
    return render_template("footer/grievances.html")

@app.route("/nptel")
def nptel():
    return render_template("footer/nptel.html")

@app.route("/student-registration")
def student_registration():
    return render_template("footer/student_registration.html")

@app.route("/news")
def news():
    return render_template("footer/news.html")

@app.route("/career")
def career():
    return render_template("footer/career.html")

# IMPORTANT LINKS

@app.route("/rgpv")
def rgpv():
    return render_template("footer/rgpv.html")

@app.route("/aicte")
def aicte():
    return render_template("footer/aicte.html")

@app.route("/mp-scholarship")
def mp_scholarship():
    return render_template("footer/mp_scholarship.html")

@app.route("/mp-dte")
def mp_dte():
    return render_template("footer/mp_dte.html")

@app.route("/anti-ragging")
def anti_ragging():
    return render_template("footer/anti_ragging.html")

@app.route("/feedback")
def feedback():
    return render_template("footer/feedback.html")

@app.route("/privacy-policy")
def privacy():
    return render_template("footer/privacy.html")

# DOWNLOAD

@app.route("/brochure")
def brochure():
    return render_template("footer/brochure.html")

@app.route("/bus-route")
def bus_route():
    return render_template("footer/bus_route.html")


from university_ai import ask_ai
from flask import request, jsonify

from university_ai import ask_ai

@app.route("/chatbot", methods=["POST"])
def chatbot():

    data = request.get_json()

    message = data.get("message")

    try:

        reply = ask_ai(message)

        return jsonify({"reply": reply})

    except Exception as e:

        print("AI ERROR:", e)

        return jsonify({
            "reply": "Sorry, AI is temporarily unavailable."
        })
    
# ======================
# ACCOUNTS MODULE
# ======================

@app.route("/fee-management")
def fee_management():

    if session.get("role") != "accounts":
        return redirect("/login")

    return render_template("accounts/fee_management.html")


@app.route("/receipts")
def receipts():

    if session.get("role") != "accounts":
        return redirect("/login")

    return render_template("accounts/receipts.html")


@app.route("/reports")
def reports():

    if session.get("role") != "accounts":
        return redirect("/login")

    return render_template("accounts/reports.html")


@app.route("/pending")
def pending():

    if session.get("role") != "accounts":
        return redirect("/login")

    return render_template("accounts/pending.html")


@app.route("/ledger")
def ledger():

    if session.get("role") != "accounts":
        return redirect("/login")

    return render_template("accounts/ledger.html")
# ==================
# RUN
# ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

