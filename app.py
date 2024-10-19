from flask import Flask, redirect, request, jsonify, g
from services.googleoauth import authorize, oauth_callback, refresh, get_userinfo
from services.calendar import get_default_calendar_id, get_events
from dotenv import load_dotenv
import os
import jwt
from models import db, User, Note, Dump
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET', 'default_fallback_secret_key')
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
login_manager = LoginManager()
login_manager.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///default.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

class User_Login(UserMixin):
    def __init__(self, email, access_token):
        self.id = email
        self.email = email
        self.access_token = access_token
        print(access_token)
        exist_user = User.query.filter_by(email=email).first()
        if not exist_user:
            db.session.add(User(id=email, email=email, calendar_id=get_default_calendar_id(access_token)))
            db.session.commit()
        exist_user = User.query.filter_by(email=email).first()
        self.calendar_id = exist_user.calendar_id
    
    def set_calendar_id(self, calendar_id):
        self.calendar_id = calendar_id
        user = User.query.filter_by(email=self.email).first()
        user.calendar_id = calendar_id
        db.session.commit()
    
    def generate_token(self):
        return jwt.encode({'email': self.email}, app.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        try:
            return jwt.decode(token, app.secret_key, algorithms=['HS256'])['email'] == self.email
        except:
            return False

    def get_id(self):
        return self.id
    
    def get_access_token(self):
        return self.access_token

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') or request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = users.get(data['email'])
            print(data)
            print(data['email'])
            print(current_user)
            if not current_user or not current_user.verify_token(token):
                return jsonify({'message': 'Token is invalid!'}), 401
            g.current_user = current_user
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(*args, **kwargs)
    return decorated

def get_current_user(jwt_token):
    jwt_token = jwt_token.split(" ")[1]
    print(jwt.decode(jwt_token, app.secret_key, algorithms=["HS256"])['email'])
    return users.get(jwt.decode(jwt_token, app.secret_key, algorithms=["HS256"])['email'])

users = {}

scopes = [
    'https://www.googleapis.com/auth/calendar.events.owned.readonly', 
    "https://www.googleapis.com/auth/calendar.readonly",
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/login", methods=['GET'])
def login():
    authorization_url = authorize(scopes)
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    access_token = oauth_callback(scopes)
    # query userinfo
    userinfo = get_userinfo(access_token)
    
    # login user
    global users
    users.update({userinfo['email']: User_Login(userinfo['email'], access_token)})
    login_user(users[userinfo['email']])

    return redirect(f"{frontend_url}?token={users[userinfo['email']].generate_token()}")

@app.route("/event/<date>", methods=['GET'])
@token_required
def events(date):
    token = request.headers.get('Authorization')
    user = get_current_user(token)
    events = get_events(user.access_token, user.id, user.calendar_id, date)
    return jsonify([{
        'event_id': event.event_id,
        'start_time': event.event_start,
        'end_time': event.event_end,
        'title': event.event_summary,
        'text': event.text,
        'picture': event.picture
    } for event in events])

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(port=8000, debug=True)