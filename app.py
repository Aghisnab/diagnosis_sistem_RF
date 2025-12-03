from flask import Flask, render_template, redirect, url_for, request, flash, make_response
import json
from flask_login import LoginManager, current_user, login_required
from functools import wraps
from dotenv import load_dotenv
import os
from datetime import datetime
from auth import auth_bp
from db_config import init_app, db
from sqlalchemy import or_, func, extract
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length
from xhtml2pdf import pisa
import io
import ast

from models.penyakit import Penyakit
from models.riwayat_diagnosis import db, RiwayatDiagnosis
from models.diagnosis import predict_disease
from collections import Counter

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

# ================= DECORATOR ADMIN =================
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


# ================= DECORATOR DOKTER =================
def dokter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('auth.login'))
        if current_user.role != RoleEnum.DOKTER:
            flash("Akses ditolak: Anda bukan dokter.", "danger")
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


def id_to_nama_gejala(ids):
    id_to_nama = {
        '1': 'nyeri ulu hati',
        '2': 'batuk',
        '3': 'nyeri dada tajam',
        '4': 'sakit kepala',
        '5': 'batuk dahak',
        '6': 'sakit tenggorokan',
        '7': 'kelelahan',
        '8': 'regurgitasi',
        '9': 'mual',
        '10': 'diare',
        '11': 'nafsu makan menurun',
        '12': 'dada terasa berat',
        '13': 'perut kembung',
        '14': 'mengi',
        '15': 'menggigil',
        '16': 'demam',
        '17': 'pilek',
        '18': 'muntah',
        '19': 'nyeri perut tajam',
        '20': 'nyeri perut kram',
        '21': 'bersin',
        '22': 'sesak napas',
        '23': 'nyeri perut terbakar',
        '24': 'hidung tersumbat',
        '25': 'nyeri seluruh tubuh'
    }
    return [id_to_nama.get(str(i).strip(), f"ID {i}") for i in ids if i]
######################### ROUTE DASHBOARD #########################

