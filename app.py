from flask import Flask, redirect, request, jsonify, g, send_from_directory
from flask_cors import CORS
from services.googleoauth import authorize, oauth_callback, refresh, get_userinfo
from services.calendar import get_default_calendar_id, get_events
from services.gemini import generate
from services.seeder import seed_notes
from dotenv import load_dotenv
import os
import jwt
from models import db, User, Note, Dump
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime

load_dotenv()

UPLOAD_FOLDER = 'picture/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv('APP_SECRET', 'default_fallback_secret_key')
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
login_manager = LoginManager()
login_manager.init_app(app)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///default.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route('/picture/<filename>')
def serve_picture(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/login", methods=['GET'])
def login():
    authorization_url = authorize(scopes, f"{backend_url}/callback")
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    access_token = oauth_callback(scopes, f"{backend_url}/callback")
    # query userinfo
    userinfo = get_userinfo(access_token)
    print(userinfo)
    
    # login user
    global users
    users.update({userinfo['email']: User_Login(userinfo['email'], access_token)})
    login_user(users[userinfo['email']])

    return redirect(f"{frontend_url}/?token={users[userinfo['email']].generate_token()}")

@app.route("/api/event/<date>", methods=['GET'])
@token_required
def events(date):
    token = request.headers.get('Authorization')
    user = get_current_user(token)
    events = get_events(user.access_token, user.id, user.calendar_id, date)
    # if events == -1:
    #     return jsonify({"message": "unauthorized"}), 401
    return jsonify([{
        'event_id': event.event_id,
        'start_time': event.event_start,
        'end_time': event.event_end,
        'title': event.event_summary,
        'note': event.text,
        'picture': event.picture
    } for event in events])

@app.route("/api/event/<event_id>/note", methods=['POST'])
@token_required
def add_note(event_id):
    token = request.headers.get('Authorization')
    user = get_current_user(token)
    event = Note.query.filter_by(event_id=event_id).first()
    if not event:
        return jsonify({'message': 'Event not found!'}), 404
    data = request.json
    event.text = data.get('note', '')
    db.session.commit()
    return jsonify({'message': 'Note added'})

@app.route("/api/event/<event_id>/picture", methods=['POST'])
@token_required
def add_picture(event_id):
    token = request.headers.get('Authorization')
    user = get_current_user(token)
    event = Note.query.filter_by(event_id=event_id).first()
    if not event:
        return jsonify({'message': 'Event not found!'}), 404
    if event.picture != '':
        return jsonify({'message': 'Picture already exists'}), 400
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Use secure_filename to sanitize the filename
        event_summary = secure_filename(event.event_summary)
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{event_id}_{event_summary}.{file_extension}"
        
        # Save the file to the specified folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Save the picture path to the event (assuming there is a picture field in the Note model)
        event.picture = filename
        db.session.commit()
        
        return jsonify({'message': 'Picture added successfully', 'filename': filename}), 200
    else:
        return jsonify({'message': 'Invalid file type. Allowed types: png, jpg, jpeg, gif'}), 400

# @app.route("/api/event", methods=['POST'])
# @token_required
# def add_event():
#     token = request.headers.get('Authorization')
#     user = get_current_user(token)
#     data = request.json
#     to_calandar = data['to_calendar']
#     event_id = hash((user.id, data['title'], data['start_time'], data['end_time']))
#     event_start = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
#     event_end = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
#     event = Note(
#         user_id=user.id,
#         event_id=event_id,
#         event_start=event_start,
#         event_end=event_end,
#         event_summary=data['title'],
#         text='',
#         picture=''
#     )
#     db.session.add(event)
#     db.session.commit()
#     # TODO: if to_calendar is True, add the event to the user's calendar
#     return jsonify({'message': 'Event added'})

@app.route("/generate", methods=['GET'])
@token_required
def call_gemini():
    token = request.headers.get('Authorization')
    user = get_current_user(token)
    return generate(user.id)

@app.route("/seed_notes")
def seed_notes_command():
    try:
        seed_notes()
        print("Notes seeded successfully!")
        return "Notes seeded successfully!", 200
    except Exception as e:
        print(f"Error seeding notes: {e}")
        return "An error occurred.", 500


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(port=8000, debug=True)