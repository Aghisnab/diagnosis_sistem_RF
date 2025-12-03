from db_config import db

class Gejala(db.Model):
    __tablename__ = 'gejala'
    
    id_gejala = db.Column(db.Integer, primary_key=True)
    gejala = db.Column(db.String(100), nullable=False, unique=True)

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
        return Gejala.query.all()

    @staticmethod
    def get_by_id(id_gejala):
        return Gejala.query.get(id_gejala)

    @staticmethod
    def get_by_name(gejala_name):
        return Gejala.query.filter_by(gejala=gejala_name).first()

    def to_dict(self):
        return {
            'id_gejala': self.id_gejala,
            'gejala': self.gejala
        }