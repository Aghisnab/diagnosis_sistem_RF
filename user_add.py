# init_user.py
from models.user import User
from db_config import db, init_app
from werkzeug.security import generate_password_hash
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'  # atau sesuaikan dengan config
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'

init_app(app)

with app.app_context():
    db.create_all()  # pastikan tabel dibuat

    # Tambahkan user admin
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123', method='pbkdf2:sha256'),
            role='admin',
            profesi='Admin'
        )
        db.session.add(admin_user)
        print("User admin berhasil ditambahkan.")
    else:
        print("User admin sudah ada.")

    # Tambahkan user biasa
    if not User.query.filter_by(username='user').first():
        normal_user = User(
            username='user',
            password=generate_password_hash('user123', method='pbkdf2:sha256'),
            role='user',
            profesi='Karyawan'
        )
        db.session.add(normal_user)
        print("User biasa berhasil ditambahkan.")
    else:
        print("User biasa sudah ada.")

    # Simpan perubahan ke database
    db.session.commit()
