from db import db
import datetime
from models.requests import RequestModel
from models.event import EventModel


class ChatModel(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer)
    chat_creation_time = db.Column(db.String(80))
    chat_expiration_time = db.Column(db.String(80))

    def __init__(self, chat_creation_time, chat_expiration_time, event_id):
        self.chat_expiration_time = chat_expiration_time
        self.chat_creation_time = chat_creation_time
        self.event_id = event_id

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        return {'chat_creation_time': self.chat_creation_time,
                'chat_expiration_time': self.chat_expiration_time,
                "id": self.id, "event_id": self.event_id}

    @classmethod
    def find_by_username(cls, username):
        user_chats = []
        allChats = cls.query.all()
        user_events = EventModel.get_participant_events(username)
        user_event_ids = [event.id for event in user_events]
        user_chats = []
        for chat in allChats:
            if chat.event_id in user_event_ids:
                user_chats.append(chat)
        
        return user_chats

    @classmethod
    def find_by_filters(cls, event_id=None, id=None):
        if event_id:
            return cls.query.filter_by(event_id=event_id).first()
        if id:
            return cls.query.filter_by(id=id).first()


    @classmethod
    def delete_chat(cls, chat):
        messages = MessageModel.find_by_chat_id(chat.id)
        chat.delete_from_db()
        for message in messages:
            message.delete_from_db()
        chat_acks = ChatAckModel.find_by_filters(chat_id=chat.id)
        for chat_ack in chat_acks:
            chat_ack.delete_from_db()


    @classmethod
    def clear_expired(cls):
        current_time = datetime.datetime.now()
        chats = cls.query.all()
        expired = []
        for chat in chats:
            if (chat.chat_expiration_time != '') and \
                    (current_time > RequestModel.expiration_to_datetime(chat.chat_expiration_time)):
                expired.append(chat)

        for chat in expired:
            print('expired deleting:', chat.json())
            ChatModel.delete_chat(chat)

class MessageModel(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    content = db.Column(db.String(200))
    timestamp = db.Column(db.String(80))
    username = db.Column(db.String(80))

    def __init__(self, chat_id, content, username, timestamp):
        self.chat_id = chat_id
        self.username = username
        self.content = content
        self.timestamp = timestamp

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def json(self):
        return {'chat_id': self.chat_id, 'content': self.content,
                'username': self.username, 'id': self.id, "timestamp" : self.timestamp}

    @classmethod
    def find_by_chat_id(cls, chat_id):
        return cls.query.filter_by(chat_id=chat_id).all()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

class ChatAckModel(db.Model):
    __tablename__ = 'chat_acks'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    timestamp = db.Column(db.String(80))
    username = db.Column(db.String(80))

    def __init__(self, chat_id, username, timestamp):
        self.chat_id = chat_id
        self.username = username
        self.timestamp = timestamp

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def json(self):
        return {'chat_id': self.chat_id, 'username': self.username, 
        'id': self.id, "timestamp" : self.timestamp}

    @classmethod
    def find_by_filters(cls, chat_id, username=None):
        if username:
            return cls.query.filter_by(chat_id=chat_id, username=username).first()
        return cls.query.filter_by(chat_id=chat_id).all()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()