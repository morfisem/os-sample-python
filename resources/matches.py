from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from models.requests import RequestModel
from models.event import EventModel
from resources.chats import Chats
from resources.event import Events
from resources.cleaner import cleanExpired
import datetime


class PostponedRequest(Resource):
    @jwt_required
    def post(self):
        print("in poster")
        parser = reqparse.RequestParser()
        parser.add_argument('requesting_user', type=str, required=True, help='Must enter the store id')
        parser.add_argument('request_type', type=str, required=True, help='Must enter the store id')
        parser.add_argument('delay', type=str, required=True, help='Must enter the store id')

        data = parser.parse_args()
        cleanExpired()
        request_type_text = data["request_type"]
        if request_type_text in RequestModel.request_types:
            request_type = RequestModel.request_types.index(request_type_text)
        else:
            return {'message': 'request type not found'}, 404

        requesting_user =data["requesting_user"]
        current_user = get_jwt_identity()
        user_request = RequestModel.find_by_filters(requesting_user=requesting_user, requested_user=current_user,
                                                        request_type=request_type)
        
        if not user_request:
            return {'message': 'request not found'}, 404
        current_time = datetime.datetime.now()
        user_request.request_state = 2
        user_request.delay = data["delay"]
        user_request.save_to_db()
        
        #remove oposite request
        RequestModel.clear_requests(requesting_user=current_user, 
                                    request_type=request_type,
                                    requested_user=requesting_user,
                                    request_state=0)
        return user_request.json()

class ConfirmRequest(Resource):
    @classmethod
    def merge_events(cls, main_event_id, other_event_id):
        main_event = EventModel.find_by_id(main_event_id)
        other_event = EventModel.find_by_id(other_event_id)
        if not main_event or not other:
            return
        #change event_id in requests
        RequestModel.replace_event(other_event_id, main_event_id)
        [main_event_id.add_user_and_save(user) for user in other_event.participants.split(',')]
    @classmethod
    def validate_request(cls, username, request):
        if 0 == request.request_state and username == request.requested_user:
            return True
        elif 2 == request.request_state and (username == request.requesting_user):
            return True
        else:
            return False
    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('requesting_user', type=str, required=True, help='Must enter the store id')
        parser.add_argument('requested_user', type=str, required=True, help='Must enter the store id')
        parser.add_argument('request_type', type=str, required=True, help='Must enter the store id')

        data = parser.parse_args()
        cleanExpired()
        request_type_text = data["request_type"]
        if request_type_text in RequestModel.request_types:
            request_type = RequestModel.request_types.index(request_type_text)
        else:
            return {'message': 'request type not found'}, 404

        requesting_user =data["requesting_user"]
        requested_user =data["requested_user"]
        user_request = RequestModel.find_by_filters(requesting_user=requesting_user, requested_user=requested_user,
                                                        request_type=request_type)
        current_user = get_jwt_identity()
        if not user_request:
            return {'message': 'request not found'}, 404
        elif not ConfirmRequest.validate_request(current_user, user_request):
            return {'message': 'access denied'}, 404

        user_request.request_state = 1
        user_request.save_to_db()
        
        event = EventModel.find_by_id(user_request.event_id)
        if not event:
            return {'message': 'event not found'}, 404
        
        if 1 != event.event_state and event.event_time == "":
            current_time = datetime.datetime.now()
            if user_request.delay != 0:
                event_time = datetime.datetime.now() + datetime.timedelta(minutes=user_request.delay)
            else:
                event_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
            event.event_time = event_time
        
        event.add_user_and_save(requested_user)

        RequestModel.clear_requests(requesting_user=requesting_user,
                                    request_type=request_type,
                                     request_state=0)
        RequestModel.clear_requests(requesting_user=requested_user, 
                                    request_type=request_type,
                                     request_state=0)
        RequestModel.clear_requests(event_id=event.id,
                                    request_type=request_type,
                                    request_state=0)
        
        Chats.create_chat(event_time=str(event.event_time), event_id=event.id)
        cleanExpired()
        return user_request.json()

