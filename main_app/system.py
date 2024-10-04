import datetime
from typing import List, Dict
import re
from PyPDF2 import PdfReader
import smtplib
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import requests
from flask import Flask, Request, request, jsonify, session
from flask import Flask, request, jsonify, render_template_string
import random
from datetime import datetime, timedelta
import functools
import traceback
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter
import statistics
from flask import Flask, redirect, request, url_for, session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
from flask import Flask, redirect, request, url_for, session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import json
from flask_cors import CORS
import traceback
from flask import current_app as app
# Update your existing get_suggestions route
import json
from datetime import datetime, timedelta
import requests
from flask import jsonify

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://localhost:8080"}})# This will enable CORS for all routes
app.secret_key = 'bdccd44f9842c6f62cdd05cba47b7da861de0b662ec3fe24' 

def log_exceptions(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Exception in {f.__name__}: {str(e)}")
            traceback.print_exc()
            return f"<h2>Error:</h2><p>An unexpected error occurred. Please try again later. Error details: {str(e)}</p>"
    return wrapper

# Canvas API configuration
CANVAS_URL = 'https://canvas.illinois.edu'
ACCESS_TOKEN = '14559~Gk6LwhwGhxMXDtfK7WaRNYDfMRnr4kz8YukmVhwKDcycMXNZXerakVXfT2KnEZZW'  # Replace with your actual access token

class Student:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self.courses: List[Course] = []

class Course:
    def __init__(self, name: str, course_id: str, data: dict):
        self.name = name
        self.course_id = course_id
        self.total_students = data.get('total_students', 0)
        self.syllabus = data.get('syllabus_body', '')
        self.term = data.get('term', {}).get('name', 'No Term')
        self.state = data.get('workflow_state', 'Unknown State')
        self.grading_structure = self.parse_grading_structure(self.syllabus)

    def parse_grading_structure(self, syllabus):
        grading_structure = {}
        if syllabus and isinstance(syllabus, str) and "Grading:" in syllabus:
            grading_section = syllabus.split("Grading:")[1].split("\n\n")[0]
            for line in grading_section.split("\n"):
                parts = line.split(":")
                if len(parts) >= 2:
                    component = parts[0].strip()
                    percentage_str = parts[-1].strip().rstrip('%')
                    try:
                        percentage = float(percentage_str)
                        grading_structure[component] = percentage
                    except ValueError:
                        # If we can't convert to float, skip this line
                        continue
        return grading_structure

class CanvasIntegration:
    def __init__(self, canvas_url: str, access_token: str):
        self.canvas_url = canvas_url
        self.headers = {'Authorization': f'Bearer {access_token}'}

    def get_course_details(self, course_id: str):
        details = {}
        
        # Get assignments
        assignments_url = f'{self.canvas_url}/api/v1/courses/{course_id}/assignments'
        response = requests.get(assignments_url, headers=self.headers)
        if response.status_code == 200:
            details['assignments'] = response.json()

        # Get announcements
        announcements_url = f'{self.canvas_url}/api/v1/courses/{course_id}/announcements'
        response = requests.get(announcements_url, headers=self.headers)
        if response.status_code == 200:
            details['announcements'] = response.json()

        # Get modules
        modules_url = f'{self.canvas_url}/api/v1/courses/{course_id}/modules'
        response = requests.get(modules_url, headers=self.headers)
        if response.status_code == 200:
            details['modules'] = response.json()

        # Get grades
        grades_url = f'{self.canvas_url}/api/v1/courses/{course_id}/students/submissions'
        response = requests.get(grades_url, headers=self.headers)
        if response.status_code == 200:
            details['grades'] = response.json()

        return details

    def get_dashboard_data(self):
        dashboard_url = f'{self.canvas_url}/api/v1/dashboard/dashboard_cards'
        response = requests.get(dashboard_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return []

    def get_courses(self):
        all_courses = []
        page = 1
        per_page = 100

        while True:
            params = {
                'enrollment_state': 'active',
                'include[]': ['term', 'total_students', 'syllabus_body', 'course_progress'],
                'state[]': ['available', 'completed', 'unpublished'],
                'per_page': per_page,
                'page': page
            }
            response = requests.get(f'{self.canvas_url}/api/v1/courses', headers=self.headers, params=params)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get courses: {response.status_code}")
            
            courses = response.json()
            if not courses:
                break
            
            all_courses.extend(courses)
            page += 1

        return all_courses
    def get_course_syllabus(self, course_id: str):
        response = requests.get(f'{self.canvas_url}/api/v1/courses/{course_id}', headers=self.headers)
        if response.status_code == 200:
            return response.json().get('syllabus_body', '')
        elif response.status_code == 403:
            return f"No permission to access syllabus for course {course_id}"
        else:
            return f"Failed to get syllabus for course {course_id}: {response.status_code}"

    def get_course_assignments(self, course_id: str):
        response = requests.get(f'{self.canvas_url}/api/v1/courses/{course_id}/assignments', headers=self.headers)
        if response.status_code == 200:
            return response.json() or []  # Return an empty list if the response is null or empty
        elif response.status_code == 403:
            return []  # Return an empty list if we don't have permission
        else:
            return []  # Return an empty list for any other error
    
    def get_calendar_events(self, start_date, end_date):
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'per_page': 100
        }
        response = requests.get(f'{self.canvas_url}/api/v1/calendar_events', headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get calendar events: {response.status_code}")
        
    def get_user_analytics(self, course_id):
        analytics_url = f'{self.canvas_url}/api/v1/courses/{course_id}/analytics/users/self'
        response = requests.get(analytics_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"User analytics not available for course {course_id}")
            return {}
        else:
            print(f"Failed to get user analytics for course {course_id}: {response.status_code}")
            return {}

    # Update get_course_details to include more information if needed
    def get_course_details(self, course_id):
        details = {}
        
        # Get assignments
        assignments_url = f'{self.canvas_url}/api/v1/courses/{course_id}/assignments'
        response = requests.get(assignments_url, headers=self.headers)
        if response.status_code == 200:
            details['assignments'] = response.json()

        # Get announcements
        announcements_url = f'{self.canvas_url}/api/v1/courses/{course_id}/announcements'
        response = requests.get(announcements_url, headers=self.headers)
        if response.status_code == 200:
            details['announcements'] = response.json()

        # Get modules
        modules_url = f'{self.canvas_url}/api/v1/courses/{course_id}/modules'
        response = requests.get(modules_url, headers=self.headers)
        if response.status_code == 200:
            details['modules'] = response.json()

        # Get grades
        grades_url = f'{self.canvas_url}/api/v1/courses/{course_id}/students/submissions'
        response = requests.get(grades_url, headers=self.headers)
        if response.status_code == 200:
            details['grades'] = response.json()

        return details

class IntelligentSuggestionGenerator:
    def generate_suggestions(self, courses, course_details, dashboard_data, calendar_events):
        suggestions = []
        now = datetime.now(ZoneInfo("UTC"))

        for course in courses:
            course_data = course_details.get(course.course_id, {})
            
            # Check for upcoming assignments
            upcoming_assignments = [
                a for a in course_data.get('assignments', [])
                if a['due_at'] and self.parse_datetime(a['due_at']) > now
            ]
            if upcoming_assignments:
                next_assignment = min(upcoming_assignments, key=lambda x: self.parse_datetime(x['due_at']))
                suggestions.append(f"Your next assignment for {course.name} is '{next_assignment['name']}' due on {next_assignment['due_at'][:10]}. Start working on it soon!")

            # Check module progress
            incomplete_modules = [m for m in course_data.get('modules', []) if not m.get('completed')]
            if incomplete_modules:
                suggestions.append(f"You have {len(incomplete_modules)} incomplete modules in {course.name}. Try to complete at least one this week.")

            # Check recent announcements
            recent_announcements = [
                a for a in course_data.get('announcements', [])
                if self.parse_datetime(a['posted_at']) > now - timedelta(days=7)
            ]
            if recent_announcements:
                suggestions.append(f"There are {len(recent_announcements)} recent announcements in {course.name}. Make sure to read them for important updates.")

            # Analyze grades
            low_grades = [g for g in course_data.get('grades', []) if g['score'] and g['score'] < 70]
            if low_grades:
                suggestions.append(f"You have {len(low_grades)} assignments with grades below 70% in {course.name}. Consider reviewing these topics or seeking help.")

        # Analyze calendar for busy periods
        event_dates = [self.parse_datetime(e['start_at']).date() for e in calendar_events if e.get('start_at')]
        date_counts = Counter(event_dates)
        busy_days = [date for date, count in date_counts.items() if count > 2]
        if busy_days:
            suggestions.append(f"You have busy days coming up on {', '.join(d.strftime('%Y-%m-%d') for d in busy_days[:3])}. Plan your time carefully!")

        # Check dashboard for to-do items
        todo_items = [card for card in dashboard_data if card.get('todo_date')]
        if todo_items:
            suggestions.append(f"You have {len(todo_items)} items on your to-do list. Try to complete at least one today!")

        return suggestions

    def parse_datetime(self, date_string):
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))