# Route dashboard untuk redirect sesuai role
@app.route('/dashboard')
@login_required
def dashboard():
    print("=== DEBUG USER DASHBOARD ===")
    print("Authenticated:", current_user.is_authenticated)
    print("Username:", current_user.username)
    print("Role:", current_user.role)
    print("Profesi:", current_user.profesi)
    if current_user.role == RoleEnum.ADMIN:
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == RoleEnum.DOKTER:
        return redirect(url_for('dokter_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

# Admin dashboard
@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    # Statistik umum
    total_users = User.query.count()
    total_diagnosis = RiwayatDiagnosis.query.count()
    total_penyakit = Penyakit.query.count()
    total_gejala = Gejala.query.count()

    # Pie Chart: Distribusi Penyakit
    penyakit_data = db.session.query(
        Penyakit.nama_penyakit,
        func.count(RiwayatDiagnosis.id_riwayat)
    ).join(RiwayatDiagnosis).group_by(Penyakit.nama_penyakit).all()
    chart_penyakit_labels = [row[0] for row in penyakit_data]
    chart_penyakit_values = [row[1] for row in penyakit_data]

    # Pie Chart: Distribusi Gejala dari gejala_dipilih (ID)
    semua_gejala = RiwayatDiagnosis.query.with_entities(RiwayatDiagnosis.gejala_dipilih).all()
    counter = Counter()

    for row in semua_gejala:
        try:
            # ✅ Gunakan ast.literal_eval karena data bukan JSON murni
            id_list = ast.literal_eval(row.gejala_dipilih)
            nama_list = id_to_nama_gejala(id_list)
            counter.update(nama_list)
        except Exception as e:
            print("Gagal membaca gejala:", e)
            continue

    gejala_teratas = counter.most_common(6)
    chart_gejala_labels = [item[0] for item in gejala_teratas]
    chart_gejala_values = [item[1] for item in gejala_teratas]

    # Bar Chart: Diagnosis per Bulan
    bulan_data = db.session.query(
        extract('month', RiwayatDiagnosis.tanggal_diagnosis),
        func.count(RiwayatDiagnosis.id_riwayat)
    ).group_by(extract('month', RiwayatDiagnosis.tanggal_diagnosis))\
     .order_by(extract('month', RiwayatDiagnosis.tanggal_diagnosis)).all()

    nama_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    chart_bulan_labels = [nama_bulan[int(item[0]) - 1] for item in bulan_data]
    chart_bulan_values = [item[1] for item in bulan_data]

    # Aktivitas Terbaru (5 diagnosis terakhir)
    aktivitas_q = RiwayatDiagnosis.query.order_by(RiwayatDiagnosis.tanggal_diagnosis.desc()).limit(5).all()
    aktivitas_terbaru = [{
        "user": item.pengguna.username,
        "penyakit": item.penyakit.nama_penyakit,
        "tanggal": item.tanggal_diagnosis.strftime("%d %B %Y")
    } for item in aktivitas_q]

    return render_template(
        'dashboard_admin.html',
        total_users=total_users,
        total_diagnosis=total_diagnosis,
        total_penyakit=total_penyakit,
        total_gejala=total_gejala,
        chart_penyakit_labels=chart_penyakit_labels,
        chart_penyakit_values=chart_penyakit_values,
        chart_gejala_labels=chart_gejala_labels,
        chart_gejala_values=chart_gejala_values,
        chart_bulan_labels=chart_bulan_labels,
        chart_bulan_values=chart_bulan_values,
        aktivitas_terbaru=aktivitas_terbaru
    )

# Dokter dashboard
@app.route('/dashboard/dokter')
@login_required
def dokter_dashboard():
    # Statistik umum
    total_users = User.query.count()
    total_diagnosis = RiwayatDiagnosis.query.count()
    total_penyakit = Penyakit.query.count()
    total_gejala = Gejala.query.count()

    # Pie Chart: Distribusi Penyakit
    penyakit_data = db.session.query(
        Penyakit.nama_penyakit,
        func.count(RiwayatDiagnosis.id_riwayat)
    ).join(RiwayatDiagnosis).group_by(Penyakit.nama_penyakit).all()
    chart_penyakit_labels = [row[0] for row in penyakit_data]
    chart_penyakit_values = [row[1] for row in penyakit_data]

    # Pie Chart: Distribusi Gejala dari gejala_dipilih (ID)
    semua_gejala = RiwayatDiagnosis.query.with_entities(RiwayatDiagnosis.gejala_dipilih).all()
    counter = Counter()

    for row in semua_gejala:
        try:
            id_list = ast.literal_eval(row.gejala_dipilih)  # ✅ bukan JSON murni
            nama_list = id_to_nama_gejala(id_list)
            counter.update(nama_list)
        except Exception as e:
            print("Gagal membaca gejala:", e)
            continue

    gejala_teratas = counter.most_common(6)
    chart_gejala_labels = [item[0] for item in gejala_teratas]
    chart_gejala_values = [item[1] for item in gejala_teratas]

    # Bar Chart: Diagnosis per Bulan
    bulan_data = db.session.query(
        extract('month', RiwayatDiagnosis.tanggal_diagnosis),
        func.count(RiwayatDiagnosis.id_riwayat)
    ).group_by(extract('month', RiwayatDiagnosis.tanggal_diagnosis))\
     .order_by(extract('month', RiwayatDiagnosis.tanggal_diagnosis)).all()

    nama_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    chart_bulan_labels = [nama_bulan[int(item[0]) - 1] for item in bulan_data]
    chart_bulan_values = [item[1] for item in bulan_data]

    # Aktivitas Terbaru (5 diagnosis terakhir)
    aktivitas_q = RiwayatDiagnosis.query.order_by(RiwayatDiagnosis.tanggal_diagnosis.desc()).limit(5).all()
    aktivitas_terbaru = [{
        "user": item.pengguna.username,
        "penyakit": item.penyakit.nama_penyakit,
        "tanggal": item.tanggal_diagnosis.strftime("%d %B %Y")
    } for item in aktivitas_q]

    return render_template(
        'dashboard_dokter.html',  # ✅ file template khusus dokter
        total_users=total_users,
        total_diagnosis=total_diagnosis,
        total_penyakit=total_penyakit,
        total_gejala=total_gejala,
        chart_penyakit_labels=chart_penyakit_labels,
        chart_penyakit_values=chart_penyakit_values,
        chart_gejala_labels=chart_gejala_labels,
        chart_gejala_values=chart_gejala_values,
        chart_bulan_labels=chart_bulan_labels,
        chart_bulan_values=chart_bulan_values,
        aktivitas_terbaru=aktivitas_terbaru
    )

# User dashboard
@app.route('/dashboard/user')
@login_required
def user_dashboard():
    penyakit_list = Penyakit.query.all()
    user_id = current_user.id_user

    # Statistik dasar
    total_diagnosis = RiwayatDiagnosis.query.filter_by(user_id=user_id).count()

    penyakit_terbanyak = db.session.query(
        RiwayatDiagnosis.penyakit_id,
        func.count(RiwayatDiagnosis.penyakit_id).label("jumlah")
    ).filter_by(user_id=user_id).group_by(RiwayatDiagnosis.penyakit_id)\
     .order_by(func.count(RiwayatDiagnosis.penyakit_id).desc()).first()

    if penyakit_terbanyak:
        penyakit_obj = Penyakit.query.get(penyakit_terbanyak.penyakit_id)
        nama_terbanyak = penyakit_obj.nama_penyakit
        jumlah_terbanyak = penyakit_terbanyak.jumlah
    else:
        nama_terbanyak = "-"
        jumlah_terbanyak = 0

    terakhir = RiwayatDiagnosis.query.filter_by(user_id=user_id)\
        .order_by(RiwayatDiagnosis.tanggal_diagnosis.desc()).first()
    tanggal_terakhir = terakhir.tanggal_diagnosis.strftime("%d %B %Y") if terakhir else "-"

    # Data chart
    chart_data = db.session.query(
        Penyakit.nama_penyakit,
        func.count(RiwayatDiagnosis.id_riwayat)
    ).join(RiwayatDiagnosis, Penyakit.id_penyakit == RiwayatDiagnosis.penyakit_id)\
     .filter(RiwayatDiagnosis.user_id == user_id)\
     .group_by(Penyakit.nama_penyakit).all()

    chart_labels = [row[0] for row in chart_data]
    chart_values = [row[1] for row in chart_data]

    return render_template(
        'dashboard_user.html',
        penyakit_list=penyakit_list,
        total_diagnosis=total_diagnosis,
        nama_terbanyak=nama_terbanyak,
        jumlah_terbanyak=jumlah_terbanyak,
        tanggal_terakhir=tanggal_terakhir,
        chart_labels=chart_labels,
        chart_values=chart_values
    )

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        file = request.files.get('photo')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/uploads', filename)
            file.save(file_path)

            # Simpan hanya relative path tanpa 'static/'
            current_user.photo = f"uploads/{filename}"
            current_user.update()

            flash("Foto profil berhasil diperbarui.", "success")
        else:
            flash("Tidak ada file yang diunggah.", "warning")

        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=current_user)

######################### ROUTE CRUD PENGGUNA #########################

#LIST USER
@app.route('/users')
@login_required
def users():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = User.query
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.profesi.ilike(f'%{search}%')
            )
        )

    pagination = query.paginate(page=page, per_page=10)
    users = pagination.items
    return render_template('users.html', users=users, pagination=pagination)

