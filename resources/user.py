from flask_restful import Resource, reqparse
from models.user import UserModel, RevokedTokenModel
from models.userInfo import UserInfoModel, UserSettingsModel
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
import datetime


class UserRegister(Resource):
    parser = reqparse.RequestParser()  # only allow price changes, no name changes allowed
    parser.add_argument('username', type=str, required=True, help='This field cannot be left blank')
    parser.add_argument('password', type=str, required=True, help='This field cannot be left blank')
    parser.add_argument('email', type=str, required=True, help='This field cannot be left blank')
    parser.add_argument('first_name', type=str, required=True, help='This field cannot be left blank')
    parser.add_argument('last_name', type=str, required=True, help='This field cannot be left blank')

    def get(self):
        return self.post()

    def post(self):
        data = UserRegister.parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {'message': 'UserModel has already been created, aborting.'}, 400

        try:
            user = UserModel(username=data['username'], password=UserModel.generate_hash(data['password']))
            info = UserInfoModel(username=data['username'], email=data['email'], first_name=data['first_name'],
                                 last_name=data['last_name'])

            user.save_to_db()
            info.save_to_db()

            access_token = create_access_token(identity=data['username'], expires_delta=datetime.timedelta(hours=2))
            refresh_token = create_refresh_token(identity=data['username'])
            return {
                'message': 'User {} was created'.format(data['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True, help='This field cannot be left blank')
    parser.add_argument('password', type=str, required=True, help='This field cannot be left blank')

    #todo - remove this
    def get(self):
        return self.post()

    def post(self):
        data = UserLogin.parser.parse_args()
        current_user = UserModel.find_by_username(data['username'])

        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['username'])}

        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity = data['username'], expires_delta=datetime.timedelta(hours=2))
            refresh_token = create_refresh_token(identity = data['username'])
            return {
                'message': 'Logged in as {}'.format(current_user.username),
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': current_user.username}
        else:
            return {'message': 'Wrong credentials'}


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti = jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user, expires_delta=datetime.timedelta(hours=2))
        return {'access_token': access_token}


class AllUsers(Resource):
    @jwt_required
    def get(self):
        users = UserModel.query.all()
        users_with_info = [UserInfoModel.find_by_name(user.username).json() for user in users]
        return {'users': users_with_info}


class UserSettings(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        settings = UserSettingsModel.find_by_username(username=current_user)
        if settings:
            return settings.json()
        else:
            return {'message': 'User not found'}, 404