from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
import statistics

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
import statistics

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
import statistics

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
import statistics

class EnhancedSuggestionGenerator:
    def generate_suggestions(self, courses, course_details, dashboard_data, calendar_events, user_analytics):
        suggestions = {
            "Workload": [],
            "Performance": [],
            "Course-specific": [],
            "Calendar": [],
            "Learning": []
        }
        now = datetime.now(ZoneInfo("UTC"))
        
        self._analyze_workload(courses, course_details, calendar_events, now, suggestions)
        self._analyze_performance_trends(courses, course_details, suggestions)
        self._analyze_calendar_conflicts(courses, course_details, calendar_events, now, suggestions)
        self._generate_learning_suggestion(user_analytics, courses, suggestions)
        
        return suggestions

    def _analyze_workload(self, courses, course_details, calendar_events, now, suggestions):
        upcoming_assignments = defaultdict(list)
        for course in courses:
            course_data = course_details.get(course.course_id, {})
            for assignment in course_data.get('assignments', []):
                due_date = self.parse_datetime(assignment.get('due_at', ''))
                if due_date and due_date > now:
                    upcoming_assignments[course.name].append((assignment.get('name', 'Unnamed'), due_date))
        
        if not upcoming_assignments:
            suggestions["Workload"].append("You don't have any upcoming assignments. This might be a good time to review past material or work on long-term projects.")
            return
        
        busy_courses = sorted(upcoming_assignments.items(), key=lambda x: len(x[1]), reverse=True)
        busiest_course, busiest_assignments = busy_courses[0]
        
        next_week = now + timedelta(days=7)
        next_week_assignments = sum(1 for assignments in upcoming_assignments.values() for _, due_date in assignments if due_date <= next_week)
        
        suggestions["Workload"].append(f"You have {next_week_assignments} assignments due in the next week.")
        suggestions["Workload"].append(f"Focus on {busiest_course} as it has the most upcoming work with {len(busiest_assignments)} assignments.")
        
        if len(busy_courses) > 1:
            suggestions["Workload"].append(f"Also allocate time for {busy_courses[1][0]} which has {len(busy_courses[1][1])} upcoming assignments.")

    def _analyze_calendar_conflicts(self, courses, course_details, calendar_events, now, suggestions):
        today_events = [e for e in calendar_events if self.parse_datetime(e['start'].get('dateTime', e['start'].get('date'))).date() == now.date()]
        today_events.sort(key=lambda x: self.parse_datetime(x['start'].get('dateTime', x['start'].get('date'))))
        
        class_count = sum(1 for e in today_events if any(course.name.lower() in e.get('summary', '').lower() for course in courses))
        meeting_count = sum(1 for e in today_events if 'meeting' in e.get('summary', '').lower())
        
        suggestions["Calendar"].append(f"Today you have {class_count} classes and {meeting_count} meetings.")
        
        free_slots = self._find_free_time_slots(today_events, now)
        
        for course in courses:
            course_data = course_details.get(course.course_id, {})
            urgent_assignments = [a for a in course_data.get('assignments', []) if self.parse_datetime(a.get('due_at', '')) and self.parse_datetime(a.get('due_at', '')).date() == now.date()]
            
            for assignment in urgent_assignments:
                due_time = self.parse_datetime(assignment.get('due_at', ''))
                suitable_slots = [slot for slot in free_slots if slot[1] <= due_time]
                
                if suitable_slots:
                    best_slot = max(suitable_slots, key=lambda x: x[1] - x[0])
                    start_time = best_slot[0].strftime("%I:%M %p")
                    end_time = best_slot[1].strftime("%I:%M %p")
                    suggestions["Course-specific"].append(f"Urgent for {course.name}: '{assignment['name']}' is due today. Try to work on it between {start_time} and {end_time}.")
                else:
                    suggestions["Course-specific"].append(f"Urgent for {course.name}: '{assignment['name']}' is due today. Find any available time to complete it as soon as possible.")

    def _find_free_time_slots(self, events, now):
        busy_times = [(self.parse_datetime(e['start'].get('dateTime', e['start'].get('date'))),
                       self.parse_datetime(e['end'].get('dateTime', e['end'].get('date')))) for e in events]
        busy_times.sort(key=lambda x: x[0])
        
        free_slots = []
        current_time = now
        for start, end in busy_times:
            if current_time < start:
                free_slots.append((current_time, start))
            current_time = max(current_time, end)
        
        if current_time < now.replace(hour=23, minute=59, second=59):
            free_slots.append((current_time, now.replace(hour=23, minute=59, second=59)))
        
        return free_slots

    def _analyze_performance_trends(self, courses, course_details, suggestions):
        course_averages = {}
        for course in courses:
            course_data = course_details.get(course.course_id, {})
            grades = [g.get('score', 0) for g in course_data.get('grades', []) if g.get('score') is not None]
            if grades:
                course_averages[course.name] = statistics.mean(grades)
        
        if not course_averages:
            suggestions["Performance"].append("No grade data available. Keep track of your grades as they come in to monitor your progress.")
            return
        
        best_course = max(course_averages, key=course_averages.get)
        worst_course = min(course_averages, key=course_averages.get)
        
        suggestions["Performance"].append(f"Your strongest performance is in {best_course} (avg: {course_averages[best_course]:.2f}%).")
        suggestions["Performance"].append(f"Focus on improving your performance in {worst_course} (avg: {course_averages[worst_course]:.2f}%).")
        suggestions["Performance"].append(f"Consider applying study strategies from {best_course} to {worst_course} to boost your performance.")

    def _generate_learning_suggestion(self, user_analytics, courses, suggestions):
        late_submissions = 0
        total_submissions = 0
        for course_analytics in user_analytics.values():
            if 'tardiness_breakdown' in course_analytics:
                tardiness = course_analytics['tardiness_breakdown']
                late_submissions += tardiness.get('late', 0) + tardiness.get('missing', 0)
                total_submissions += sum(tardiness.values())
        
        if total_submissions > 0:
            late_ratio = late_submissions / total_submissions
            if late_ratio > 0.2:
                suggestions["Learning"].append(f"You've submitted {late_submissions} out of {total_submissions} assignments late. Set personal deadlines 2-3 days before the actual due date to improve your on-time submission rate and reduce stress.")
        
        course_topics = [course.name.split(':')[0] for course in courses]
        if 'Math' in course_topics or 'Statistics' in course_topics:
            suggestions["Learning"].append("For math-related courses, utilize Khan Academy or MIT OpenCourseWare for additional explanations and practice problems. Consider joining or forming a study group for collaborative problem-solving.")
        elif 'Computer Science' in course_topics or 'Programming' in course_topics:
            suggestions["Learning"].append("For programming courses, practice coding daily on platforms like Codecademy or LeetCode. Build small projects to apply what you're learning and solidify your understanding.")
        
        suggestions["Learning"].append("Create a study schedule that includes regular reviews of past material, practice problems, and collaborative study sessions. Use various learning resources like online tutorials, textbook supplements, and study groups to reinforce your understanding across all courses.")

    def parse_datetime(self, date_string):
        if not date_string:
            return None
        try:
            if isinstance(date_string, str):
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.replace(tzinfo=ZoneInfo("UTC"))
            elif isinstance(date_string, datetime):
                return date_string.replace(tzinfo=ZoneInfo("UTC")) if date_string.tzinfo is None else date_string
            return None
        except ValueError:
            print(f"Unable to parse date string: {date_string}")
            return None

