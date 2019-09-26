from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from models.idea import IdeaModel, SwipeModel, IgnoreModel
import datetime
from resources.event import Events
from models.event import EventModel
from resources.chats import Chats
from resources.commands import Commands
from resources.cleaner import cleanExpired


class Ideas(Resource):
    @jwt_required
    def get(self):
        SwipeModel.clear_expired()
        current_user = get_jwt_identity()
        user_swipes = SwipeModel.find_by_username(username=current_user)
        ideas = IdeaModel.get_all_verified()
        if None == ideas or None == user_swipes:
            return {'message': 'Ideas not found'}, 404
        
        user_swipe_ids = [swipe.idea_id for swipe in user_swipes]
        user_ideas = [idea.json() for idea in ideas if idea.id not in user_swipe_ids]
        return user_ideas
    
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('icon', type=str, required=True)
        parser.add_argument('title', type=str, required=True)
        parser.add_argument('category', type=str, required=True)
        parser.add_argument('description', type=str, required=True)
        data = parser.parse_args()

        icon = data["icon"]
        title = data["title"]
        category = data["category"]
        description = data["description"]
        new_idea = IdeaModel(title=title, category=category, event_time="", location="", description=description,
                 icon=icon, request_expiration_time="", min_amount=2, max_amount=100, owner=current_user)
        
        new_idea.save_to_db()
        
        return new_idea.json()

class Matches(Resource):    
    @classmethod
    def get_matching_users(cls, event, event_viewers):
        events_attendies = event.participants.split(',')
        event_ignores = [ignore.username for ignore in IgnoreModel.find_by_event(event_id=event.id)]

        if event.owner not in events_attendies:
            events_attendies.append(event.owner)
        
        if 0 == event.event_state:
            return events_attendies
        
        if not event.idea_id:
            return []
        
        matches = []
        event_swipes = SwipeModel.find_by_idea(idea_id=event.idea_id, confirm=1)
        for swipe in event_swipes:
            if swipe.username in events_attendies or swipe.username not in event_viewers:
                continue
            if swipe.username in event_ignores:
                continue
            if 0 == swipe.group_id:
                matches.append(swipe.username)
                continue
            
            friends = SwipeModel.get_friends(username=swipe.username, friend_type=swipe.group_id)
            if friends in events_attendies:
                matches.append(swipe.username)
                continue
        return matches
    
    @classmethod
    def get_match_for_swipe(cls, swipe):
        if 0 == swipe.confirm:
            return []
        
        user_events = EventModel.find_by_username(username=swipe.username)
        user_ignores = [ignore.event_id for ignore in IgnoreModel.find_by_username(username=swipe.username)]
        matches = []
        for event in user_events:
            events_attendies = event.participants.split(',')
            events_attendies.append(event.owner)
            if event.id in user_ignores:
                continue
            if event.event_state == 1 and event.idea_id == swipe.idea_id and swipe.username not in events_attendies:
                    if 0 == swipe.group_id:
                        matches.append(event.id)
                        continue
                    swipe_friends = SwipeModel.get_friends(username=swipe.username, friend_type=swipe.group_id)
                    event_friends = [user for user in events_attendies if user in swipe_friends] 
                    if  len(event_friends) > 0 :
                        matches.append(event.id)
        return matches
            
    @classmethod
    def get_matching_events(cls, current_user, user_events):
        user_swipes = SwipeModel.find_by_username(username=current_user, confirm=1)
        user_ideas = [user_swipe.idea_id for user_swipe in user_swipes]
        user_ignores = [ignore.event_id for ignore in IgnoreModel.find_by_username(username=current_user)]
        friends = {1: SwipeModel.get_friends(username=current_user, friend_type=1),
                    2: SwipeModel.get_friends(username=current_user, friend_type=2)}
        matches = []
        for event in user_events:
            events_attendies = event.participants.split(',')
            if current_user in events_attendies or current_user == event.owner:
                continue
            if not event.idea_id or event.id in user_ignores:
                continue
            
            event_swipe = None
            for swipe in user_swipes:
                if swipe.idea_id == event.idea_id:
                    event_swipe = swipe
                    break
            if not event_swipe:
                continue
            
            if 0 == event_swipe.group_id:
                matches.append(event.id)
                continue
            
            swipe_friends = friends[event_swipe.group_id]
            
            event_friends = [user for user in events_attendies if user in swipe_friends] 
            if  len(event_friends) > 0 :
                matches.append(event.id)
        return matches
    
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user_events = EventModel.find_by_username(username=current_user)
        user_active_events = [ event for event in user_events if event.event_state == 1]
        user_passive_events = [ event for event in user_events if event.event_state == 0]

        matching_events = Matches.get_matching_events(current_user, user_active_events)
        print("matching_events",matching_events)
        for event in user_passive_events:
            if current_user in event.participants.split(',') or current_user == event.owner:
                matching_events.append(event.id)

        return [{"event_id": match} for match in matching_events]

class Swipes(Resource):
    @classmethod
    def process_swipe(cls, username, idea_id):
        
        matches = SwipeModel.check_for_matches("safe", True)
        for idea_id in matches:
            idea_matches = matches[idea_id]
            idea = IdeaModel.find_by_id(idea_id)
            if not idea:
                continue
            for matched_group in idea_matches:
                #TO DO: acknolage min amount, max amount, access, duration
                event = Events.create_new_event( title=idea.title, event_type=idea.category,
                                         owner=username,access=1, location=idea.location, 
                                         duration=120, participants=",".join(matched_group), 
                                         event_time=idea.event_time,icon=idea.icon, idea_id=idea_id, description=idea.description)
                Chats.create_chat(event_time=event.event_time, event_id=event.id)
                Commands.create_group(event.participants, event.title, event.id)
                

                for matched_user in matched_group:
                    SwipeModel.ack_swipe(username=matched_user, idea_id=idea_id)
        #cleanExpired()
    
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('confirm', type=str, required=True, help='Must enter the store id')
        parser.add_argument('idea_id', type=str, required=True, help='Must enter the store id')
        parser.add_argument('group', type=str, required=True, help='Must enter the store id')
        data = parser.parse_args()

        idea_id = data["idea_id"]
        group = data["group"]
        group_id = SwipeModel.group_ids[group]
        
        confirm = data["confirm"]
        idea = IdeaModel.find_by_id(id=idea_id)
        
        if None == idea:
            return {'message': 'idea not found'}, 404
        
        current_time = datetime.datetime.now()
        swipe_expiration_time = current_time + datetime.timedelta(minutes=int(idea.request_expiration_time))

        existing_swipe = SwipeModel.find_by_filter(idea_id=idea_id, username=current_user)
        
        current_swipe = None
        if None == existing_swipe:
            current_swipe = SwipeModel(username=current_user, idea_id=idea_id, confirm=confirm,
                                swipe_expiration_time= swipe_expiration_time, group_id=group_id, matched=0)
        else:
            existing_swipe.confirm = confirm
            existing_swipe.swipe_expiration_time = swipe_expiration_time
            existing_swipe.group_id = group_id
            existing_swipe.matched = 0
            current_swipe = existing_swipe
        
        current_swipe.save_to_db()
        Swipes.process_swipe(username=current_user, idea_id=idea_id)
        matches = Matches.get_match_for_swipe(current_swipe)
        return [{"event_id": match} for match in matches]

class Ignore(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=str, required=True)
        data = parser.parse_args()

        event_id = data["event_id"]
        ignore = IgnoreModel(username=current_user, event_id=event_id)
        if not ignore:
            return {'ignore': 'failed to ignore'}, 404
        ignore.save_to_db()
        return {"event_id":event_id}
