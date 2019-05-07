from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from models.userInfo import UserInfoModel


class UserInfo(Resource):
    @jwt_required  # Requires dat token
    def get(self):
        current_user = get_jwt_identity()
        user_info = UserInfoModel.find_by_name(current_user)
        if user_info:
            return user_info.json()
        return {'message': 'User info not found'}, 404

    @jwt_required
    def put(self):
        parser = reqparse.RequestParser()
        current_user = get_jwt_identity()
        parser.add_argument('email', type=str, required=True, help='Must enter the store id')
        parser.add_argument('first_name', type=str, required=True, help='Must enter the store id')
        parser.add_argument('last_name', type=str, required=True, help='Must enter the store id')

        # Create or Update
        data = parser.parse_args()
        info = UserInfoModel.find_by_name(current_user)

        if info is None:
            info = UserInfoModel(current_user, data['email'], data['first_name'], data['last_name'])
        else:
            info.email = data['email']
            info.first_name = data['first_name']
            info.last_name = data['last_name']

        info.save_to_db()

        return info.json()