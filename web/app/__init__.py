from flask import Flask

# Initialize the app
app = Flask(__name__, instance_relative_config=True)

# Load the views
from app import views

# Load the config file
app.config.from_object('config')

# Instantiate the database
import sqlite3

database = 'email.db'

# In this implementation, Message-ID is unique, and therefore primary key and not null.
create_email_table = """ CREATE TABLE IF NOT EXISTS email (
                            to_address text,
                            from_address text,
                            date text,
                            subject text,
                            message_id text PRIMARY KEY UNIQUE NOT NULL
                        ); """
                        
try:
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(create_email_table)
except Error as e:
    print(e)
finally:
    conn.close()
 