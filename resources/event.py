from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from models.requests import RequestModel
from models.event import EventModel

import datetime


class Events(Resource):
    @classmethod 
    def get_all(cls):
        return EventModel.get_all()
    @classmethod 
    def create_new_event(cls, title, event_type, owner,access, location, duration,
                        participants=None, event_time="", icon="", idea_id="", description=""):
        if not participants:
            participants=owner
        event = EventModel( title=title, event_time=event_time,
                            event_type=event_type, participants=participants,
                            event_state=0, access=access, location=location, 
                            duration=duration, owner=owner, icon=icon, idea_id=idea_id, description=description)
        event.save_to_db()
        return event
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user_events = EventModel.find_by_username(username=current_user)
        #all_events = EventModel.get_all()

        #for event in [e for e in all_events if e not in user_events]:
        #    print("left out event",current_user,event.id)

        #    print("left out event",current_user,event.id)
        
        if None == user_events:
            return {'message': 'Events not found'}, 404
        else:
            current_time = datetime.datetime.now()
            events_json = []
            for event in user_events:
                event_time = RequestModel.expiration_to_datetime(event.event_time)
                event_json = event.json()
                if not event_time:
                    event_json["future"] = True
                else:
                    event_json["future"] =  current_time < event_time
                
                if current_user == event.owner:
                    event_json["access"] =  event.access
                
                events_json.append(event_json)
            return events_json
        

    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        
        #parser.add_argument('event_type', type=str, required=True, help='Must enter the store id')
        #parser.add_argument('participants', type=str, required=True, help='Must enter the store id')
        
        parser.add_argument('event_id', type=str, required=True, help='Must enter the store id')
        #optional params
        parser.add_argument('event_time', type=str, required=False, help='Must enter the store id')
        parser.add_argument('title', type=str, required=False, help='Must enter the store id')
        parser.add_argument('event_location', type=str, required=False, help='Must enter the store id')
        parser.add_argument('access', type=str, required=False, help='Must enter the store id')
        parser.add_argument('duration', type=str, required=False, help='Must enter the store id')
        parser.add_argument('description', type=str, required=False, help='Must enter the store id')

        data = parser.parse_args()
        #event = Events.create_new_event( title=data["title"], event_time=data['event_time'], event_type=data['event_type'],
        #                     participants=data['participants'], event_state=0,access=data['access'],location=data['location'],
        #                     duration=data["duration"])
        
        event_id = data["event_id"]

        title = data["title"]
        event_location = data["event_location"]
        access = data["access"]
        duration = data["duration"]
        event_time = data["event_time"]
        description = data["description"] 

        event = EventModel.find_by_id(event_id)
        current_user = get_jwt_identity()
        if not event:
            return {'message': 'Event not found'}, 404
        elif current_user != event.owner:
            return {'message': 'Access Denied'}, 404
        
        if title:
            event.title = title
        if event_location:
            event.location = event_location
        if access:
            event.access = access
        if duration:
            event.duration = duration
        if description:
            event.description = description
        if event_time and RequestModel.expiration_to_datetime(event_time):
            event.event_time = event_time
            event.event_state = 1
        
        
        event.save_to_db()
        return event.json()