# Schedule Suggestion System

This Python-based Schedule Suggestion System parses course syllabi in PDF format and generates personalized scheduling suggestions for students.

## Demo Video

[Click here to view the demo](test 2.mov)

## Features

- Parse PDF syllabi to extract course schedules and assignments
- Generate personalized suggestions based on upcoming classes and assignments
- Easily extendable for additional features like email notifications or calendar integration

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher installed on your system
- pip (Python package installer)

## Installation

1. Clone this repository or download the source code:

   ```
   git clone https://github.com/yourusername/schedule-suggestion-system.git
   cd schedule-suggestion-system
   ```

2. Install the required dependencies:

   ```
   pip install PyPDF2
   ```

## File Structure

Ensure your project directory contains the following files:

- `schedule_suggestion_system.py`: Contains the main classes and logic for the system
- `run_system.py`: Script to run the system and generate suggestions
- `Course_Calendar_SE450_2024_v2.pdf`: Sample syllabus PDF (replace with your own syllabus)

## Usage

1. Place your syllabus PDF file in the project directory.

2. Open `run_system.py` and update the syllabus file path if necessary:

   ```python
   syllabus_data = system.parse_syllabus_pdf('path/to/your/syllabus.pdf')
   ```

3. Run the system:

   ```
   python run_system.py
   ```

4. The system will output parsed syllabus data and generated suggestions.

## Customization

- To add more courses, create additional `Course` objects in `run_system.py`.
- To modify suggestion generation logic, update the `generate_suggestions` method in `schedule_suggestion_system.py`.
- To change PDF parsing behavior, modify the `parse_syllabus_pdf` method in `schedule_suggestion_system.py`.

## Troubleshooting

If you encounter issues with date parsing:

1. Check your syllabus PDF for consistent date formats.
2. Adjust the date parsing logic in `generate_suggestions` and `parse_syllabus_pdf` methods if necessary.

## Contributing

Contributions to the Schedule Suggestion System are welcome. Please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b <branch_name>`.
3. Make your changes and commit them: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create the pull request.

Alternatively, see the GitHub documentation on [creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

## Contact

If you want to contact the maintainer of this project, please email [your-email@example.com].

## License

This project uses the following license: GPL-3.0 license.
