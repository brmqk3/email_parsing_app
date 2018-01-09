from flask import render_template, request, redirect, url_for
from werkzeug import secure_filename
from app import app

import os
import re
import sqlite3
import tarfile

# Regex for each email field
TO_REGEX = r"(?:^To:.*?)([a-zA-Z0-9\.\-_\+]+@[a-zA-Z0-9\.\-_\+]+)>?"
FROM_REGEX = r"(?:^From:.*?)([a-zA-Z0-9\.\-_\+]+@[a-zA-Z0-9\.\-_\+]+)>?"
DATE_REGEX = r"(?:^Date:[ ]*)(.*)"
SUBJECT_REGEX = r"(?:^Subject:[ ]*)(.*)"
MESSAGE_ID_REGEX = r"(?:^Message-ID:[ ]*)(.*)"

# Name of database
DB = 'email.db'

# Sqlite string to insert email into database
insert_email = '''INSERT INTO email(to_address,from_address,date,subject,message_id)
                  VALUES(?,?,?,?,?)'''


@app.route('/')
def index():
    return render_template("index.html")
    
@app.route('/form')
def email_form():
    return render_template("upload_email.html")

# Unzips the archive, parses the .msg files for relevant fields, and saves them to the database.
@app.route('/form/submit', methods=['GET', 'POST'])
def submit_email_form():
    if request.method == 'POST':
        error_string = ""
        # Get and save file from email form
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Ensure tar file is actually a compressed archive, doesn't just have the extension
        try:
            tarfile_obj = tarfile.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        except tarfile.TarError:
            error_string = 'Failed to open tarfile, possibly corrupted'
            app.logger.info(error_string)
            # Return error page since this is a major failure
            return render_template("error.html", data=error_string)

        for member in tarfile_obj.getmembers():
            # Ensure all emails are of the .msg format
            if member.name.endswith('.msg'):
                text = tarfile_obj.extractfile(member)
                email_to = email_parser(text, TO_REGEX)
                email_from = email_parser(text, FROM_REGEX)
                email_date = email_parser(text, DATE_REGEX)
                email_subject = email_parser(text, SUBJECT_REGEX)
                email_message_id = email_parser(text, MESSAGE_ID_REGEX)
                store_email(email_to, email_from, email_date, email_subject, email_message_id, member.name)
            else:
                error_string = "File in archive %s not of type .msg" % member.name
                app.logger.info(error_string)

        return redirect(url_for('email_table'))

# Displays all the emails currently in the database
@app.route('/email')
def email_table():
    data = get_email()
    return render_template("view_email.html", data=data)

# Gets all emails from database
def get_email():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM email")
    all_email = cur.fetchall()
    return all_email

# Inserts emails into the database
def store_email(email_to, email_from, email_date, email_subject, email_message_id, file_name):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute(insert_email, (email_to, email_from, email_date, email_subject, email_message_id))
    except sqlite3.IntegrityError:
        # Since message id is primary key, we want it to be unique
        if email_message_id:
            app.logger.info("Entry already exists with the Message-ID:%s" % email_message_id)
        # Since message id is primary key, we want it to exist
        else:
            app.logger.info("File %s does not contain Message-ID field" % file_name)
        return
    conn.commit()
    
def create_connection():
    conn = sqlite3.connect(DB)
    return conn

# Searches each line of email text for the regex provided
def email_parser(content, regex):
    match = None
    for line in content.readlines():
        match = re.search(regex, line)
        if match:
            match = match.group(1)
            break;

    content.seek(0)
    return match
