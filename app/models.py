from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login
from enum import Enum

class MyEnum(Enum):
    Male = 1
    Female = 2

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    appointments = db.relationship('Appointment', backref='applicant', lazy='dynamic')
    dogs = db.relationship('Dog', backref='owner', lazy='dynamic')
    address = db.Column(db.String(140))
    administrator = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @property
    def is_administrator(self):
        return self.administrator

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def create_appos(self):
        appo = Appointment.query.filter_by(user_id=self.id)
        return appo.order_by(Appointment.create_time.desc())

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(140))
    date = db.Column(db.Date)
    time = db.Column(db.String(9))
    comment = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    create_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    complete = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Appointment {}>'.format(self.address)

    @property
    def is_compelte(self):
        return self.complete

class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    dog_type = db.Column(db.String(64))
    age = db.Column(db.Integer)
    length = db.Column(db.Float)
    gender = db.Column(db.Enum(MyEnum))
    comment = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    appointments = db.relationship('Appointment', backref='fordog', lazy='dynamic')

    def __repr__(self):
        return '<Dog {}>'.format(self.name)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    price = db.Column(db.Float)
    appointments = db.relationship('Appointment', backref='type', lazy='dynamic')
    expired = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Service {}>'.format(self.name)

    @property
    def is_expired(self):
        return self.expired
        
