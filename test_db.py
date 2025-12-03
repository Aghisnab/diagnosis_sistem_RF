from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/diagnosis_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from sqlalchemy import text

try:
    with app.app_context():
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connected:", result.fetchone())
except Exception as e:
    print("Error connecting to database:", e)

