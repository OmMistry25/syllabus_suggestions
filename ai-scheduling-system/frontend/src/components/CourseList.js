import React from 'react';

function CourseList({ courses }) {
  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Your Courses ({courses.length})</h2>
      <div className="space-y-4">
        {courses.map((course, index) => (
          <div key={index} className="border rounded-lg p-4">
            <h3 className="text-lg font-semibold">{course.name}</h3>
            <p className="text-sm text-gray-500">ID: {course.id}</p>
            <p className="text-sm text-gray-500">Term: {course.term.name}</p>
            <p className="text-sm text-gray-500">State: {course.workflow_state}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CourseList;