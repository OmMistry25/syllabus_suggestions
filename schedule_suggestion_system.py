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
        if "Grading:" in syllabus:
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
    def __init__(self):
        self.encouragement_phrases = [
            "You're doing great!",
            "Keep up the good work!",
            "You've got this!",
            "Believe in yourself!",
            "Every step forward is progress!"
        ]

    def generate_suggestions(self, courses, assignments, calendar_events):
        suggestions = []

        # Count upcoming assignments
        upcoming_assignments = [a for a in assignments if datetime.strptime(a['due_date'], '%Y-%m-%d') > datetime.now()]
        num_upcoming = len(upcoming_assignments)

        # Workload assessment
        if num_upcoming == 0:
            suggestions.append("You have no upcoming assignments. Great job staying on top of your work!")
        elif num_upcoming <= 2:
            suggestions.append(f"You have only {num_upcoming} assignments due soon. This is a great opportunity to get ahead in your studies or focus on other aspects of your life!")
        elif num_upcoming <= 5:
            suggestions.append(f"You have {num_upcoming} upcoming assignments. Consider creating a schedule to manage your time effectively.")
        else:
            suggestions.append(f"You have {num_upcoming} upcoming assignments. It might be a busy period - remember to take breaks and manage your stress levels.")

        # Time management
        if num_upcoming > 0:
            earliest_due = min(assignments, key=lambda x: datetime.strptime(x['due_date'], '%Y-%m-%d'))
            days_until_due = (datetime.strptime(earliest_due['due_date'], '%Y-%m-%d') - datetime.now()).days
            if days_until_due <= 3:
                suggestions.append(f"Your next assignment is due soon! Consider prioritizing '{earliest_due['name']}' for {earliest_due['course']}.")
            elif days_until_due <= 7:
                suggestions.append(f"You have about a week until your next assignment is due. This is a good time to start working on '{earliest_due['name']}' for {earliest_due['course']}.")

        # Course engagement
        for course in courses:
            if course.total_students > 50:
                suggestions.append(f"'{course.name}' is a large class. Consider forming study groups or attending office hours to get more personalized attention.")

        # Work-life balance
        if datetime.now().weekday() >= 5:  # Weekend
            suggestions.append("It's the weekend! While it's good to stay on top of your studies, don't forget to relax and recharge.")
        
        # Random encouragement
        suggestions.append(random.choice(self.encouragement_phrases))

        # Calendar-based suggestions
        upcoming_events = [e for e in calendar_events if e.get('start_at') and datetime.strptime(e['start_at'][:10], '%Y-%m-%d') > datetime.now()]
        if upcoming_events:
            next_event = min(upcoming_events, key=lambda x: datetime.strptime(x['start_at'][:10], '%Y-%m-%d'))
            suggestions.append(f"Your next event is '{next_event.get('title', 'Unnamed Event')}' on {next_event['start_at'][:10]}. Make sure you're prepared!")

        # Grading structure-based suggestions
        for course in courses:
            for assignment in assignments:
                if assignment['course'] == course.name:
                    for component, percentage in course.grading_structure.items():
                        if component.lower() in assignment['name'].lower():
                            suggestions.append(f"The upcoming '{assignment['name']}' for {course.name} is worth {percentage}% of your final grade. Plan your time accordingly!")

        # Workload distribution
        weekly_workload = {}
        for assignment in assignments:
            week = datetime.strptime(assignment['due_date'], '%Y-%m-%d').isocalendar()[1]
            weekly_workload[week] = weekly_workload.get(week, 0) + 1
        if weekly_workload:
            busiest_week = max(weekly_workload, key=weekly_workload.get)
            suggestions.append(f"Week {busiest_week} seems to be your busiest with {weekly_workload[busiest_week]} assignments due. Start preparing early!")

        # Exam preparation
        for event in upcoming_events:
            if 'exam' in event.get('title', '').lower():
                exam_date = datetime.strptime(event['start_at'][:10], '%Y-%m-%d')
                days_until_exam = (exam_date - datetime.now()).days
                if days_until_exam <= 14:
                    suggestions.append(f"You have an exam ({event['title']}) in {days_until_exam} days. Start reviewing your notes and practice problems!")

        # If no suggestions were generated, add a default one
        if not suggestions:
            suggestions.append("No specific suggestions at this time. Keep up with your regular study habits!")

        # Random encouragement
        suggestions.append(random.choice(self.encouragement_phrases))

        return suggestions

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
        suggestion_generator = IntelligentSuggestionGenerator()
        
        assignments = []
        for course in student.courses:
            try:
                course_assignments = self.canvas.get_course_assignments(course.course_id)
                if course_assignments is not None:
                    for assignment in course_assignments:
                        due_at = assignment.get('due_at')
                        if due_at:
                            assignments.append({
                                'course': course.name,
                                'name': assignment.get('name', 'Unnamed Assignment'),
                                'due_date': due_at[:10]
                            })
            except Exception as e:
                print(f"Error fetching assignments for course {course.name}: {str(e)}")

        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)  # Get events for the next 30 days
        
        try:
            calendar_events = self.canvas.get_calendar_events(start_date, end_date)
        except Exception as e:
            print(f"Error fetching calendar events: {str(e)}")
            calendar_events = []

        return suggestion_generator.generate_suggestions(student.courses or [], assignments or [], calendar_events or [])
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
def get_suggestions():
    try:
        student = Student("Test Student", "test@example.com")
        
        canvas_courses = system.get_canvas_courses()
        for canvas_course in canvas_courses:
            course = Course(
                canvas_course.get('name', 'Unnamed Course'),
                canvas_course.get('id', 'No ID'),
                canvas_course
            )
            student.courses.append(course)

        suggestions = system.generate_suggestions(student)
        suggestion_list = "<ul>"
        for suggestion in suggestions:
            suggestion_list += f"<li>{suggestion}</li>"
        suggestion_list += "</ul>"
        return f"<h2>Your Personalized Suggestions:</h2>{suggestion_list}"
    except Exception as e:
        return f"<h2>Error:</h2><p>{str(e)}</p>"
    
if __name__ == '__main__':
    app.run(debug=True)