from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from models.user import User, RoleEnum

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login berhasil!", "success")

            # Alihkan sesuai role
            if user.role == RoleEnum.ADMIN:
                return redirect(url_for('admin_dashboard'))
            elif user.role == RoleEnum.DOKTER:
                return redirect(url_for('dokter_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Login gagal. Periksa kembali username/password.", "danger")
        
                # Debugging
        if user:
            print("Password input:", password)
            print("Password hash DB:", user.password)
            print("Check password result:", user.check_password(password))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')  # BUKAN 'success'
    return redirect(url_for('auth.login'))
