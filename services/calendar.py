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
    response = requests.get(
        f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events", 
        headers={"Authorization": f"Bearer {access_token}"}, 
        params={"timeMin": start_time, "timeMax": end_time}
    )
    
    # if response.status_code == 401:
    #     return 1
    
    result = response.json()
    print(result)
    events = result.get('items', [])
    filtered_events = [
        event for event in events 
        if 'start' in event and 
            'end' in event and 
            'dateTime' in event['start'] and 
            'dateTime' in event['end'] and
            Note.query.filter_by(event_id=event['id']).first() is None
    ]
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
        for event in filtered_events
    ]
    print(notes)
    
    stmt = insert(Note).values(notes)
    stmt = stmt.prefix_with('IGNORE')
    print(stmt)
    try:
        print("try")
        db.session.execute(stmt)
        db.session.commit()
    except IntegrityError:
        print("integrity error")
        db.session.rollback()
    # return 0


def get_events(access_token, user_id, calendar_id, date):
    start_time = f"{date}T00:00:00.000Z"
    end_time = f"{date}T23:59:59.000Z"
    err = sync_events(access_token, user_id, calendar_id, start_time, end_time)
    # if err:
    #     return -1
    events = Note.query.filter(Note.user_id == user_id, Note.event_start >= start_time, Note.event_end <= end_time).order_by(Note.event_start).all()
    return events
    