#DELETE USER
@app.route('/delete_user/<int:id_user>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(id_user):
    user = User.get_by_id(id_user)
    if not user:
        flash("User tidak ditemukan.", "danger")
        return redirect(url_for('users'))

    if user.id == current_user.id:
        flash("Tidak bisa menghapus akun Anda sendiri.", "danger")
        return redirect(url_for('users'))

    user.delete()
    flash("User berhasil dihapus.", "success")
    return redirect(url_for('users'))

# TAMBAH USER via MODAL
@app.route('/add_user_modal', methods=['POST'])
@login_required
@admin_required
def add_user_modal():
    username = request.form.get('username')
    password = request.form.get('password')
    profession = request.form.get('profession')
    role = request.form.get('role')

    if not username or not password:
        flash("Username dan password wajib diisi.", "warning")
        return redirect(url_for('users'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Username sudah digunakan.", "danger")
        return redirect(url_for('users'))

    user = User(username=username, profesi=profession, role=role)
    user.set_password(password)
    user.save()

    flash("Pengguna berhasil ditambahkan!", "success")
    return redirect(url_for('users'))

# EDIT USER via MODAL
@app.route('/update_user_modal', methods=['POST'])
@login_required
@admin_required
def update_user_modal():
    id_user = request.form.get('id_user')
    user = User.get_by_id(id_user)

    if not user:
        flash("Pengguna tidak ditemukan.", "danger")
        return redirect(url_for('users'))

    user.username = request.form.get('username')
    user.profesi = request.form.get('profession')
    user.role = request.form.get('role')

    password = request.form.get('password')
    if password:
        user.set_password(password)

    user.update()
    flash("Data pengguna berhasil diperbarui!", "success")
    return redirect(url_for('users'))


######################### ROUTE CRUD GEJALA #########################
from models.gejala import Gejala

#LIST GEJALA
@app.route('/gejala')
@login_required
def gejala():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = Gejala.query
    if search:
        query = query.filter(Gejala.gejala.ilike(f"%{search}%"))

    pagination = query.paginate(page=page, per_page=10)
    gejalas = pagination.items
    return render_template('gejala.html', gejalas=gejalas, pagination=pagination)

#EDIT GEJALA
@app.route('/update_gejala', methods=['POST'])
@login_required
@dokter_required
def update_gejala():
    id_gejala = request.form.get('id_gejala')
    nama_gejala = request.form.get('gejala')

    if not id_gejala or not nama_gejala:
        flash("Data tidak lengkap.", "warning")
        return redirect(url_for('gejala'))

    gejala = Gejala.get_by_id(int(id_gejala))
    if not gejala:
        flash("Gejala tidak ditemukan.", "danger")
        return redirect(url_for('gejala'))

    gejala.gejala = nama_gejala
    gejala.update()
    flash("Gejala berhasil diperbarui.", "success")
    return redirect(url_for('gejala'))


######################### ROUTE CRUD PENYAKIT #########################
from models.penyakit import Penyakit

# LIST PENYAKIT
@app.route('/penyakit')
@login_required
def penyakit():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = Penyakit.query
    if search:
        query = query.filter(
            or_(
                Penyakit.nama_penyakit.ilike(f"%{search}%"),
                Penyakit.penyebab.ilike(f"%{search}%"),
                Penyakit.definisi_penyakit.ilike(f"%{search}%"),
                Penyakit.penanganan.ilike(f"%{search}%")
            )
        )

    pagination = query.paginate(page=page, per_page=3)
    daftar_penyakit = pagination.items
    return render_template('penyakit.html', daftar_penyakit=daftar_penyakit, pagination=pagination)

# EDIT PENYAKIT
@app.route('/update_penyakit', methods=['POST'])
@login_required
@dokter_required
def update_penyakit():
    id_penyakit = request.form.get('id_penyakit')
    nama_penyakit = request.form.get('nama_penyakit')
    definisi = request.form.get('definisi_penyakit')
    penyebab = request.form.get('penyebab')
    penanganan = request.form.get('penanganan')

    penyakit = Penyakit.get_by_id(id_penyakit)
    if penyakit:
        penyakit.nama_penyakit = nama_penyakit
        penyakit.definisi_penyakit = definisi
        penyakit.penyebab = penyebab
        penyakit.penanganan = penanganan
        penyakit.update()
        flash("Penyakit berhasil diperbarui.", "success")
    else:
        flash("Data penyakit tidak ditemukan.", "danger")

    return redirect(url_for('penyakit'))


######################### ROUTE DIAGNOSIS #########################
import re
def parse_catatan(catatan):
    # Suhu: float satu angka di belakang koma, contoh: 36.5
    suhu = re.search(r"Suhu:\s*([0-9]+\.[0-9])\b", catatan)

    # Tensi: 2 angka dipisahkan oleh slash, contoh: 120/80
    tensi = re.search(r"Tensi:\s*(\d{2,3}/\d{2,3})\b", catatan)

    # Berat Badan: angka (boleh float atau int)
    berat = re.search(r"Berat Badan:\s*(\d+(\.\d+)?)\b", catatan)
    
    keluhan_match = re.search(
        r"(?:Keluhan|Keterangan):\s*(.*?)(?=\n\S+:|$)",
        catatan,
        re.DOTALL | re.IGNORECASE
    )

    nadi = re.search(r"Nadi:\s*([^\n\r]+)", catatan)
    saturasi = re.search(r"Saturasi:\s*([^\n\r]+)", catatan)

    diagnosis_match = re.search(
        r"Diagnosis Akhir:\s*(.*)", 
        catatan,
        re.DOTALL | re.IGNORECASE
    )

    return {
        "suhu": suhu.group(1).strip() if suhu else "-",
        "tensi": tensi.group(1).strip() if tensi else "-",
        "berat": berat.group(1).strip() if berat else "-",
        "keluhan": keluhan_match.group(1).strip() if keluhan_match else "-",
        "nadi": nadi.group(1).strip() if nadi else "-",
        "saturasi": saturasi.group(1).strip() if saturasi else "-",
        "diagnosis": diagnosis_match.group(1).strip() if diagnosis_match else "-"
    }

@app.route('/diagnosis', methods=['GET', 'POST'])
@login_required
def diagnosis():
    gejalas = Gejala.query.all()
    daftar_gejala = [{'id': g.id_gejala, 'nama': g.gejala} for g in gejalas]

    if request.method == 'POST':
        nama_pasien = request.form['nama']
        umur = int(request.form['umur'])
        gejala_dipilih = request.form.getlist('gejala')

        # === Validasi Umur ===
        umur_raw = request.form.get('umur', '').strip()
        try:
            umur = int(umur_raw)
        except ValueError:
            flash('Umur harus berupa angka bulat.', 'danger')
            return redirect(url_for('diagnosis'))

        if umur < 3 or umur > 70:
            flash(f'Umur {umur} tahun tidak valid, butuh validasi klinis lanjutan.', 'warning')
            return redirect(url_for('diagnosis'))

        suhu = request.form.get('suhu')
        tensi = request.form.get('tensi')
        berat = request.form.get('berat')
        keluhan = request.form.get('keterangan')

        catatan_parts = []
        if suhu:
            catatan_parts.append(f"Suhu: {suhu}°C")
        if tensi:
            catatan_parts.append(f"Tensi: {tensi}")
        if berat:
            catatan_parts.append(f"Berat Badan: {berat} kg")
        if keluhan:
            catatan_parts.append(f"Keterangan: {keluhan}")

        catatan = "\n".join(catatan_parts) if catatan_parts else None

        # === Validasi Format ===
        error_msg = []

        if suhu:  # hanya validasi jika suhu diisi
            if not re.match(r"^\d+(\.\d)?$", suhu.strip()):
                error_msg.append("Format suhu tidak valid (contoh: 36.5).")

        if tensi:  # hanya validasi jika tensi diisi
            if not re.match(r"^\d{2,3}/\d{2,3}$", tensi.strip()):
                error_msg.append("Format tensi tidak valid (contoh: 120/80).")

        if berat:  # hanya validasi jika berat diisi
            if not re.match(r"^\d+(\.\d+)?$", berat.strip()):
                error_msg.append("Format berat badan tidak valid (contoh: 60 atau 60.5).")

        if not gejala_dipilih:
            flash('Silakan pilih minimal satu gejala.', 'warning')
            return redirect(url_for('diagnosis'))

        hasil, kemungkinan_json = predict_disease(gejala_dipilih)  # ← diubah jadi 2 hasil
        top_disease, prob, penyakit_id = hasil[0]

        if prob >= 0.6:
            tingkat = "Tinggi"
        elif prob >= 0.4:
            tingkat = "Sedang"
        else:
            tingkat = "Rendah"

        penyakit_utama = Penyakit.query.get(penyakit_id)
        if not penyakit_utama:
            flash('Penyakit tidak ditemukan.', 'danger')
            return redirect(url_for('diagnosis'))

        riwayat = RiwayatDiagnosis(
            user_id=current_user.id,
            penyakit_id=penyakit_id,
            nama_pasien=nama_pasien,
            umur=umur,
            gejala_dipilih=", ".join(gejala_dipilih),
            probabilitas=round(prob, 4),
            catatan=catatan,
            kemungkinan_lainnya=kemungkinan_json  # ← disimpan ke database
        )
        db.session.add(riwayat)
        db.session.commit()

        data_catatan = parse_catatan(catatan) if catatan else {}

        penyakit_list = [
            {
                'nama_penyakit': p.nama_penyakit,
                'definisi_penyakit': p.definisi_penyakit,
                'penyebab': p.penyebab,
                'penanganan': p.penanganan
            }
            for p in Penyakit.query.all()
        ]

        return render_template(
            'hasil_diagnosis.html',
            riwayat=riwayat,
            hasil=hasil,
            penyakit=penyakit_utama,
            tingkat=tingkat,
            penyakit_list=penyakit_list,
            data_catatan=data_catatan
        )

    return render_template('diagnosis.html', daftar_gejala=daftar_gejala)


######################### ROUTE CRUD RIWAYAT DIAGNOSIS #########################
@app.route('/riwayat')
@login_required
def riwayat():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 5  # atau bebas sesuai jumlah per halaman

    # Base query sesuai role
    if current_user.role.value == 'admin':
        query = RiwayatDiagnosis.query
    elif current_user.role.value == 'dokter':
        query = RiwayatDiagnosis.query
    else:
        query = RiwayatDiagnosis.query.filter_by(user_id=current_user.id_user)

    if search:
        found = False
        date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']
        for fmt in date_formats:
            try:
                search_date = datetime.strptime(search, fmt).date()
                query = query.filter(func.date(RiwayatDiagnosis.tanggal_diagnosis) == search_date)
                found = True
                break
            except ValueError:
                continue
        if not found:
            query = query.filter(RiwayatDiagnosis.nama_pasien.ilike(f'%{search}%'))

    pagination = query.order_by(RiwayatDiagnosis.tanggal_diagnosis.desc()).paginate(page=page, per_page=per_page)
    data = pagination.items

    for item in data:
        item.username = item.pengguna.username if item.pengguna else 'N/A'
        item.nama_penyakit = item.penyakit.nama_penyakit if item.penyakit else 'N/A'

        try:
            raw_ids = item.gejala_dipilih
            if raw_ids.startswith('['):
                import ast
                id_list = ast.literal_eval(raw_ids)
            else:
                id_list = [id.strip() for id in raw_ids.split(',') if id.strip()]
            item.gejala_nama = id_to_nama_gejala(id_list)
        except Exception:
            item.gejala_nama = ['(gagal membaca gejala)']

    empty_data = len(data) == 0
    return render_template('riwayat_diagnosis.html', data=data, pagination=pagination, search=search, empty_data=empty_data)

@app.route('/riwayat/detail/<int:id_riwayat>')
@login_required
def detail_riwayat(id_riwayat):
    riwayat = RiwayatDiagnosis.query.get_or_404(id_riwayat)

    data_catatan = parse_catatan(riwayat.catatan) if riwayat.catatan else {}

    keluhan = "-"
    diagnosis_akhir = "-"

    if riwayat.catatan:
        try:
            if riwayat.catatan.strip().startswith("{"):
                data = json.loads(riwayat.catatan)
                keluhan = data.get("keluhan", "-")
                diagnosis_akhir = data.get("diagnosis", "-")
            else:
                full_text = riwayat.catatan.strip()

                # Buat baris baru sebelum keyword pemeriksaan
                pemeriksaan_keywords = ['Suhu:', 'Tensi:', 'Berat Badan:', 'Nadi:', 'Saturasi:']
                for keyword in pemeriksaan_keywords:
                    full_text = full_text.replace(keyword, f'\n{keyword}')

                # Split menjadi baris
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]

                # Ambil hanya baris non-pemeriksaan
                non_pemeriksaan_lines = [
                    line for line in lines if not any(line.startswith(k) for k in pemeriksaan_keywords)
                ]

                # Gabungkan kembali
                cleaned_text = ' '.join(non_pemeriksaan_lines)

                # Pisah berdasarkan diagnosis keyword
                diagnosis_keywords = ['Diagnosis Akhir:', 'Dx:', 'Diagnosa Akhir:']
                diagnosis_start = -1
                keyword_used = ''

                for keyword in diagnosis_keywords:
                    diagnosis_start = cleaned_text.find(keyword)
                    if diagnosis_start != -1:
                        keyword_used = keyword
                        break

                if diagnosis_start != -1:
                    keluhan = cleaned_text[:diagnosis_start].strip()
                    diagnosis_akhir = cleaned_text[diagnosis_start + len(keyword_used):].strip()
                else:
                    keluhan = cleaned_text

                # Hapus awalan 'Keterangan:' dari keluhan jika ada
                if keluhan.lower().startswith("keterangan:"):
                    keluhan = keluhan[len("keterangan:"):].strip()

        except Exception as e:
            print("Gagal parsing catatan:", e)

    # Parse kemungkinan_lainnya ke list
    kemungkinan_list = []
    if riwayat.kemungkinan_lainnya:
        try:
            raw_data = json.loads(riwayat.kemungkinan_lainnya)
            kemungkinan_list = [{'nama': x[0], 'prob': x[1]} for x in raw_data]
        except Exception as e:
            print("Gagal parsing kemungkinan_lainnya:", e)

    return render_template(
        'detail_riwayat_diagnosis.html',
        riwayat=riwayat,
        data_catatan=data_catatan,
        kemungkinan_list=kemungkinan_list,
        keluhan=keluhan,
        diagnosis_akhir=diagnosis_akhir
    )

@app.route('/riwayat/edit/<int:id_riwayat>', methods=['POST'])
@login_required
@dokter_required
def edit_riwayat(id_riwayat):
    riwayat = RiwayatDiagnosis.query.get_or_404(id_riwayat)

    try:
        riwayat.nama_pasien = request.form['nama_pasien']
        riwayat.umur = int(request.form['umur'])

        # === Validasi Umur ===
        umur_raw = request.form.get('umur', '').strip()
        try:
            umur = int(umur_raw)
        except ValueError:
            flash("Umur harus berupa angka bulat.", "danger")
            return redirect(url_for('riwayat'))

        if umur < 3 or umur > 70:
            flash(f"Umur {umur} tahun tidak valid, butuh validasi klinis lanjutan.", "danger")
            return redirect(url_for('riwayat'))

        # Ambil dari dua textarea
        catatan_medis = request.form.get('catatan', '').strip()
        diagnosis_akhir = request.form.get('diagnosis_akhir', '').strip()

        # === Validasi Format ===
        suhu = re.search(r"Suhu:\s*([0-9]+\.[0-9])\b", catatan_medis)
        tensi = re.search(r"Tensi:\s*(\d{2,3}/\d{2,3})\b", catatan_medis)
        berat = re.search(r"Berat Badan:\s*(\d+(\.\d+)?)\b", catatan_medis)

        error_msg = []
        if not suhu:
            error_msg.append("Format suhu tidak valid (contoh: 36.5).")
        if not tensi:
            error_msg.append("Format tensi tidak valid (contoh: 120/80).")
        if not berat:
            error_msg.append("Format berat badan tidak valid (contoh: 60 atau 60.5).")

        if error_msg:
            for msg in error_msg:
                flash(msg, 'danger')
            return redirect(url_for('riwayat'))

        # Gabungkan keduanya ke dalam satu string catatan
        if diagnosis_akhir and diagnosis_akhir.lower() != 'belum ada data':
            riwayat.catatan = f"{catatan_medis}\n\nDiagnosis Akhir: {diagnosis_akhir}".strip()
        else:
            riwayat.catatan = catatan_medis.strip()

        db.session.commit()
        flash("Riwayat berhasil diperbarui.", "success")

    except Exception as e:
        db.session.rollback()
        flash('Terjadi kesalahan saat mengedit riwayat.', 'danger')

    return redirect(url_for('riwayat'))

@app.route('/riwayat/delete/<int:id_riwayat>', methods=['POST'])
@login_required
def delete_riwayat(id_riwayat):
    riwayat = RiwayatDiagnosis.query.get_or_404(id_riwayat)

    riwayat.delete()
    flash('Riwayat diagnosis berhasil dihapus.', 'success')
    return redirect(url_for('riwayat'))

from datetime import datetime
import io
import json
import os
from flask import make_response, render_template
from xhtml2pdf import pisa

@app.route('/riwayat/pdf/<int:id_riwayat>')
@login_required
def cetak_pdf(id_riwayat):
    riwayat = RiwayatDiagnosis.query.get_or_404(id_riwayat)
    data_catatan = parse_catatan(riwayat.catatan) if riwayat.catatan else {}

    keluhan = "-"
    diagnosis_akhir = "-"
    kemungkinan_list = []

    if riwayat.catatan:
        try:
            if riwayat.catatan.strip().startswith("{"):
                # Format JSON (lebih aman)
                data = json.loads(riwayat.catatan)
                keluhan = data.get("keluhan", "-")
                diagnosis_akhir = data.get("diagnosis", "-")
            else:
                full_text = riwayat.catatan.strip()

                # Tambahkan newline di depan keyword pemeriksaan
                pemeriksaan_keywords = ['Suhu:', 'Tensi:', 'Berat Badan:', 'Nadi:', 'Saturasi:']
                for keyword in pemeriksaan_keywords:
                    full_text = full_text.replace(keyword, f'\n{keyword}')

                # Buat daftar baris
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]

                # Hilangkan baris pemeriksaan
                non_pemeriksaan_lines = [
                    line for line in lines if not any(line.startswith(k) for k in pemeriksaan_keywords)
                ]
                cleaned_text = ' '.join(non_pemeriksaan_lines)

                # Cari diagnosis akhir
                diagnosis_keywords = ['Diagnosis Akhir:', 'Dx:', 'Diagnosa Akhir:']
                diagnosis_start = -1
                keyword_used = ''

                for keyword in diagnosis_keywords:
                    diagnosis_start = cleaned_text.find(keyword)
                    if diagnosis_start != -1:
                        keyword_used = keyword
                        break

                if diagnosis_start != -1:
                    keluhan = cleaned_text[:diagnosis_start].strip()
                    diagnosis_akhir = cleaned_text[diagnosis_start + len(keyword_used):].strip()
                else:
                    keluhan = cleaned_text

                # Bersihkan awalan "Keterangan:"
                if keluhan.lower().startswith("keterangan:"):
                    keluhan = keluhan[len("keterangan:"):].strip()

        except Exception as e:
            print("Gagal parsing catatan:", e)

    # Parsing kemungkinan penyakit
    if riwayat.kemungkinan_lainnya:
        try:
            raw_data = json.loads(riwayat.kemungkinan_lainnya)
            kemungkinan_list = [{'nama': x[0], 'prob': x[1]} for x in raw_data]
        except:
            kemungkinan_list = []

    # Format tanggal
    tanggal_cetak = datetime.now().strftime('%d-%m-%Y')

    # Render HTML dengan data lengkap
    rendered = render_template(
        'pdf_riwayat.html',
        riwayat=riwayat,
        data_catatan=data_catatan,
        keluhan=keluhan,
        diagnosis_akhir=diagnosis_akhir,
        kemungkinan_list=kemungkinan_list,
        tanggal_cetak=tanggal_cetak
    )

    # Generate PDF dari HTML (tanpa CSS eksternal, sudah inline)
    result = io.BytesIO()
    pisa.CreatePDF(io.StringIO(rendered), dest=result)

    # Nama file rapi
    nama_pasien_slug = riwayat.nama_pasien.replace(" ", "_")
    filename = f"Riwayat Diagnosis_{nama_pasien_slug}_{tanggal_cetak}.pdf"

    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename={filename}'

    return response

# Jalankan Aplikasi
if __name__ == '__main__':
    app.debug = True
    app.run()