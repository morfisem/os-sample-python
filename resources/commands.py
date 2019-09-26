from flask_restful import Resource, reqparse
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from models.commands import CommandModel
import json


class Commands(Resource):
    @classmethod 
    def add_command(cls, command_type, params):
        command = CommandModel(command_type, params)
        command.save_to_db()
        return command
    @classmethod
    def create_group(cls, participants, title, event_id):
        params = {}
        params["title"] = title
        params["event_id"] = event_id
        params["participants"] = participants
        cls.add_command(1, json.dumps(params))
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()        
        if current_user != 'admin':
            return {'message': 'Access Denied'}, 404
        
        command = CommandModel.get_next_command()
        if command:
            CommandModel.command_delivered(command.id)
            return command.json()

        return {'message': 'No Commands'}, 404

    @jwt_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('command_id', type=str, required=True, help='Must enter id')

        data = parser.parse_args()
        command_id = data['command_id']
        if not command_id:
            return {'message': 'Command id not found'}, 404
        
        command = CommandModel.ack_command(command_id)
        if not command:
            return {'message': 'Command not found'}, 404
        return command.json()