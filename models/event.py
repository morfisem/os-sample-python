from db import db
from models.requests import RequestModel
from models.friendship import FriendshipModel


class EventModel(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    event_type = db.Column(db.Integer)
    event_time = db.Column(db.String(80))
    participants = db.Column(db.String(80))
    access = db.Column(db.Integer)
    event_state = db.Column(db.Integer)
    location = db.Column(db.String(80))
    duration = db.Column(db.Integer)
    owner = db.Column(db.String(80))
    icon = db.Column(db.String(300))
    idea_id = db.Column(db.Integer)
    description = db.Column(db.String(300))


    def __init__(self, title, event_type, event_time, participants, access, event_state,
                location, duration, owner, icon, idea_id, description):
        self.title = title
        self.event_type = event_type
        self.event_time = event_time
        self.participants = participants
        self.access = access
        self.event_state = event_state
        self.location = location
        self.duration = duration
        self.owner = owner
        self.icon = icon
        self.idea_id = idea_id
        self.description = description

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        return {'title': self.title, 'event_type': self.event_type, 'event_time': self.event_time,
                "participants": self.participants,
                "event_state": self.event_state,"location": self.location,
                "id":self.id, "duration":self.duration, "owner":self.owner, "icon":self.icon, "description": self.description}

    def add_user_and_save(self, username):
        if username in self.participants.split(','):
            return
        self.participants += "," + username
        self.save_to_db()
    
    def remove_user_and_save(self, username):
        participants = self.participants.split(',')
        if username not in participants:
            return self.participants
        participants.remove(username)
        self.participants = ",".join(participants)
        self.save_to_db()
        return self.participants

    @classmethod
    def get_participant_events(cls, username):
        allEvents = cls.query.all()
        user_events = {}
        for event in allEvents:
            if username in event.participants.split(',') or username == event.owner:
                user_events[event.id] = event
        return user_events.values()
    
    @classmethod
    def find_by_state(cls, event_state):
        return cls.query.filter_by(event_state=event_state).all()
    
    def get_event_viewers(self):
        user_events = {}
        basic_viewers = self.participants.split(',') + [self.owner]
        if 1 == self.access:
            return None
        elif 2 == self.access:
            friendsList = FriendshipModel.get_user_friends(main_user=self.owner, friend_type=1)
            palList = FriendshipModel.get_user_friends(main_user=self.owner, friend_type=2)
            return friendsList + palList + basic_viewers
        elif 3 == self.access:
            friendsList = FriendshipModel.get_user_friends(main_user=self.owner, friend_type=1)
            return friendsList + basic_viewers
        else:
            return basic_viewers
    
    @classmethod
    def find_by_username(cls, username):
        user_events = {}
        allEvents = cls.query.all()
        #allActiveEvents = cls.query.filter_by(event_state=1).all()
        #allNonActiveEvents = cls.query.filter_by(event_state=0).all()

        #for event in allActiveEvents:
        for event in allEvents:
            if 1 == event.access:
                user_events[event.id] = event
            elif 2 == event.access:    
                friendsList = FriendshipModel.get_user_friends(main_user=event.owner, friend_type=1)
                palList = FriendshipModel.get_user_friends(main_user=event.owner, friend_type=2)
                for friendship in friendsList + palList:
                    if friendship.other_user == username:
                        user_events[event.id] = event
            elif 3 == event.access:
                friendsList = FriendshipModel.get_user_friends(main_user=event.owner, friend_type=1)
                for friendship in friendsList:
                    if friendship.other_user == username:
                        user_events[event.id] = event
            
            if username in event.participants.split(',') or username == event.owner:
                user_events[event.id] = event
        '''
        for event in allNonActiveEvents:
            requests = RequestModel.find_by_event_id(event.id)
            if not requests:
                continue
            for request in requests:
                if username == request.requesting_user or username == request.requested_user:
                    user_events[event.id] = event
                    break
        '''
        return user_events.values()
    
    @classmethod
    def get_all(cls):
        return cls.query.all()
    
    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()
    
    @classmethod
    def clear_events(cls):
        events = cls.query.filter_by(event_state=0).all()
        event_to_delete = []
        for event in events:
            requests = RequestModel.find_by_event_id(event.id)
            if not requests:
                event_to_delete.append(event)
        
        for event in event_to_delete:
            event.delete_from_db()