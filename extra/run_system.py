from schedule_suggestion_system import ScheduleSuggestionSystem, Student, Course
import datetime

def main():
    print("Starting the Schedule Suggestion System")
    system = ScheduleSuggestionSystem()
    
    print("Creating student")
    alice = Student("Alice", "alice@example.com")
    system.add_student(alice)
    
    print("Parsing syllabus")
    syllabus_data = system.parse_syllabus_pdf('/workspaces/syllabus_suggestions/Course_Calendar_SE450_2024_v2.pdf')
    
    print("Creating course")
    course = Course("SE450", syllabus_data)
    alice.add_course(course)
    
    print("Generating suggestions")
    suggestions = system.generate_suggestions(alice)
    print("Generated suggestions:")
    for suggestion in suggestions:
        print(suggestion)
    
    # Get material summary for the next class
    next_class_date = course.schedule[0]['date']  # Assuming the schedule is sorted
    material_summary = system.get_material_summary(alice, next_class_date)
    print(f"\nMaterial summary for next class ({next_class_date}):")
    print(material_summary)

    print("Script completed")

if __name__ == "__main__":
    main()