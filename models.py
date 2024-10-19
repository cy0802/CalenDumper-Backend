from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User model
class User(db.Model):
    __tablename__ = 'users'  # Best practice: plural table names

    id = db.Column(db.String(100), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    calendar_id = db.Column(db.String(255), nullable=True)

    notes = db.relationship('Note', backref='user', lazy=True)
    dumps = db.relationship('Dump', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

# Note model
class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    # if event_id is null, this event does not belong to a calendar event
    event_id = db.Column(db.String(255), nullable=True)
    event_start = db.Column(db.DateTime, nullable=True)
    event_end = db.Column(db.DateTime, nullable=True)
    event_summary = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=True)
    picture = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Note {self.event_summary}>"

# Dump model
class Dump(db.Model):
    __tablename__ = 'dumps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('users.id'), nullable=False)
    picture = db.Column(db.String(255), nullable=True)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Dump {self.id}>"
