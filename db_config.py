from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

db = SQLAlchemy()

def get_db_uri():
    user = os.getenv('DB_USER')
    password = os.getenv('')
    host = os.getenv('DB_HOST')
    dbname = os.getenv('DB_NAME')

    if password:
        return f"mysql+pymysql://{user}:{password}@{host}/{dbname}"
    else:
        return f"mysql+pymysql://{user}@{host}/{dbname}"

def init_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from models.user import User

print("DB URI:", get_db_uri())
