from flask import Flask, redirect, session, request
import google.oauth2.credentials
import google_auth_oauthlib.flow
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET', 'default_fallback_secret_key')

scopes = ['https://www.googleapis.com/auth/calendar.events.owned.readonly']
cred = "credential.json"
redirect_uri = "http://localhost:8000/callback"


@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/login")
def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file (
        cred, scopes=scopes)
    flow.redirect_uri = redirect_uri
    authorization_url, state = flow.authorization_url (
        access_type='offline',
        include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    state = session.get('state')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        cred, scopes=scopes, state=state)
    flow.redirect_uri = redirect_uri
    if state != request.args.get('state'):
        return "Error: State mismatch. Possible CSRF attack.", 400
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    return f"Access Token: {credentials.token}"

if __name__ == "__main__":
    app.run(port=8000, debug=True)