from db_config import db
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
from flask_login import UserMixin

class RoleEnum(Enum):
    ADMIN = "admin"
    USER = "user"
    DOKTER = "dokter"  # tambahan role dokter

class User(UserMixin, db.Model):
    __tablename__ = 'pengguna'

    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 255 agar cukup panjang untuk hash
    role = db.Column(
        db.Enum(RoleEnum, values_callable=lambda enum: [e.value for e in enum]), 
        default=RoleEnum.USER.value,  
        nullable=False
    )
    profesi = db.Column(db.String(100))
    photo = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')  # method default: 'pbkdf2:sha256'

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.id_user)
    
    @property
    def id(self):
        return self.id_user

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
        return User.query.all()

    @staticmethod
    def get_by_id(id_user):
        return User.query.get(id_user)
