import React from 'react';
import { BookOpen, AlertTriangle, CheckCircle, Calendar } from 'react-feather';

function SuggestionList({ suggestions }) {
  const getIcon = (type) => {
    switch (type) {
      case 'assignment':
        return <Calendar className="w-5 h-5 text-blue-500" />;
      case 'module':
        return <BookOpen className="w-5 h-5 text-green-500" />;
      case 'grade':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <CheckCircle className="w-5 h-5 text-purple-500" />;
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Personalized Suggestions</h2>
      <div className="space-y-4">
        {suggestions.map((suggestion, index) => (
          <div key={index} className="flex items-start space-x-3 border rounded-lg p-4">
            {getIcon(suggestion.type)}
            <div>
              <p className="font-semibold">{suggestion.course}</p>
              <p>{suggestion.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SuggestionList;