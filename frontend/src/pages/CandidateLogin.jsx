import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Hash, ArrowLeft } from 'lucide-react';
import apiClient from '../services/apiClient';

const CandidateLogin = () => {
  const navigate = useNavigate();
  const [regNo, setRegNo] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!regNo.trim()) {
      setError('Please enter your registration number');
      setLoading(false);
      return;
    }

    try {
      const response = await apiClient.post('/candidates/candidate-login/', {
        registration_number: regNo.trim().toUpperCase(),
      });

      // Store candidate data in localStorage
      localStorage.setItem('candidateToken', response.data.token);
      localStorage.setItem('candidateData', JSON.stringify(response.data.candidate));
      
      // Navigate to candidate portal
      navigate('/candidate-portal');
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Registration number not found. Please check and try again.';
      setError(errorMsg);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col">
      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Logo and Title */}
          <div className="text-center mb-8">
            <img
              src="/uvtab-logo.png"
              alt="UVTAB Logo"
              className="w-24 h-24 mx-auto mb-4 object-contain"
            />
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Candidate Portal</h1>
            <p className="text-blue-600 font-medium">Uganda Vocational & Technical Assessment Board</p>
            <p className="text-gray-500 text-sm mt-1">Access Your Assessment Information</p>
          </div>

          {/* Login Card */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Registration Number Input */}
              <div>
                <label htmlFor="regNo" className="block text-sm font-medium text-gray-700 mb-2">
                  Registration Number
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Hash className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="regNo"
                    value={regNo}
                    onChange={(e) => {
                      setRegNo(e.target.value);
                      setError('');
                    }}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 uppercase"
                    placeholder="Enter your registration number"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Example: UVT001/U/26/A/HD/M/0001
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Access My Portal'}
              </button>
            </form>

            {/* Help Section */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3 text-center">Need Help?</h3>
              <ul className="text-xs text-gray-500 space-y-2">
                <li>• Use your registration number exactly as it appears on your documents</li>
                <li>• Contact your assessment center if you don't know your registration number</li>
                <li>• Results are only available after official release by UVTAB</li>
              </ul>
            </div>
          </div>

          {/* Back to Staff Login */}
          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600 text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              Staff/Admin Login
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-gray-500">
        © Uganda Vocational & Technical Assessment Board
        <br />
        Education Management Information System
      </footer>
    </div>
  );
};

export default CandidateLogin;
