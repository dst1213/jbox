# -*- coding: utf-8 -*-
import random, string
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from sqlalchemy.exc import IntegrityError
from jbox import db
from flask_login import UserMixin
from . import login_manager


class Developer(UserMixin, db.Model):
    __tablename__ = 'developers'
    id = db.Column(db.Integer, primary_key=True)
    dev_key = db.Column(db.String(40), unique=True, index=True)
    platform = db.Column(db.String(50))
    platform_id = db.Column(db.String(40), unique=True)
    username = db.Column(db.String(150), index=True)
    channel = db.Column(db.String(150))
    confirmed = db.Column(db.Boolean, default=False)
    integrations = db.relationship('Integration', backref='developer')

    def __repr__(self):
        return '<Developer %r>' % self.dev_key

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return Developer.query.get(data['id'])

    def insert_to_db(self):
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            b = False
            while b == False:
                user = Developer.query.filter_by(dev_key=self.dev_key).first()
                if user is None:
                    user = Developer.query.filter_by(platform_id=self.platform_id).first()
                    if user is not None:
                        self.platform_id = generate_platform_id()
                        db.session.add(self)
                        try:
                            db.session.commit()
                            b = True
                        except IntegrityError:
                            db.session.rollback()
                            b = False
                else:
                    self.dev_key = generate_dev_key()
                    db.session.add(self)
                    try:
                        db.session.commit()
                        b = True
                    except IntegrityError:
                        db.session.rollback()
                        b = False
        return True





class Integration(db.Model):
    __tablename__ = 'integrations'
    id = db.Column(db.Integer, primary_key=True)
    integration_id = db.Column(db.String(40), unique=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(150))
    icon = db.Column(db.String(150))
    channel = db.Column(db.String(150))
    developer_id = db.Column(db.Integer, db.ForeignKey('developers.id'))

    def __repr__(self):
        return '<Integration %r>' % self.integration_id

    def insert_to_db(self):
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flag = False
            while flag == False:
                integration = Integration.query.filter_by(integration_id=self.integration_id).first()
                if integration is not None:
                    self.integration_id = generate_integration_id()
                    db.session.add(self)
                    try:
                        db.session.commit()
                        flag = True
                    except IntegrityError:
                        db.session.rollback()
                        flag = False
                else:
                    flag = True
        return True


@login_manager.user_loader
def load_user(user_id):
    return Developer.query.get(int(user_id))


def generate_dev_key():
    dev_key = ''.join([(string.ascii_letters+string.digits)[x] for x in random.sample(range(0, 62), 40)])
    return dev_key


def generate_platform_id():
    platform_id = ''.join([(string.ascii_letters+string.digits)[x] for x in random.sample(range(0, 62), 40)])
    return platform_id


def generate_integration_id():
    integration_id = ''.join([(string.ascii_letters+string.digits)[x] for x in random.sample(range(0, 62), 40)])
    return integration_id
