from db import db


class UserInfoModel(db.Model):
    __tablename__ = 'userInfo'

    username = db.Column(db.String(80), primary_key=True)
    email = db.Column(db.String(80))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    profile = db.Column(db.String(80))

    def __init__(self, username, email, first_name, last_name, profile):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.profile = profile

    def json(self):
        return {'username': self.username, 'email': self.email, 'first_name': self.first_name,
                'last_name': self.last_name, 'profile': self.profile}

    @classmethod
    def find_by_name(cls, username):
        return cls.query.filter_by(username=username).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

class UserSettingsModel(db.Model):
    __tablename__ = 'user_settings'

    username = db.Column(db.String(80), primary_key=True)
    default_location = db.Column(db.String(80))
    max_requests = db.Column(db.Integer)
    pal_precent = db.Column(db.Integer)
    friend_precent = db.Column(db.Integer)
    default_access = db.Column(db.Integer)
    default_duration = db.Column(db.Integer)

    def __init__(self, username, default_location, max_requests, pal_precent, friend_precent, default_access):
        self.username = username
        self.default_location = default_location
        self.max_requests = max_requests
        self.pal_precent = pal_precent
        self.friend_precent = friend_precent
        self.default_access = default_access
        self.default_duration = default_duration

    def json(self):
        return {'username': self.username, 'default_location': self.default_location, 'max_requests': self.max_requests,
                'pal_precent': self.pal_precent,'friend_precent': self.friend_precent, "default_access":self.default_access, "default_duration":self.default_duration}

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()