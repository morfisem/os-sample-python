from db import db


class CommandModel(db.Model):
    __tablename__ = 'commands'

    id = db.Column(db.Integer, primary_key=True)
    command_type = db.Column(db.Integer)
    params = db.Column(db.String(80))
    ack = db.Column(db.Integer)

    def __init__(self, command_type, params, ack=0):
        self.command_type = command_type
        self.params = params
        self.ack=ack

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_next_command(cls):
        return cls.query.filter_by(ack=0).first()
    
    @classmethod
    def ack_command(cls, command_id):
        command = cls.query.filter_by(id=command_id).first()
        if command:
            command.ack = 2
            command.save_to_db()
            return command
        return None
    
    @classmethod
    def command_delivered(cls, command_id):
        command = cls.query.filter_by(id=command_id).first()
        if command:
            command.ack = 1
            command.save_to_db()
            return command
        return None
    
    def json(self):
        return {'command_type': self.command_type,
                'params': self.params,
                "id": self.id}