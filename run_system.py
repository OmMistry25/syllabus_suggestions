from schedule_suggestion_system import ScheduleSuggestionSystem, Student, Course

def main():
    print("Starting the Schedule Suggestion System")
    system = ScheduleSuggestionSystem()
    
    print("Creating student")
    alice = Student("Alice", "alice@example.com")
    system.add_student(alice)
    
    print("Parsing syllabus")
    syllabus_data = system.parse_syllabus_pdf('/workspaces/syllabus_suggestions/Course_Calendar_SE450_2024_v2.pdf')
    print(f"Parsed syllabus data: {syllabus_data}")
    
    print("Creating course")
    course = Course("SE450", syllabus_data)
    alice.add_course(course)
    
    print("Generating suggestions")
    suggestions = system.generate_suggestions(alice)
    print("Generated suggestions:")
    for suggestion in suggestions:
        print(suggestion)
    
    print("Script completed")

if __name__ == "__main__":
    main()