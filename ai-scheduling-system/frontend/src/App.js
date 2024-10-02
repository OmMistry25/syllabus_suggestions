import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CourseList from './components/CourseList';
import SuggestionList from './components/SuggestionList';

function App() {
  const [courses, setCourses] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [activeTab, setActiveTab] = useState('courses');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const coursesResponse = await axios.get('/api/courses');
      setCourses(coursesResponse.data);

      const suggestionsResponse = await axios.get('/api/suggestions');
      setSuggestions(suggestionsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Schedule Suggestion System</h1>
      <div className="mb-4">
        <button
          className={`mr-2 px-4 py-2 rounded ${activeTab === 'courses' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('courses')}
        >
          Your Courses
        </button>
        <button
          className={`px-4 py-2 rounded ${activeTab === 'suggestions' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('suggestions')}
        >
          Suggestions
        </button>
      </div>
      {activeTab === 'courses' ? (
        <CourseList courses={courses} />
      ) : (
        <SuggestionList suggestions={suggestions} />
      )}
      <div className="mt-6 flex justify-center">
        <button
          className="bg-green-500 text-white px-4 py-2 rounded"
          onClick={fetchData}
        >
          Refresh Data
        </button>
      </div>
    </div>
  );
}

export default App;