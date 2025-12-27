import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock } from 'lucide-react';
import apiClient from '../services/apiClient';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiClient.post('/users/login/', {
        email: formData.email,
        password: formData.password,
      });

      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/dashboard');
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Login failed. Please try again.';
      setError(errorMsg);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Top Blue Section with Title */}
      <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 pt-12 pb-48 relative">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white">UVTAB Informal</h1>
        </div>
        
        {/* Curved Wave at Bottom */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" className="w-full" preserveAspectRatio="none" style={{ height: '120px' }}>
            <path
              d="M0,64 C240,100 480,100 720,64 C960,28 1200,28 1440,64 L1440,120 L0,120 Z"
              fill="#ffffff"
            ></path>
          </svg>
        </div>
      </div>

      {/* Main Content Container */}
      <div className="flex-1 container mx-auto px-4 py-8 -mt-24">
        <div className="grid md:grid-cols-2 gap-12 items-center max-w-7xl mx-auto">
          {/* Left Side - Information */}
          <div className="text-gray-700">
            {/* Illustration */}
            <div className="mb-6 flex justify-center">
              <img
                src="/illustration.jpg"
                alt="EIMS Illustration"
                className="w-full max-w-sm h-auto object-contain"
              />
            </div>

            <p className="text-base mb-4 text-center text-gray-800">Some of the Services Offered by Informal System:</p>
            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
              <div className="bg-white border border-gray-200 p-4 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-2">
                <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z" />
                </svg>
                </div>
                <p className="text-sm">Candidate Management</p>
              </div>

              <div className="bg-white border border-gray-200 p-4 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center mb-2">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <p className="text-sm">Assessment Series Management</p>
              </div>

              <div className="bg-white border border-gray-200 p-4 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-cyan-500 rounded-lg flex items-center justify-center mb-2">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                  </svg>
                </div>
                <p className="text-sm">Informal Statistics</p>
              </div>

              <div className="bg-white border border-gray-200 p-4 rounded-lg shadow-sm">
                <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-2">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                    <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                  </svg>
                </div>
                <p className="text-sm">Candidate Results Management</p>
              </div>
            </div>
          </div>

          {/* Right Side - White Login Card */}
          <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-xl mx-auto w-full">
            <div className="text-center mb-8">
            <img
              src="/uvtab-logo.png"
              alt="UVTAB Logo"
              className="w-24 h-24 mx-auto mb-4 object-contain"
            />
            <h2 className="text-2xl text-gray-800 mb-2">
              UGANDA VOCATIONAL AND TECHNICAL
            </h2>
            <h3 className="text-2xl text-gray-800 mb-2">ASSESSMENT BOARD</h3>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Input */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter your email"
                    required
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="••••••"
                    required
                  />
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Login Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed text-lg"
              >
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Footer - Sticky at bottom */}
      <footer className="bg-white border-t border-gray-200 py-4 mt-auto">
        <div className="text-center text-sm text-gray-500">
          Copyright © 2025 UVTAB. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default Login;
