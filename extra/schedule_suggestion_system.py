import datetime
from typing import List, Dict
import requests
from flask import Flask, request, jsonify, render_template_string
import random

app = Flask(__name__)
app.secret_key = 'bdccd44f9842c6f62cdd05cba47b7da861de0b662ec3fe24'

CANVAS_URL = 'https://canvas.illinois.edu'
ACCESS_TOKEN = '14559~Gk6LwhwGhxMXDtfK7WaRNYDfMRnr4kz8YukmVhwKDcycMXNZXerakVXfT2KnEZZW'

class Student:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self.courses: List[Dict] = []

class CanvasIntegration:
    def __init__(self, canvas_url: str, access_token: str):
        self.canvas_url = canvas_url
        self.headers = {'Authorization': f'Bearer {access_token}'}

    def get_courses(self):
        response = requests.get(f'{self.canvas_url}/api/v1/courses', headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    def get_course_assignments(self, course_id: str):
        response = requests.get(f'{self.canvas_url}/api/v1/courses/{course_id}/assignments', headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return []

class ScheduleSuggestionSystem:
    def __init__(self):
        self.canvas = CanvasIntegration(CANVAS_URL, ACCESS_TOKEN)

    def get_canvas_courses(self):
        return self.canvas.get_courses()

    def generate_suggestions(self, student: Student) -> List[str]:
        print("Starting generate_suggestions method")
        suggestions = []
        assignments = []

        for course in student.courses:
            try:
                print(f"Fetching assignments for course: {course.name}")
                course_assignments = self.canvas.get_course_assignments(course.course_id)
                print(f"Assignments for course {course.name}: {course_assignments}")
                if course_assignments:
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

        # Sort assignments by due date
        assignments.sort(key=lambda x: x['due_date'])

        # Generate personalized suggestions
        if assignments:
            upcoming_assignments = [a for a in assignments if datetime.strptime(a['due_date'], '%Y-%m-%d').date() >= datetime.now().date()]
            if upcoming_assignments:
                next_assignment = upcoming_assignments[0]
                suggestions.append(f"Your next assignment is '{next_assignment['name']}' for {next_assignment['course']}, due on {next_assignment['due_date']}.")
                
                # Check for assignments due within the next week
                week_assignments = [a for a in upcoming_assignments if (datetime.strptime(a['due_date'], '%Y-%m-%d').date() - datetime.now().date()).days <= 7]
                if len(week_assignments) > 1:
                    suggestions.append(f"You have {len(week_assignments)} assignments due within the next week. Plan your time wisely!")

                # Check for assignments due on the same day
                due_dates = [a['due_date'] for a in upcoming_assignments]
                if len(due_dates) != len(set(due_dates)):
                    suggestions.append("You have multiple assignments due on the same day. Consider starting early to manage your workload.")

        else:
            suggestions.append("You have no upcoming assignments. Great job staying on top of your work!")

        # Add general study tips
        suggestions.append(random.choice([
            "Remember to take regular breaks to maintain productivity.",
            "Consider using the Pomodoro Technique for effective study sessions.",
            "Don't forget to review your notes from previous lectures.",
            "Try explaining concepts to others to reinforce your understanding."
        ]))

        print(f"Generated suggestions: {suggestions}")
        return suggestions
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
            course_list += f"<li>{course_name} (ID: {course_id})</li>"
        course_list += "</ul>"
        return f"<h2>Your Courses ({len(courses)}):</h2>{course_list}"
    except Exception as e:
        return f"<h2>Error:</h2><p>{str(e)}</p>"

@app.route('/get_suggestions')
def get_suggestions():
    try:
        student = Student("Test Student", "test@example.com")
        student.courses = system.get_canvas_courses()

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