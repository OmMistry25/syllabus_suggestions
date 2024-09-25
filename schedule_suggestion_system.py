import datetime
from typing import List, Dict
import re
from PyPDF2 import PdfReader

class Student:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self.courses: List[Course] = []
        self.performance: Dict[str, float] = {}  # course name: GPA

    def add_course(self, course):
        self.courses.append(course)

    def update_performance(self, course_name: str, gpa: float):
        self.performance[course_name] = gpa

class Course:
    def __init__(self, name: str, syllabus: Dict[str, List[Dict[str, str]]]):
        self.name = name
        self.schedule = syllabus['schedule']
        self.syllabus = syllabus

class ScheduleSuggestionSystem:
    def __init__(self):
        self.students: List[Student] = []

    def add_student(self, student: Student):
        self.students.append(student)

    def parse_syllabus_pdf(self, pdf_path: str) -> Dict[str, List[Dict[str, str]]]:
        print(f"Attempting to parse PDF: {pdf_path}")
        syllabus_data = {"assignments": [], "schedule": []}
        try:
            reader = PdfReader(pdf_path)
            print(f"Successfully opened PDF. Number of pages: {len(reader.pages)}")
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            print(f"Extracted text (first 500 characters): {text[:500]}")
            
            # Split the text into lines and process each line
            lines = text.split('\n')
            current_week = ""
            current_date = ""
            for line in lines:
                # Check for week
                week_match = re.match(r'Week #(\d+)', line)
                if week_match:
                    current_week = f"Week {week_match.group(1)}"
                    continue
                
                # Check for date and topic
                date_topic_match = re.match(r'(\d{1,2}/\d{1,2})\s*(.*)', line)
                if date_topic_match:
                    current_date = date_topic_match.group(1)
                    topic = date_topic_match.group(2).strip()
                    syllabus_data["schedule"].append({
                        "week": current_week,
                        "date": current_date,
                        "topic": topic
                    })
                    
                    # Check for assignments in the topic
                    assignment_match = re.search(r'(HW-\d+\s+DUE)', topic)
                    if assignment_match:
                        syllabus_data["assignments"].append({
                            "name": assignment_match.group(1),
                            "due_date": current_date
                        })
                    
                    # Check for exams in the topic
                    exam_match = re.search(r'(EXAM-[I|V]+|FINAL EXAM)', topic)
                    if exam_match:
                        syllabus_data["assignments"].append({
                            "name": exam_match.group(1),
                            "due_date": current_date
                        })

            print(f"Found {len(syllabus_data['schedule'])} schedule entries")
            print(f"Found {len(syllabus_data['assignments'])} assignments")

            return syllabus_data
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return syllabus_data

    def generate_suggestions(self, student: Student) -> List[str]:
        suggestions = []
        today = datetime.date.today()
        
        def parse_date(date_str):
            try:
                return datetime.datetime.strptime(date_str, '%m/%d').replace(year=today.year).date()
            except ValueError:
                print(f"Warning: Could not parse date '{date_str}'. Skipping this entry.")
                return None

        upcoming_classes = [
            class_info for course in student.courses
            for class_info in course.schedule
            if (parsed_date := parse_date(class_info['date'])) and parsed_date >= today
        ]
        upcoming_classes.sort(key=lambda x: parse_date(x['date']))

        upcoming_assignments = [
            assignment for course in student.courses
            for assignment in course.syllabus['assignments']
            if (parsed_date := parse_date(assignment['due_date'])) and parsed_date >= today
        ]
        upcoming_assignments.sort(key=lambda x: parse_date(x['due_date']))

        if upcoming_classes:
            suggestions.append(f"You have {len(upcoming_classes)} classes in the next week. Make sure to prepare for them!")
            for class_info in upcoming_classes[:3]:  # Show details for the next 3 classes
                suggestions.append(f"Upcoming class: {class_info['topic']} on {class_info['date']}")

        if upcoming_assignments:
            suggestions.append(f"You have {len(upcoming_assignments)} assignments due soon. Start working on them!")
            for assignment in upcoming_assignments[:3]:  # Show details for the next 3 assignments
                suggestions.append(f"Upcoming assignment: {assignment['name']} due on {assignment['due_date']}")

        return suggestions