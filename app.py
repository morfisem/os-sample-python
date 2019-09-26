import time
from flask import Flask, request
from flask_jwt_extended import JWTManager, utils
from flask_jwt import _jwt
from flask_restful import Api
import json
import datetime
import eventlet
eventlet.monkey_patch()

from sqlalchemy.dialects import sqlite, postgresql, mysql

from sqlConfig import sqliteConfig, postgresqlConfig, mysqlConfig
from resources.user import UserRegister, UserLogin, UserLogoutAccess, UserLogoutRefresh, AllUsers, TokenRefresh, UserSettings
from resources.userInfo import UserInfo
from resources.chats import Chats, Messages, ChatAck
from resources.friendship import Friendship
from resources.matches import Requests, ConfirmRequest, JoinEvent, PostponedRequest
from resources.event import Events
from resources.idea import Ideas, Swipes, Matches, Ignore
from resources.commands import Commands

from models.user import RevokedTokenModel
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
from db import db

app = Flask(__name__)
CORS(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = postgresqlConfig
app.config['SQLALCHEMY_DATABASE_URI'] = sqliteConfig #sqliteConfig
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
################################################################
app.config['PROPAGATE_EXCEPTIONS'] = True
################################################################
app.secret_key = 'Dese.Decent.Pups.BOOYO0OST'
api = Api(app)
db.init_app(app)

def get_events(app):
    #global socketio  
    global chat_clients_sid
    print('thread strarted')
    
    with app.app_context():
        all_events = []
        while True:
            time.sleep(5)
            if len(all_events) == 0:
                all_events = Events.get_all()
                continue
            
            new_all_events = Events.get_all()
            all_events_ids = [event.id for event in all_events]
            new_events = [event for event in new_all_events if event.id not in all_events_ids]
            all_events = new_all_events
            if 0 == len(new_events):
                continue
            print("chat_clients_sid",chat_clients_sid)
            print("!!!!new_all_events,all_events,new_events",new_all_events,all_events_ids,new_events)

            for event in new_events:
                print('in new event!', event)
                users = event.get_event_viewers()
                if None == users:
                    users = chat_clients_sid.keys()
                print('viewers', users)
                matching_users = Matches.get_matching_users(event, users)
                for user in users:
                    if user in chat_clients_sid:
                        event_json = event.json()
                        event_json['match'] = user in matching_users
                        socketio.emit('NEW_EVENT', json.dumps(event_json), room=chat_clients_sid[user])

app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
jwt = JWTManager(app)
socketio = SocketIO(app)
# jwt = JWT(app, authenticate, identity)  # Auto Creates /auth endpoint
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)


@app.before_first_request
def create_tables():
    db.create_all()
    greenth = eventlet.spawn(get_events, app) 

# Fika operations
api.add_resource(UserInfo, '/info')
api.add_resource(Friendship, '/friends/<string:friend_type_string>', '/set_friend')
api.add_resource(Events, '/events')
api.add_resource(Requests, '/requests', '/send_request')
api.add_resource(ConfirmRequest, '/confirm')
api.add_resource(PostponedRequest, '/Later')
api.add_resource(JoinEvent, '/join_event/<int:event_id>')
api.add_resource(Chats, '/chats', '/create_chat')
api.add_resource(ChatAck, '/chat_ack/<int:chat_id>')
api.add_resource(Messages, '/messages/<int:chat_id>')
api.add_resource(Ideas, '/ideas')
api.add_resource(Swipes, '/swipe')
api.add_resource(Matches, '/matches')
api.add_resource(Ignore, '/ignore')
api.add_resource(Commands, '/commands')


# user operations
api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogoutAccess, '/logout/access')
api.add_resource(UserLogoutRefresh, '/logout/refresh')
api.add_resource(TokenRefresh, '/token/refresh')
api.add_resource(AllUsers, '/users')
api.add_resource(UserSettings, '/user_settings')

chat_clients_sid = {}
def valiidate_chat_event(token):
    try:
        value = utils.decode_token(token)
        return value["identity"]
    except Exception as e:
        return None

@socketio.on('SEND_MESSAGE')
def handle_my_custom_event(json_value, methods=['GET', 'POST']):
    username = valiidate_chat_event(json_value['token'])
    if not username:
        socketio.emit('ACCESS_DENIED')
        print("access_denied")
        return

    message = Messages.add_message(chat_id=json_value['chat_id'],
                                    username=username,
                                    content=json_value['content'])
    if message:
        socketio.emit('NEW_MESSAGE', json.dumps(message.json()), room=message.chat_id)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in chat_clients_sid.values():
        users = [user for user in chat_clients_sid if request.sid == chat_clients_sid[user]]
        for user in users:
            chat_clients_sid.pop(user, None)

@socketio.on('INIT_USER')
def on_user_init(data):
    token = data['token']
    username = valiidate_chat_event(token)
        
    if username :
        chat_clients_sid[username] = request.sid

@socketio.on('JOIN_CHAT')
def on_chat(data):
    room = data['chat_id']
    token = data['token']
    username = valiidate_chat_event(token)
    #TODO check room is for user
        
    if username :
        join_room(room)
        chat_clients_sid[username] = request.sid

@socketio.on('LEAVE_CHAT')
def on_leave(data):
    token = data['token']
    room = data['room']
    username = valiidate_chat_event(token)
    if username:
        leave_room(room)

if __name__ == '__main__':
    #app.run(debug=False)  # important to mention debug=True
    #socketio.run(app, host='0.0.0.0', port=8080)
    socketio.run(app, host='0.0.0.0', port=5000,debug=True) 