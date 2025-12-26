import { useState } from 'react';
import { BookImage, Download, Loader2 } from 'lucide-react';

const Albums = () => {
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    assessmentSeries: '',
    registrationCategory: '',
    level: '',
  });

  const handleGenerate = async () => {
    setLoading(true);
    // TODO: Implement album generation logic
    setTimeout(() => {
      setLoading(false);
      alert('Album generation will be implemented');
    }, 1000);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center space-x-3">
          <BookImage className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Albums</h1>
            <p className="text-gray-600 mt-1">Generate Registration Lists</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter Options</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series
            </label>
            <select
              value={filters.assessmentSeries}
              onChange={(e) => setFilters({ ...filters, assessmentSeries: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select Series</option>
              {/* TODO: Load from API */}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Registration Category
            </label>
            <select
              value={filters.registrationCategory}
              onChange={(e) => setFilters({ ...filters, registrationCategory: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Categories</option>
              <option value="modular">Modular</option>
              <option value="formal">Formal</option>
              <option value="workers_pas">Workers PAS</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Level
            </label>
            <select
              value={filters.level}
              onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Levels</option>
              {/* TODO: Load from API */}
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center space-x-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              <span>Generate Album</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Albums;