class ScheduleSuggestionSystem:
    def __init__(self):
        self.students = []
        self.canvas = CanvasIntegration(CANVAS_URL, ACCESS_TOKEN)
        self.suggestion_generator = EnhancedSuggestionGenerator()

    def add_student(self, student):
        self.students.append(student)

    def get_canvas_courses(self):
        return self.canvas.get_courses()

    def generate_suggestions(self, student, google_calendar_events):
        course_details = {}
        user_analytics = {}
        for course in student.courses:
            course_details[course.course_id] = self.canvas.get_course_details(course.course_id)
            analytics = self.canvas.get_user_analytics(course.course_id)
            if analytics:  # Only add analytics if they are available
                user_analytics[course.course_id] = analytics

        dashboard_data = self.canvas.get_dashboard_data()

        return self.suggestion_generator.generate_suggestions(
            student.courses, course_details, dashboard_data, google_calendar_events, user_analytics
        )
system = ScheduleSuggestionSystem()

import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Set up the Flow object
CLIENT_SECRETS_FILE = "/workspaces/syllabus_suggestions/credentials/client_secret.json"
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/calendar.events.freebusy',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.calendars.readonly'
]

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri='https://localhost:8080/oauth2callback'
)

@app.route('/')
def index():
    html = """
    <h1>Welcome to the Schedule Suggestion System!</h1>
    <ul>
        <li><a href="/get_courses">View Your Courses</a></li>
        <li><a href="/get_suggestions">Get Scheduling Suggestions</a></li>
    </ul>
    """
    return render_template_string(html)

