from flask import Flask, render_template, redirect, url_for, request, flash, make_response
import json
from flask_login import LoginManager, current_user, login_required
from functools import wraps
from dotenv import load_dotenv
import os
from datetime import datetime
from auth import auth_bp
from db_config import init_app, db
from sqlalchemy import or_, func
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length
from xhtml2pdf import pisa
import io

from models.penyakit import Penyakit
from models.riwayat_diagnosis import db, RiwayatDiagnosis
from models.diagnosis import predict_disease

# Load environment variables
load_dotenv()

# Inisialisasi Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'fallback_secret_key'

# Inisialisasi SQLAlchemy melalui modul terpusat
init_app(app)

# Register Blueprint
app.register_blueprint(auth_bp)

# Inisialisasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Decorator admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('auth.login'))
        if current_user.role != RoleEnum.ADMIN:
            flash("Akses ditolak: Anda bukan admin.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Load Model User dan RoleEnum
from models.user import User, RoleEnum

@login_manager.user_loader
def load_user(id_user):
    return User.get_by_id(int(id_user))

# Route utama
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

#ADD USER
class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    profession = StringField('Profesi')
    role = SelectField('Role', choices=[('user', 'Pengguna'), ('admin', 'Administrator')], validators=[DataRequired()])
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AddUserForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        profession = form.profession.data
        role = form.role.data

        # Simpan user baru
        user = User(username=username, profesi=profession, role=role)
        user.set_password(password)
        user.save()

        flash('Pengguna berhasil ditambahkan!', 'success')
        return redirect(url_for('users'))

    return render_template('add_user.html', form=form)

#UPDATE USER
@app.route('/edit_user/<int:id_user>', methods=['GET'])
@login_required
@admin_required
def edit_user(id_user):
    user = User.query.get_or_404(id_user)
    form = AddUserForm()
    return render_template('edit_user.html', user=user, form=form)
@app.route('/update_user/<int:id_user>', methods=['POST'])
@login_required
@admin_required
def update_user(id_user):
    user = User.query.get_or_404(id_user)
    form = AddUserForm()

    user.username = request.form['username']
    user.profesi = request.form['profession']
    user.role = request.form['role']

    password = request.form.get('password')
    if password:
        user.set_password(password)

    db.session.commit()
    flash('Data pengguna berhasil diperbarui!', 'success')
    
    return redirect(url_for('users'))
