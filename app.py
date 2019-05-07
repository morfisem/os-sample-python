from flask import Flask, request
from flask_jwt_extended import JWTManager, utils
from flask_jwt import _jwt
from flask_restful import Api
import json
import datetime

from sqlalchemy.dialects import sqlite, postgresql, mysql

from sqlConfig import sqliteConfig, postgresqlConfig, mysqlConfig
from resources.user import UserRegister, UserLogin, UserLogoutAccess, UserLogoutRefresh, AllUsers, TokenRefresh, UserSettings
from resources.userInfo import UserInfo
from resources.chats import Chats, Messages, ChatAck
from resources.friendship import Friendship
from resources.matches import Requests, ConfirmRequest, JoinEvent, PostponedRequest
from resources.event import Events

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


@app.before_first_request
def create_tables():
    db.create_all()


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

# user operations
api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogoutAccess, '/logout/access')
api.add_resource(UserLogoutRefresh, '/logout/refresh')
api.add_resource(TokenRefresh, '/token/refresh')
api.add_resource(AllUsers, '/users')
api.add_resource(UserSettings, '/user_settings')

chat_clients_sid = {}
username_timestamps = {}
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
        print("passed on message")


@socketio.on('disconnect')
def on_disconnect():
    if request.sid in chat_clients_sid:
        username_timestamps[chat_clients_sid[request.sid]] = datetime.datetime.now().timestamp()

@socketio.on('JOIN_CHAT')
def on_chat(data):
    room = data['chat_id']
    token = data['token']
    username = valiidate_chat_event(token)
    #TODO check room is for user
        
    if username :
        join_room(room)
        chat_clients_sid[request.sid] = username

@socketio.on('LEAVE_CHAT')
def on_leave(data):
    print("left chat!")
    token = data['token']
    room = data['room']
    username = valiidate_chat_event(token)
    if username:
        leave_room(room)

if __name__ == '__main__':
    app.run(debug=True)  # important to mention debug=True
