from db_config import db

class Penyakit(db.Model):
    __tablename__ = 'penyakit'
    
    id_penyakit = db.Column(db.Integer, primary_key=True)
    nama_penyakit = db.Column(db.String(100), nullable=False, unique=True)
    definisi_penyakit = db.Column(db.Text, nullable=True)
    penyebab = db.Column(db.Text, nullable=True)
    penanganan = db.Column(db.Text, nullable=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Penyakit.query.all()

    @staticmethod
    def get_by_id(id_penyakit):
        return Penyakit.query.get(id_penyakit)

    @staticmethod
    def get_by_name(nama_penyakit):
        return Penyakit.query.filter_by(nama_penyakit=nama_penyakit).first()

    def to_dict(self):
        return {
            'id_penyakit': self.id_penyakit,
            'nama_penyakit': self.nama_penyakit,
            'definisi_penyakit': self.definisi_penyakit,
            'penyebab': self.penyebab,
            'penanganan': self.penanganan
        }
