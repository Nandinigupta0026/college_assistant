import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    creds = None
    
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(
                port=8080,
                prompt="consent",
                access_type="offline"
            )
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    return build("calendar", "v3", credentials=creds)


def create_calendar_event(title, due_date, subject="General"):
    service = get_calendar_service()
    
    event = {
        "summary": f"📚 {title} - {subject}",
        "description": f"Assignment/Exam for {subject}",
        "start": {
            "date": due_date,  # YYYY-MM-DD format
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "date": due_date,
            "timeZone": "Asia/Kolkata"
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 2880},  # 2 days before
                {"method": "popup", "minutes": 1440},  # 1 day before
            ]
        }
    }
    
    event = service.events().insert(
        calendarId="primary", body=event
    ).execute()
    
    return f"✅ Added to Google Calendar: {title} on {due_date}"


def get_upcoming_events():
    service = get_calendar_service()
    
    now = datetime.datetime.utcnow().isoformat() + "Z"
    
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    
    if not events:
        return "No upcoming events found!"
    
    result = "Your upcoming events:\n"
    for event in events:
        start = event["start"].get("date", event["start"].get("dateTime", ""))
        result += f"- {event['summary']} → {start}\n"
    
    return result

def get_daily_summary():
    today = datetime.date.today()
    all_events=get_upcoming_events()
    
    todays_events = []
    upcoming_events = []
    
    for event in all_events.split("\n"):
        if str(today) in event:
            todays_events.append(event)
        else:
            upcoming_events.append(event)
            
    summary=f"Good Morning!\n\n"
    summary+=f"Today's Deadline:\n"
    
    for e in todays_events:
        summary+=f"  -{e}\n"
    summary+=f"\n Upcoming Deadline:\n"
    
    for e in upcoming_events:
        summary+=f"  -{e}\n"
        
    return summary             