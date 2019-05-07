from db import db
import datetime


class RequestModel(db.Model):
    __tablename__ = 'requests'
    request_types = ["stub", "Coffee", "Lunch", "Movie","Beer","Game"]
    id = db.Column(db.Integer, primary_key=True)
    request_state = db.Column(db.Integer)
    request_type = db.Column(db.Integer)
    requesting_user = db.Column(db.String(80))
    requested_user = db.Column(db.String(80))
    request_time = db.Column(db.String(80))
    request_expiration_time = db.Column(db.String(80))
    event_id = db.Column(db.Integer)
    delay = db.Column(db.Integer)

    def __init__(self, request_state, requesting_user, requested_user, request_time, request_expiration_time,
                 request_type, event_id, delay=0):
        self.request_state = request_state
        self.requesting_user = requesting_user
        self.requested_user = requested_user
        self.request_time = request_time
        self.request_expiration_time = request_expiration_time
        if request_type in RequestModel.request_types:
            self.request_type = RequestModel.request_types.index(request_type)
        else:
            self.request_type = request_type
        self.event_id = event_id
        self.delay = delay

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def json(self):
        if self.request_type in RequestModel.request_types:
            string_request_type = self.request_type
        elif int(self.request_type) < len(RequestModel.request_types):
            string_request_type = RequestModel.request_types[self.request_type]
        else:
            string_request_type = 'unknown'
        
        return {'request_state': self.request_state, 'requesting_user': self.requesting_user,
                'requested_user': self.requested_user, 'request_time': self.request_time,
                "request_expiration_time": self.request_expiration_time,
                "request_type": string_request_type,
                "id": self.id, "event_id": self.event_id,"delay": self.delay}

    @classmethod
    def get_received_requests(cls, username):
        user_requests = cls.query.filter_by(requested_user=username).all()
        return user_requests

    @classmethod
    def get_active_sent_requests(cls, username):
        user_requests = cls.query.filter_by(requesting_user=username).all()
        return user_requests

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_filters(cls, requesting_user, requested_user, request_type):
        print("filters: ", requesting_user,requested_user,request_type)
        return cls.query.filter_by(requesting_user=requesting_user, requested_user=requested_user,
                                   request_type=request_type).first()

    @classmethod
    def find_by_event_id(cls, event_id):
        return cls.query.filter_by(event_id=event_id).all()
    
    @classmethod
    def expiration_to_datetime(cls, expiration_time):
        if not expiration_time:
            return None
        if "." in expiration_time:
            return datetime.datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S.%f")
        else:
            return datetime.datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S")

    @classmethod
    def clear_expired(cls):
        current_time = datetime.datetime.now()
        requests = cls.query.all()
        expired = []
        for request in requests:
            if (request.request_expiration_time != '') and \
                    (current_time > cls.expiration_to_datetime(request.request_expiration_time)):
                expired.append(request)

        for request in expired:
            print('expired deleting:', request.json())
            request.delete_from_db()
    
    @classmethod
    def clear_abandoned(cls, events):
        requests = cls.query.all()
        event_ids = [event.id for event in events]
        expired = []
        for request in requests:
            if request.event_id not in event_ids:
                expired.append(request)

        for request in expired:
            request.delete_from_db()

    @classmethod
    def filter_duplicates(cls):
        filtered = {}
        requests = cls.query.all()
        duplicated = []

        for request in requests:
            filter_params = (request.requesting_user, request.requested_user, request.request_type)
            if filter_params in filtered:
                exp1 = cls.expiration_to_datetime(filtered[filter_params].request_expiration_time)
                exp2 = cls.expiration_to_datetime(request.request_expiration_time)

                if exp1 > exp2:
                    duplicated.append(request)
                else:
                    duplicated.append(filtered[filter_params])
                    filtered[filter_params] = request
            else:
                filtered[filter_params] = request

        for request in duplicated:
            print('filter deleting:', request.json())
            request.delete_from_db()
    @classmethod
    def replace_event(cls,old_event_id, new_event_id):
        filtered = {}
        requests = cls.query.filter_by(event_id=old_event_id).all()
        duplicated = []

        for request in requests:
            request.event_id = new_event_id
            request.save_to_db()
    
    @classmethod
    def clear_requests(cls,request_type, requesting_user=None, request_state=None, requested_user=None, event_id=None):
        args = {"request_type":request_type,
                "requesting_user":requesting_user,
                "request_state":request_state,
                "requested_user":requested_user,
                "event_id":event_id}
        
        args = {k:v for k,v in args.items() if None != v}
        print("args after:",args)
        requests = cls.query.filter_by(**args).all()
        for request in requests:
            request.delete_from_db()