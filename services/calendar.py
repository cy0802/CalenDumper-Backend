from models import db, User, Note
from sqlalchemy.dialects.mysql import insert
import requests
from datetime import datetime
from sqlalchemy.exc import IntegrityError

def get_default_calendar_id(access_token):
    result = requests.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary", 
        headers={"Authorization": f"Bearer {access_token}"} 
    ).json()
    return result['id']

def sync_events(access_token, user_id, calendar_id, start_time, end_time):
    result = requests.get(
        f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events", 
        headers={"Authorization": f"Bearer {access_token}"}, 
        params={"timeMin": start_time, "timeMax": end_time}
    ).json()
    print(result)
    events = result.get('items', [])
    notes = [
        {
            'user_id': user_id,
            'event_id': event['id'],
            'event_start': event['start']['dateTime'],
            'event_end': event['end']['dateTime'],
            'event_summary': event.get('summary', 'No Title'),
            'text': '',
            'picture': ''
        }
        for event in events
    ]
    print(notes)
    
    stmt = insert(Note).values(notes)
    # stmt = stmt.prefix_with('IGNORE')
    print(stmt)
    try:
        print("try")
        db.session.execute(stmt)
        db.session.commit()
    except IntegrityError:
        print("integrity error")
        db.session.rollback()


def get_events(access_token, user_id, calendar_id, date):
    start_time = f"{date}T00:00:00.000Z"
    end_time = f"{date}T23:59:59.000Z"
    sync_events(access_token, user_id, calendar_id, start_time, end_time)
    events = Note.query.filter(Note.event_start >= start_time, Note.event_end <= end_time).all()
    return events
    