@app.route('/get_courses')
def get_courses():
    try:
        courses = system.get_canvas_courses()
        course_list = "<ul>"
        for course in courses:
            course_name = course.get('name', 'Unnamed Course')
            course_id = course.get('id', 'No ID')
            course_term = course.get('term', {}).get('name', 'No Term')
            course_state = course.get('workflow_state', 'Unknown State')
            course_list += f"<li>{course_name} (ID: {course_id}, Term: {course_term}, State: {course_state})</li>"
        course_list += "</ul>"
        return f"<h2>Your Courses ({len(courses)}):</h2>{course_list}"
    except Exception as e:
        return f"<h2>Error:</h2><p>{str(e)}</p>"
    
@app.route('/authorize')
def authorize():
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/check_session')
def check_session():
    return jsonify(dict(session))

@app.route('/oauth2callback')
def oauth2callback():
    app.logger.info("OAuth callback initiated")
    app.logger.info(f"Request URL: {request.url}")
    app.logger.info(f"Request args: {request.args}")
    
    try:
        app.logger.info("Attempting to fetch token")
        flow.fetch_token(authorization_response=request.url)
        app.logger.info("Token fetched successfully")
        
        credentials = flow.credentials
        app.logger.info(f"Credentials obtained: {credentials.to_json()}")
        
        session['credentials'] = credentials_to_dict(credentials)
        app.logger.info("Credentials stored in session")
        
        return redirect(url_for('get_suggestions'))
    except Exception as e:
        app.logger.error(f"Error in oauth2callback: {str(e)}")
        app.logger.error(f"Exception details: {traceback.format_exc()}")
        return f"An error occurred: {str(e)}", 500

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_calendar_service():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))
    
    credentials = Credentials(**session['credentials'])
    
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        session['credentials'] = credentials_to_dict(credentials)
    
    return build('calendar', 'v3', credentials=credentials)



