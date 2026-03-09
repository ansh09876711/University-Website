import imaplib
import email
from email.utils import parseaddr
from datetime import datetime
import psycopg2
import os
import re
from dateutil import parser as dateparser

EMAIL = "collegeportal52@gmail.com"
PASSWORD = "gmwdsbpfbhjwqvph"

UPLOAD_FOLDER = "static/uploads/leaves"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_dates(text):

    patterns = re.findall(
        r'\d{4}-\d{2}-\d{2}|'
        r'\d{2}-\d{2}-\d{4}|'
        r'\d{2}/\d{2}/\d{4}|'
        r'\d{1,2}\s+[A-Za-z]+\s+\d{4}|'
        r'[A-Za-z]+\s+\d{1,2},?\s+\d{4}',
        text
    )

    results = []

    for p in patterns:
        try:
            results.append(dateparser.parse(p, dayfirst=True).date())
        except:
            pass

    return results


def check_new_emails():

    print("Checking emails...")

    try:
        conn = psycopg2.connect(
            database="college_portal",
            user="postgres",
            password="college@123"
        )
        cur = conn.cursor()

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')

        for num in messages[0].split():

            status, msg_data = mail.fetch(num, "(RFC822)")

            for response in msg_data:

                if isinstance(response, tuple):

                    msg = email.message_from_bytes(response[1])

                    subject = msg["Subject"] or "Leave Application"
                    sender_name, sender_email = parseaddr(msg.get("From"))

                    # ================= BODY =================

                    body = ""

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    # ================= NAME =================

                    teacher_name = sender_name

                    for line in body.split("\n"):
                        if "name:" in line.lower():
                            teacher_name = line.split(":")[-1].strip()

                    # ================= AI SMART PARSING =================

                    leave_from = None
                    leave_to = None
                    reason = None

                    dates = extract_dates(body)

                    if len(dates) >= 1:
                        leave_from = dates[0]

                    if len(dates) >= 2:
                        leave_to = dates[1]

                    # Reason = full paragraph except date lines
                    reason = body.strip()

                    # ================= ATTACHMENT =================

                    file_path = None

                    if msg.is_multipart():
                        for part in msg.walk():

                            if part.get_content_disposition() == "attachment":

                                filename = part.get_filename()

                                if filename:
                                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))

                                    file_path = filepath

                    # ================= INSERT =================

                    cur.execute("""
                        INSERT INTO hr_email_leaves
                        (teacher_name, teacher_email, subject,
                         leave_from, leave_to, reason, file_path, status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')
                        ON CONFLICT (teacher_email, leave_from, leave_to)
                        DO NOTHING
                    """,(
                        teacher_name,
                        sender_email,
                        subject,
                        leave_from,
                        leave_to,
                        reason,
                        file_path
                    ))

        conn.commit()
        mail.logout()
        cur.close()
        conn.close()

        print("Mail check done ✅")

    except Exception as e:
        print("Mail service error:", e)