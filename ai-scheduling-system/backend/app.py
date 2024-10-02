from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from system import ScheduleSuggestionSystem

app = Flask(__name__, static_folder='../frontend/build')
CORS(app)

system = ScheduleSuggestionSystem()

@app.route('/api/courses')
def get_courses():
    courses = system.get_canvas_courses()
    return jsonify(courses)

@app.route('/api/suggestions')
def get_suggestions():
    student = system.create_test_student()
    suggestions = system.generate_suggestions(student)
    return jsonify(suggestions)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)