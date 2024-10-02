import datetime
from typing import List, Dict
from zoneinfo import ZoneInfo
from collections import Counter

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

class CanvasIntegration:
    def __init__(self, canvas_url: str, access_token: str):
        self.canvas_url = canvas_url
        self.headers = {'Authorization': f'Bearer {access_token}'}

    def get_courses(self):
        # Simulated course data
        return [
            {"name": "Fall 2024-IE 360-Facilities Planning and Design-Sections AB1, AB2, AB3, AL1", "id": "51135", "term": {"name": "2024 - Fall"}, "workflow_state": "available"},
            {"name": "Fall 2024-IE 405-Computing for ISE-Sections G, U", "id": "30947", "term": {"name": "2024 - Fall"}, "workflow_state": "available"},
            {"name": "Fall 2024-SE 450-Decision Analysis I-Sections G, U", "id": "47270", "term": {"name": "2024 - Fall"}, "workflow_state": "available"},
            {"name": "Fall 2024-STAT 400-Statistics and Probability I-Sections YL1, YL2", "id": "48800", "term": {"name": "2024 - Fall"}, "workflow_state": "available"},
            {"name": "PORT 150-Writing Brazilians into U.S.-Fall2024", "id": "51415", "term": {"name": "2024 - Fall"}, "workflow_state": "available"},
            {"name": "SCD Lab Trainings", "id": "36705", "term": {"name": "DEV"}, "workflow_state": "available"},
        ]

class IntelligentSuggestionGenerator:
    def generate_suggestions(self, courses):
        suggestions = []
        for course in courses:
            suggestions.append({"type": "assignment", "course": course.name, "message": f"Your next assignment for {course.name} is due soon. Start working on it!"})
            suggestions.append({"type": "module", "course": course.name, "message": f"You have incomplete modules in {course.name}. Try to complete at least one this week."})
            suggestions.append({"type": "grade", "course": course.name, "message": f"You have assignments with grades below 70% in {course.name}. Consider reviewing these topics or seeking help."})
        return suggestions

class ScheduleSuggestionSystem:
    def __init__(self):
        self.canvas = CanvasIntegration('https://canvas.illinois.edu', 'your_access_token_here')
        self.suggestion_generator = IntelligentSuggestionGenerator()

    def get_canvas_courses(self):
        return self.canvas.get_courses()

    def create_test_student(self):
        student = Student("Test Student", "test@example.com")
        canvas_courses = self.get_canvas_courses()
        for course_data in canvas_courses:
            course = Course(course_data['name'], course_data['id'], course_data)
            student.courses.append(course)
        return student

    def generate_suggestions(self, student: Student) -> List[Dict]:
        return self.suggestion_generator.generate_suggestions(student.courses)