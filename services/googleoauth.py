import google.oauth2.credentials
import google_auth_oauthlib.flow
from flask import session, request
import requests

# scopes = ['https://www.googleapis.com/auth/calendar.events.owned.readonly']
cred = "credential.json"
redirect_uri = "http://localhost:8000/callback"

def authorize(scopes):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file (
        cred, scopes=scopes
    )
    flow.redirect_uri = redirect_uri
    authorization_url, state = flow.authorization_url (
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return authorization_url

def oauth_callback(scopes):
    state = session.get('state')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        cred, scopes=scopes, state=state)
    flow.redirect_uri = redirect_uri
    if state != request.args.get('state'):
        return "Error: State mismatch. Possible CSRF attack.", 400
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    return credentials.token

def refresh():
    pass

def get_userinfo(access_token):
    result = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo", 
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    return result