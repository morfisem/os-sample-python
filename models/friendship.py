from db import db

class FriendshipModel(db.Model):
    __tablename__ = 'friendships'

    id = db.Column(db.Integer, primary_key=True)
    main_user = db.Column(db.String(80))
    other_user = db.Column(db.String(80))
    friend_type = db.Column(db.Integer)

    def __init__(self, main_user, other_user, friend_type):
        self.main_user = main_user
        self.other_user = other_user
        self.friend_type = friend_type

    def json(self):
        return {'main_user': self.main_user, 'other_user': self.other_user,
                'type:': FriendshipModel.type_tostring(self.friend_type)}

    @classmethod
    def get_user_friends(cls, main_user, friend_type):
        friend_list = cls.query.filter_by(main_user=main_user, friend_type=friend_type)
        return friend_list.all()

    @classmethod
    def get_friendship(cls, main_user, other_user):
        friendship = cls.query.filter_by(main_user=main_user, other_user=other_user)
        return friendship.first()

    @staticmethod
    def type_tostring(friend_type):
        type_map = {1: "friend", 2: "pal"}
        return type_map[friend_type]

    @staticmethod
    def type_fromstring(friend_type):
        type_map = {"friend": 1, "pal": 2}
        return type_map[friend_type]

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()