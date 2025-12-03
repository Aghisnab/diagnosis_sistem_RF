# model/riwayat_diagnosis.py
from db_config import db
from datetime import datetime

class RiwayatDiagnosis(db.Model):
    __tablename__ = 'riwayat_diagnosis'

    id_riwayat = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('pengguna.id_user'), nullable=False)
    penyakit_id = db.Column(db.Integer, db.ForeignKey('penyakit.id_penyakit'), nullable=False)

    nama_pasien = db.Column(db.String(100), nullable=False)
    umur = db.Column(db.Integer, nullable=False)
    gejala_dipilih = db.Column(db.Text, nullable=False)
    probabilitas = db.Column(db.Float, nullable=False)
    tanggal_diagnosis = db.Column(db.DateTime, default=datetime.utcnow)
    catatan = db.Column(db.Text, nullable=False)
    kemungkinan_lainnya = db.Column(db.Text, nullable=False)

    # ✅ Relasi model lowercase
    pengguna = db.relationship("User", backref="riwayat")
    penyakit = db.relationship("Penyakit", backref="riwayat")

    # Method penyimpanan
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # Static method tambahan
    @staticmethod
    def get_all():
        return RiwayatDiagnosis.query.all()

    @staticmethod
    def get_by_id(id_riwayat):
        return RiwayatDiagnosis.query.get(id_riwayat)

    @staticmethod
    def get_by_user(user_id):
        return RiwayatDiagnosis.query.filter_by(user_id=user_id).all()
