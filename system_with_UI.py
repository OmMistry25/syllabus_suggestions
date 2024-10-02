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
from flask import Flask, request, jsonify, session
from flask import Flask, request, jsonify, render_template_string
import random
from datetime import datetime, timedelta
import functools
import traceback
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter

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

app = Flask(__name__)
app.secret_key = 'bdccd44f9842c6f62cdd05cba47b7da861de0b662ec3fe24'  # Replace with a real secret key

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

class ScheduleSuggestionSystem:
    def __init__(self):
        self.students: List[Student] = []
        self.canvas = CanvasIntegration(CANVAS_URL, ACCESS_TOKEN)
        self.tokenizer = AutoTokenizer.from_pretrained("Falconsai/text_summarization")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("Falconsai/text_summarization")

    def add_student(self, student: Student):
        self.students.append(student)

    def get_canvas_courses(self):
        return self.canvas.get_courses()

    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        inputs = self.tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
        summary_ids = self.model.generate(inputs, max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary

    def generate_suggestions(self, student: Student) -> List[str]:
        course_details = {}
        for course in student.courses:
            course_details[course.course_id] = self.canvas.get_course_details(course.course_id)

        dashboard_data = self.canvas.get_dashboard_data()
        calendar_events = self.canvas.get_calendar_events(datetime.now(), datetime.now() + timedelta(days=30))

        suggestion_generator = IntelligentSuggestionGenerator()
        return suggestion_generator.generate_suggestions(student.courses, course_details, dashboard_data, calendar_events)
system = ScheduleSuggestionSystem()

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
    
@app.route('/get_suggestions')
@log_exceptions
def get_suggestions():
    print("Starting get_suggestions route")
    student = Student("Test Student", "test@example.com")
    
    print("Fetching Canvas courses")
    canvas_courses = system.get_canvas_courses()
    print(f"Number of Canvas courses: {len(canvas_courses)}")
    
    if not canvas_courses:
        return "<h2>No courses found</h2><p>Unable to retrieve courses from Canvas.</p>"

    print("Creating Course objects")
    for canvas_course in canvas_courses:
        print(f"Processing course: {canvas_course.get('name', 'Unnamed Course')}")
        print(f"Course data: {canvas_course}")
        course = Course(
            canvas_course.get('name', 'Unnamed Course'),
            str(canvas_course.get('id', 'No ID')),
            canvas_course
        )
        student.courses.append(course)
    print(f"Number of student courses: {len(student.courses)}")

    print("Generating suggestions")
    suggestions = system.generate_suggestions(student)
    print(f"Number of generated suggestions: {len(suggestions)}")

    if not suggestions:
        return "<h2>No suggestions available</h2><p>Unable to generate suggestions at this time.</p>"

    suggestion_list = "<ul>"
    for suggestion in suggestions:
        suggestion_list += f"<li>{suggestion}</li>"
    suggestion_list += "</ul>"
    return f"<h2>Your Personalized Suggestions:</h2>{suggestion_list}"
    
if __name__ == '__main__':
    app.run(debug=True)