from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

app = Flask(__name__)
app.secret_key = '91992610ba585f32948fb021041be673ee8d46745a2a52c6'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
CLIENT_SECRETS_FILE = "/workspaces/syllabus_suggestions/credentials/client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri='http://localhost:8080/oauth2callback'
)

@app.route('/')
def index():
    return '<a href="/authorize">Authorize</a>'

@app.route('/authorize')
def authorize():
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('get_calendar'))

@app.route('/get_calendar')
def get_calendar():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))
    
    credentials = Credentials(**session['credentials'])
    calendar_service = build('calendar', 'v3', credentials=credentials)
    events_result = calendar_service.events().list(calendarId='primary').execute()
    
    events = events_result.get('items', [])
    return f"Calendar events: {events}"

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8080)
