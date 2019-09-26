from models.requests import RequestModel
from models.event import EventModel

def cleanExpired():
    RequestModel.clear_expired()
    RequestModel.filter_duplicates()
    #EventModel.clear_events()
    passive_events = EventModel.find_by_state(0)
    RequestModel.clear_abandoned(passive_events)

