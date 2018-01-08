from flask import render_template, request
from werkzeug import secure_filename
from app import app

import os
import re
import sqlite3
import tarfile
import email

TO_REGEX = r"(?:^To:.*?)([a-zA-Z0-9\.\-_\+]+@[a-zA-Z0-9\.\-_\+]+)>?"
FROM_REGEX = r"(?:^From:.*?)([a-zA-Z0-9\.\-_\+]+@[a-zA-Z0-9\.\-_\+]+)>?"
DATE_REGEX = r"(?:^Date:[ ]*)(.*)"
SUBJECT_REGEX = r"(?:^Subject:[ ]*)(.*)"
MESSAGE_ID_REGEX = r"(?:^Message-ID:[ ]*)(.*)"
DB = 'email.db'
insert_email = '''INSERT INTO email(to_address,from_address,date,subject,message_id)
                  VALUES(?,?,?,?,?)'''


@app.route('/')
def index():
    return render_template("index.html")
    
@app.route('/form')
def email_form():
    return render_template("upload_email.html")
    
@app.route('/form/submit', methods=['GET', 'POST'])
def submit_email_form():
    if request.method == 'POST':
      file = request.files['file']
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      tarfile_obj = tarfile.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      email_array = []
      for member in tarfile_obj.getmembers():
        text = tarfile_obj.extractfile(member)
        email_to = email_parser(text, TO_REGEX)
        email_array.append(email_to)
        email_from = email_parser(text, FROM_REGEX)
        email_array.append(email_from)
        email_date = email_parser(text, DATE_REGEX)
        email_array.append(email_date)
        email_subject = email_parser(text, SUBJECT_REGEX)
        email_array.append(email_subject)
        email_message_id = email_parser(text, MESSAGE_ID_REGEX)
        email_array.append(email_message_id)
        store_email(email_to, email_from, email_date, email_subject, email_message_id)
      return 'file submitted successfully'

@app.route('/email')
def email_table():
    data = get_email()
    return render_template("view_email.html", data=data)

def get_email():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM email")
    all_email = cur.fetchall()
    return all_email

def store_email(email_to, email_from, email_date, email_subject, email_message_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute(insert_email, (email_to, email_from, email_date, email_subject, email_message_id))
    conn.commit()
    
def create_connection():
    conn = sqlite3.connect(DB)
    return conn
    
def email_parser(content, regex):
    for line in content.readlines():
        match = re.search(regex, line)
        if match:
            content.seek(0)
            return match.group(1)
