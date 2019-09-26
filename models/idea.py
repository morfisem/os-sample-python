from db import db
import networkx as nx
from models.friendship import FriendshipModel
from models.requests import RequestModel
import datetime


class IdeaModel(db.Model):
    __tablename__ = 'ideas'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    category = db.Column(db.String(80))
    event_time = db.Column(db.String(80))
    location = db.Column(db.String(80))
    #description = db.Column(db.BLOB)
    description = db.Column(db.String(300))
    icon = db.Column(db.String(300))
    request_expiration_time = db.Column(db.String(80))
    min_amount = db.Column(db.Integer)
    max_amount = db.Column(db.Integer)
    verified = db.Column(db.Integer)
    owner = db.Column(db.String(80))

    def __init__(self, title, category, event_time, location, description,
                 icon, request_expiration_time, min_amount, max_amount,owner, verified=0):
        self.title = title
        self.category = category
        self.event_time = event_time
        self.location = location
        self.description = description
        self.icon = icon
        self.request_expiration_time = request_expiration_time
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.verified = verified
        self.owner = owner

    def json(self):
        return {'id':self.id, 'title': self.title, 'category': self.category, 'event_time:': self.event_time,
                'location': self.location, 'description': self.description, 'icon': self.icon,
                'request_expiration_time': self.request_expiration_time, "min_amount": self.min_amount, "max_amount": self.max_amount}

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    @classmethod
    def get_all_verified(cls):
        return cls.query.filter_by(verified=1).all()


class SwipeModel(db.Model):
    __tablename__ = 'swipes'

    group_ids = {"Friends":1, "Pals":2, "New People":3, "":0}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    idea_id = db.Column(db.Integer)
    group_id = db.Column(db.Integer)
    swipe_expiration_time = db.Column(db.String(80))
    confirm = db.Column(db.Integer)
    matched = db.Column(db.Integer)

    def __init__(self, username, idea_id, swipe_expiration_time, confirm, group_id, matched):
        self.username = username
        self.idea_id = idea_id
        self.swipe_expiration_time = swipe_expiration_time
        self.confirm = confirm
        self.group_id = group_id
        self.matched = matched

    def json(self):
        return {'id': self.id, 'username': self.username, 'swipe_expiration_time:': self.swipe_expiration_time,
                'idea_id': self.idea_id, 'confirm': self.confirm, "group_id": self.group_id, "matched": self.matched}

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def find_by_username(cls, username, confirm=None):
        if confirm:
            return cls.query.filter_by(username=username, confirm=confirm).all()
        return cls.query.filter_by(username=username).all()
    
    @classmethod
    def find_by_idea(cls, idea_id, confirm=None):
        if confirm:
            return cls.query.filter_by(idea_id=idea_id, confirm=confirm).all()
        return cls.query.filter_by(idea_id=idea_id).all()
    
    @classmethod
    def find_by_filter(cls, username, idea_id ):
        return cls.query.filter_by(username=username, idea_id=idea_id).first()
    
    @classmethod
    def ack_swipe(cls, username, idea_id ):
        swipe = cls.query.filter_by(username=username, idea_id=idea_id).first()
        if swipe:
            swipe.matched = 1
            swipe.save_to_db()
    @classmethod
    def get_friends(cls, username, friend_type):
        friendshipList = FriendshipModel.get_user_friends(main_user=username, friend_type=friend_type)
        return [friendship.other_user for friendship in friendshipList] 
    @classmethod
    def check_match_user(cls, swipe, other_user):
        if swipe.group_id == 0:
            return True
        friendshipList = SwipeModel.get_friends(username=swipe.username, friend_type=swipe.group_id)
        return other_user in friendshipList
    @classmethod
    def get_max_clique(cls, cliques):
        max_clique = []
        for clique in cliques:
            if len(clique) > len(max_clique):
                max_clique = clique
        return max_clique
    @classmethod
    def get_sorted_matches(cls, matches, mode, single):
        sorted_matches = {}
        for idea_id in matches:
            idea_matches = matches[idea_id]
            if not idea_matches:
                continue
            
            g = nx.Graph()
            for match in idea_matches:
                swipes1, swipes2  = list(match)
                g.add_edge(swipes1.username, swipes2.username)
            
            #print('graph!!!!',idea_id,g.nodes,g.edges,nx.k_components(g))
            #sorted_matches[idea_id] = nx.k_components(g)
            if mode == "inclusive":
                sorted_matches[idea_id] = nx.k_components(g)[1]

            elif mode == "safe" and not single:
                cliques = nx.algorithms.clique.find_cliques(g)
                sorted_matches[idea_id] = [set(clique) for clique in cliques]

            elif mode == "safe" and single:
                sorted_matches[idea_id] = []
                cliques = nx.algorithms.clique.find_cliques(g)
                max_clique = SwipeModel.get_max_clique(cliques)
                while len(max_clique) > 1:
                    sorted_matches[idea_id].append(set(max_clique))
                    g.remove_nodes_from(max_clique)
                    cliques = nx.algorithms.clique.find_cliques(g)
                    max_clique = SwipeModel.get_max_clique(cliques)                
                
        return sorted_matches
            
    @classmethod
    def check_for_matches(cls, mode, single):
        swipes = cls.query.filter_by(confirm=1, matched=0).all()
        sorted_swipes = {}
        matches = {}
        for swipe in swipes:
            if swipe.idea_id in sorted_swipes:
                sorted_swipes[swipe.idea_id].append(swipe)
            else:
                sorted_swipes[swipe.idea_id] = [swipe]
        for idea_id in sorted_swipes :
            matches[idea_id] = []
            swipe_list = sorted_swipes[idea_id]
            if len(swipe_list) < 2:
                continue
            for swipe1 in swipe_list:
                for swipe2 in swipe_list:
                    if swipe1 == swipe2:
                        continue
                    confirm1 = SwipeModel.check_match_user(swipe=swipe1,other_user=swipe2.username)
                    confirm2 = SwipeModel.check_match_user(swipe=swipe2,other_user=swipe1.username)
                    
                    if confirm1 and confirm2 and {swipe1,swipe2} not in matches[idea_id]:
                        matches[idea_id].append({swipe1,swipe2})
                    
        print('matches',matches)
        sorted_matches = SwipeModel.get_sorted_matches(matches, mode, single)
        print('sorted_matches',sorted_matches)
        return sorted_matches
    
    @classmethod
    def clear_expired(cls):
        current_time = datetime.datetime.now()
        swipes = cls.query.all()
        expired = []
        for swipe in swipes:
            if (not swipe.swipe_expiration_time or swipe.swipe_expiration_time == '' ):
                continue
            swipe_expiration_time = RequestModel.expiration_to_datetime(swipe.swipe_expiration_time)
            if current_time > swipe_expiration_time:
                expired.append(swipe)

        for swipe in expired:
            print('expired deleting:', swipe.json())
            swipe.delete_from_db()
        return expired


class IgnoreModel(db.Model):
    __tablename__ = 'user_ignore'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    event_id = db.Column(db.Integer)

    def __init__(self, username, event_id):
        self.username = username
        self.event_id = event_id
    
    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).all()
    @classmethod
    def find_by_event(cls, event_id):
        return cls.query.filter_by(event_id=event_id).all()