@app.route('/get_suggestions')
def get_suggestions():
    def get_nocodeapi_calendar_events():
        try:
            url = "https://v1.nocodeapi.com/ommistry/calendar/uIJAtQBXWzuolwnf/listEvents"
            now = datetime.now(ZoneInfo("UTC"))
            params = {
                'calendarId': 'primary',
                'timeMin': now.isoformat(),
                'timeMax': (now + timedelta(days=30)).isoformat(),
                'singleEvents': 'true',
                'orderBy': 'startTime',
                'maxResults': '100'
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                events = response.json().get('items', [])
                print(f"Retrieved {len(events)} events from Google Calendar")
                return events
            else:
                print(f"Failed to retrieve calendar events from NoCodeAPI: {response.status_code}")
                print(f"Response content: {response.text}")
                return []
        except Exception as e:
            print(f"Error retrieving calendar events: {str(e)}")
            return []

    # Fetch Google Calendar events using NoCodeAPI
    google_calendar_events = get_nocodeapi_calendar_events()
    
    # Debug: Print the number of events and the first few events
    print(f"Number of calendar events: {len(google_calendar_events)}")
    if google_calendar_events:
        for event in google_calendar_events[:3]:
            print(json.dumps(event, indent=2))
    else:
        print("No calendar events retrieved.")

    # Your existing code for generating suggestions
    student = Student("Test Student", "test@example.com")
    canvas_courses = system.get_canvas_courses()
    
    if not canvas_courses:
        return "<h2>No courses found</h2><p>Unable to retrieve courses from Canvas.</p>"

    for canvas_course in canvas_courses:
        course = Course(
            canvas_course.get('name', 'Unnamed Course'),
            str(canvas_course.get('id', 'No ID')),
            canvas_course
        )
        student.courses.append(course)

    # Generate suggestions using Canvas data and NoCodeAPI Google Calendar events
    try:
        suggestions = system.generate_suggestions(student, google_calendar_events)
    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")
        return jsonify({"error": "An error occurred while generating suggestions."}), 500

    # Generate HTML for suggestions
    html_content = """
    <h2>Your Personalized Suggestions:</h2>
    {% for category, category_suggestions in suggestions.items() %}
        {% if category_suggestions %}
            <h3>{{ category }}:</h3>
            <ul>
            {% for suggestion in category_suggestions %}
                <li>{{ suggestion }}</li>
            {% endfor %}
            </ul>
        {% endif %}
    {% endfor %}
    """
    return render_template_string(html_content, suggestions=suggestions)


@app.route('/debug')
def debug():
    return "Application is running. Debug endpoint reached."

@app.route('/test')
def test():
    return "Server is running"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)