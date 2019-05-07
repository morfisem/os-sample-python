from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from models.chat import ChatModel, MessageModel, ChatAckModel
import datetime
from models.event import EventModel
from models.requests import RequestModel


class Chats(Resource):
    @classmethod
    def create_chat(cls, event_time, event_id):
        current_time = datetime.datetime.now()
        expiration_time = RequestModel.expiration_to_datetime(event_time) + datetime.timedelta(hours=2)
        print("creating chat event time:",event_time, str(expiration_time), str(RequestModel.expiration_to_datetime(event_time)))
        chat = ChatModel(chat_creation_time=str(current_time), event_id=event_id,
                         chat_expiration_time=str(expiration_time))
        chat.save_to_db()
        return chat
    
    @jwt_required
    def get(self):
        ChatModel.clear_expired()
        current_user = get_jwt_identity()
        user_chats = ChatModel.find_by_username(current_user)
        if not user_chats:
            return {'message': 'User not found'}, 404
        
        chats_json = []
        for chat in user_chats:
            event = EventModel.find_by_id(chat.event_id)
            chats_json.append({'users': event.participants, "id": chat.id, "event_id": chat.event_id,
                                'title': event.title})
        return chats_json

    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=str, required=True, help='Must enter the store id')

        data = parser.parse_args()
        event_id = RequestModel.request_types.index(data['event_id'])
        current_chat = ChatModel.find_by_filters(event_id=event_id)
        if current_chat:
            return current_chat.json()

        event = EventModel.find_by_id(chat.event_id)
        if not event:
            return {'message': 'Event not found'}, 404
        
        chat = Chats.create_chat(event_time=event.event_time, event_type=event_type)
        
        return chat.json()


class Messages(Resource):
    @classmethod
    def get_chat_messages(cls, chat_id):
        return MessageModel.find_by_chat_id(chat_id=chat_id)

    @classmethod
    def add_message(cls, chat_id, username, content):
        current_time = datetime.datetime.now().timestamp()
        message = MessageModel(chat_id=chat_id, username=username, content=content, timestamp=str(current_time))
        message.save_to_db()
        ChatAck.add_ack(username=username,chat_id=chat_id)
        return message

    @jwt_required
    def get(self, chat_id):
        current_user = get_jwt_identity()
        chat = ChatModel.find_by_filters(id=chat_id)

        if not chat:
            return {'message': 'chat not found'}, 404

        user_events = EventModel.get_participant_events(username=current_user)
        if chat.event_id not in [user_event.id for user_event in user_events]:
            return {'message': 'Access Denied'}, 404

        messages = Messages.get_chat_messages(chat_id=chat_id)
        chat_ack = ChatAckModel.find_by_filters(chat_id=chat_id,username=current_user)
        if chat_ack:
            last_ack = chat_ack.timestamp
        else:
            last_ack = 0
        if messages:
            return {'messages': [message.json() for message in messages], "last_ack":last_ack}
        if messages == []:
            return {'messages':[],"last_ack":0}
        return {'message': 'User not found'}, 404

class ChatAck(Resource):
    @classmethod
    def add_ack(cls, chat_id, username):
        current_time = datetime.datetime.now().timestamp()
        chat_ack = ChatAckModel.find_by_filters(chat_id=chat_id,username=username)
        
        if chat_ack:
            chat_ack.timestamp = current_time
            chat_ack.save_to_db()
            return chat_ack
        else:
            new_chat_ack = ChatAckModel(username=username,timestamp=current_time,chat_id=chat_id)
            new_chat_ack.save_to_db()
            return new_chat_ack

    @jwt_required
    def post(self, chat_id):
        current_user = get_jwt_identity()

        chat = ChatModel.find_by_filters(id=chat_id)

        if not chat:
            return {'message': 'chat not found'}, 404

        user_events = EventModel.get_participant_events(username=current_user)
        if chat.event_id not in [user_event.id for user_event in user_events]:
            return {'message': 'Access Denied'}, 404
        
        result = ChatAck.add_ack(chat_id=chat_id,username=current_user)
        if not result:
            return {'message': 'chat ack error'}, 404
        return result.json()
