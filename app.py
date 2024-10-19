from flask import Flask, redirect, request
from services.googleoauth import authorize, oauth_callback, refresh
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET', 'default_fallback_secret_key')
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

scopes = ['https://www.googleapis.com/auth/calendar.events.owned.readonly']

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/login")
def login():
    authorization_url = authorize(scopes)
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    access_token = oauth_callback(scopes)
    return redirect(frontend_url)

if __name__ == "__main__":
    app.run(port=8000, debug=True)