class JoinEvent(Resource):
    @jwt_required
    def post(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('unjoin', type=str, required=False, help='Must enter the store id')

        data = parser.parse_args()
        unjoin =data["unjoin"]
        
        event = EventModel.find_by_id(event_id)

        if not event:
            return {'message': 'event not found'}, 404
        
        current_user = get_jwt_identity()
        user_events = EventModel.find_by_username(username=current_user)

        if event.id not in [user_event.id for user_event in user_events]:
            return {'message': 'Access Denied'}, 404
        
        if not unjoin or unjoin==0:
            event.add_user_and_save(current_user)
        else:
            remaining_participants = event.remove_user_and_save(current_user)
            if len(remaining_participants.split(',')) < 2:
                event.delete_from_db()
                Chats.delete_chat(event_id=event.id)

        return event.json()


class Requests(Resource):
    @classmethod
    def add_new_request(cls, request):
        if request.requesting_user == request.requested_user:
            return None
        existing_request = RequestModel.find_by_filters(requesting_user=request.requesting_user,
                                                        requested_user=request.requested_user,
                                                        request_type=request.request_type)
        if existing_request and existing_request.request_state != 0:
            return None
        if existing_request:
            request.event_id = existing_request.event_id
        request.save_to_db()
        return request

    @jwt_required
    def get(self):
        cleanExpired()
        current_user = get_jwt_identity()
        received_requests = RequestModel.get_received_requests(current_user)
        sent_requests = RequestModel.get_active_sent_requests(username=current_user)
        if None == received_requests or None == sent_requests:
            return {'message': 'User not found'}, 404
        return {"received_requests":[request.json() for request in received_requests],
                "sent_requests":[request.json() for request in sent_requests]}

    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('requested_user', type=str, required=True, help='Must enter the store id')
        parser.add_argument('requested_user_list', type=str, required=True, help='Must enter the store id')
        parser.add_argument('request_expiration_time', type=str, required=True, help='Must enter the store id')
        parser.add_argument('request_type', type=str, required=True, help='Must enter the store id')
        parser.add_argument('event_title', type=str, required=True, help='Must enter the store id')
        #parser.add_argument('event_location', type=str, required=True, help='Must enter the store id')
        parser.add_argument('access', type=str, required=True, help='Must enter the store id')
        parser.add_argument('duration', type=str, required=True, help='Must enter the store id')

        data = parser.parse_args()
        cleanExpired()

        current_time = datetime.datetime.now()
        expiration_time = current_time + datetime.timedelta(minutes=int(data["request_expiration_time"]))
        request_type = data["request_type"]
        current_user = get_jwt_identity()
        event_title = data["event_title"]
        #location = data["event_location"]
        duration = data["duration"]
        access = data["access"]
        event = Events.create_new_event( title=event_title, event_type=request_type,
                                         owner=current_user,access=access, location="",
                                         duration=duration)
        return_json = "" 
        if "" == data['requested_user_list']:
            request = RequestModel(request_state=0, requesting_user=current_user,
                               requested_user=data["requested_user"], request_time=str(current_time),
                               request_expiration_time=str(expiration_time),
                               request_type=request_type, event_id=event.id)

            Requests.add_new_request(request)
            return_json = request.json()
        else:
            requested_users = data['requested_user_list'].split(',')
            requests = [RequestModel(request_state=0, requesting_user=current_user,
                               requested_user=requested_user, request_time=str(current_time),
                               request_expiration_time=str(expiration_time),
                               request_type=request_type,event_id=event.id) for requested_user in requested_users]

            for request in requests:
                Requests.add_new_request(request)
            return_json = [request.json() for request in requests]
        return return_json

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('requesting_user', type=str, required=True, help='Must enter the store id')
        parser.add_argument('request_type', type=str, required=True, help='Must enter the store id')
        parser.add_argument('requested_user', type=str, required=False, help='Must enter the store id')

        data = parser.parse_args()
        cleanExpired()
        request_type_text = data["request_type"]
        requesting_user = data["requesting_user"]
        requested_user = data["requested_user"]
        if request_type_text in RequestModel.request_types:
            request_type = RequestModel.request_types.index(request_type_text)
        else:
            return {'message': 'request type not found'}, 404
        

        current_user = get_jwt_identity()
        if current_user != requesting_user and current_user != requested_user:
            return {'message': 'access denied'}, 404
        
        if requested_user:
            RequestModel.clear_requests(requesting_user=requesting_user,
                                        requested_user=requested_user,
                                        request_type=request_type)
        else:
            RequestModel.clear_requests(requesting_user=requesting_user, 
                                        request_type=request_type)
            RequestModel.clear_requests(requested_user=requesting_user,
                                        request_type=request_type,
                                        request_state=1)
        cleanExpired()
        return {'message': 'delete success'}