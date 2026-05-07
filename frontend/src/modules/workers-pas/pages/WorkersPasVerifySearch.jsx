import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ShieldCheck } from 'lucide-react';

const WorkersPasVerifySearch = () => {
  const [bookNumber, setBookNumber] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (!bookNumber.trim()) return;

    // Convert standard book number format (WP/WPTP/43000001) to slug (WP-WPTP-43000001)
    const slug = bookNumber.trim().replace(/\//g, '-');
    navigate(`/workers-pas/verify/${encodeURIComponent(slug)}`);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-green-100 rounded-full mb-3">
            <ShieldCheck className="w-7 h-7 text-green-600" />
          </div>
          <h1 className="text-xl font-bold text-gray-900">Worker's PAS Verification</h1>
          <p className="text-sm text-gray-500 mt-1">Enter a booklet number to verify its authenticity</p>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <form onSubmit={handleSearch}>
            <div className="mb-4">
              <label htmlFor="bookNumber" className="block text-sm font-medium text-gray-700 mb-2">
                Booklet Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="bookNumber"
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-green-500 focus:border-green-500 sm:text-sm uppercase"
                  placeholder="e.g. WP/WPTP/43000001"
                  value={bookNumber}
                  onChange={(e) => setBookNumber(e.target.value.toUpperCase())}
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              disabled={!bookNumber.trim()}
            >
              Verify Booklet
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Directorate of Industrial Training (DIT) · Ministry of Education & Sports
        </p>
      </div>
    </div>
  );
};

export default WorkersPasVerifySearch;
