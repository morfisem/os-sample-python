from flask_jwt_extended import (jwt_required, get_jwt_identity)
from flask_restful import Resource, reqparse
from models.friendship import FriendshipModel
from models.user import UserModel
from models.userInfo import UserInfoModel


class Friendship(Resource):
    @jwt_required
    def get(self, friend_type_string):
        current_user = get_jwt_identity()
        friend_type = FriendshipModel.type_fromstring(friend_type_string)
        friendshipList = FriendshipModel.get_user_friends(main_user=current_user, friend_type=friend_type)
        friends_with_info = [UserInfoModel.find_by_name(friendship.other_user) for friendship in friendshipList]
        if not friends_with_info:
            return []
        return [friend.json() for friend in friends_with_info]

    @jwt_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('friend', type=str, required=True, help='Must enter the store id')
        parser.add_argument('friend_type', type=str, required=True, help='Must enter the store id')

        data = parser.parse_args()
        other_user = data['friend']
        current_user = get_jwt_identity()

        if other_user == current_user:
            return {'message': 'friend same as user'}, 404
        
        friend_type = FriendshipModel.type_fromstring(data['friend_type'])
        friendship = FriendshipModel.get_friendship(main_user=current_user, other_user=other_user)

        if not friendship:
            friendship = FriendshipModel(main_user=current_user, other_user=other_user, friend_type=friend_type)
            friendship.save_to_db()
        elif friendship.friend_type != friend_type:
            friendship.friend_type = friend_type
            friendship.save_to_db()

        return friendship.json()

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        current_user = get_jwt_identity()
        parser.add_argument('friend', type=str, required=True, help='Must enter the store id')

        data = parser.parse_args()
        other_user = data['friend']

        friendship = FriendshipModel.get_friendship(main_user=current_user, other_user=other_user)

        if not friendship:
            print("here not found")
            return {'message': 'friend not found'}, 404

        friendship.delete_from_db()

        return friendship.json()
