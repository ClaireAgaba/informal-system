import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Building2,
  UserCircle,
  Calendar,
  Search,
  FileText,
  Banknote,
  FileSpreadsheet,
  Database,
  LogOut,
  ChevronDown,
  MessageSquare,
  BarChart3,
  Award,
  Lock,
  Eye,
  EyeOff,
  X,
} from 'lucide-react';
import apiClient from '../services/apiClient';

const modules = [
  {
    name: 'Candidates',
    icon: Users,
    path: '/candidates',
    color: 'bg-pink-500',
    description: 'Manage Candidates',
  },
  {
    name: 'Occupations',
    icon: Briefcase,
    path: '/occupations',
    color: 'bg-blue-400',
    description: 'Occupation Management',
  },
  {
    name: 'Assessment Centers',
    icon: Building2,
    path: '/assessment-centers',
    color: 'bg-yellow-600',
    description: 'Centers & Branches',
  },
  {
    name: 'Assessment Series',
    icon: Calendar,
    path: '/assessment-series',
    color: 'bg-green-500',
    description: 'Assessment Periods',
  },
  {
    name: 'Users',
    icon: UserCircle,
    path: '/users',
    color: 'bg-purple-500',
    description: 'User Management',
  },
  {
    name: 'Reports',
    icon: FileText,
    path: '/reports',
    color: 'bg-teal-500',
    description: 'Generate Reports',
  },
  {
    name: 'UVTAB Fees',
    icon: Banknote,
    path: '/fees',
    color: 'bg-rose-500',
    description: 'Candidate & Center Fees',
  },
  {
    name: 'Marksheets',
    icon: FileSpreadsheet,
    path: '/marksheets',
    color: 'bg-indigo-500',
    description: 'Generate & Manage Marksheets',
  },
  {
    name: 'Complaints',
    icon: MessageSquare,
    path: '/complaints',
    color: 'bg-orange-500',
    description: 'Manage Complaints',
  },
  {
    name: 'DIT Legacy data',
    icon: Database,
    path: '/dit-legacy-data',
    color: 'bg-cyan-600',
    description: 'Import & reconcile legacy DIT data',
  },
  {
    name: 'Statistics',
    icon: BarChart3,
    path: '/statistics',
    color: 'bg-blue-600',
    description: 'System Analytics & Reports',
  },
  {
    name: 'Awards',
    icon: Award,
    path: '/awards',
    color: 'bg-amber-500',
    description: 'Successful Candidates & Awards',
  },
];

// Helper to get user from localStorage synchronously
const getUserFromStorage = () => {
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      return JSON.parse(userStr);
    }
  } catch (error) {
    console.error('Error parsing user data:', error);
  }
  return null;
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  // Initialize currentUser synchronously to prevent flash of all modules
  const [currentUser, setCurrentUser] = useState(() => getUserFromStorage());
  const dropdownRef = useRef(null);

  // Change Password state
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Get user display name
  const getUserDisplayName = () => {
    if (!currentUser) return 'User';
    
    // For center representatives, use their profile fullname
    if (currentUser.user_type === 'center_representative') {
      if (currentUser.center_representative?.fullname) {
        return currentUser.center_representative.fullname;
      }
    }
    
    // For all other users (staff, support_staff, superuser), try first_name + last_name
    if (currentUser.first_name && currentUser.last_name) {
      return `${currentUser.first_name} ${currentUser.last_name}`;
    }
    
    // If only first_name exists
    if (currentUser.first_name) {
      return currentUser.first_name;
    }
    
    // Fall back to username
    return currentUser.username || 'User';
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
      setPasswordError('All fields are required');
      return;
    }

    if (passwordForm.new_password.length < 6) {
      setPasswordError('New password must be at least 6 characters');
      return;
    }

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('New password and confirm password do not match');
      return;
    }

    setPasswordLoading(true);
    try {
      await apiClient.post('/users/change-password/', passwordForm);
      setPasswordSuccess('Password changed successfully. Redirecting to login...');
      setTimeout(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
      }, 2000);
    } catch (error) {
      setPasswordError(error.response?.data?.error || 'Failed to change password. Please try again.');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      // Call logout API if token exists
      const token = localStorage.getItem('token');
      if (token) {
        // Optional: Call logout endpoint to invalidate token on server
        // await apiClient.post('/users/logout/');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Navigate to login
      navigate('/login');
    }
  };

  // Filter modules based on user type and search query
  const getAccessibleModules = () => {
    // For security: if no user, return empty modules
    if (!currentUser) return [];
    
    let accessibleModules = modules;
    
    // Filter by user type
    if (currentUser.user_type === 'center_representative') {
      // Center reps only see: Candidates, Reports, UVTAB Fees, Complaints
      const allowedModules = ['Candidates', 'Reports', 'UVTAB Fees', 'Complaints'];
      accessibleModules = modules.filter(module => allowedModules.includes(module.name));
    }
    
    // Apply search filter
    return accessibleModules.filter((module) =>
      module.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const filteredModules = getAccessibleModules();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900">
      {/* Header */}
      <div className="bg-blue-800/50 backdrop-blur-sm border-b border-blue-500/30">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                <LayoutDashboard className="w-5 h-5 text-blue-600" />
              </div>
              <h1 className="text-white text-xl font-semibold">Informal Portal</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-white/90 text-sm">11:59 AM</span>
              
              {/* User Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center space-x-2 hover:bg-white/10 rounded-lg px-3 py-2 transition-colors"
                >
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                    <UserCircle className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-white text-sm">{getUserDisplayName()}</span>
                  <ChevronDown className={`w-4 h-4 text-white transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu */}
                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50">
                    <button
                      onClick={() => { setShowChangePassword(true); setDropdownOpen(false); }}
                      className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      <Lock className="w-4 h-4" />
                      <span>Change Password</span>
                    </button>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-blue-300 w-5 h-5" />
            <input
              type="text"
              placeholder="Search menus..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-blue-800/30 border border-blue-500/30 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent backdrop-blur-sm"
            />
          </div>
        </div>

        {/* Module Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {filteredModules.map((module) => {
            const Icon = module.icon;
            return (
              <button
                key={module.name}
                onClick={() => navigate(module.path)}
                className="group relative bg-white/10 backdrop-blur-sm hover:bg-white/20 rounded-xl p-6 transition-all duration-200 hover:scale-105 hover:shadow-xl border border-white/20 hover:border-white/30"
              >
                {/* Icon Container */}
                <div className="flex flex-col items-center space-y-3">
                  <div
                    className={`${module.color} w-16 h-16 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow`}
                  >
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  
                  {/* Module Name */}
                  <div className="text-center">
                    <h3 className="text-white font-medium text-sm leading-tight">
                      {module.name}
                    </h3>
                  </div>
                </div>

                {/* Hover Tooltip */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                  {module.description}
                </div>
              </button>
            );
          })}
        </div>

        {/* No Results */}
        {filteredModules.length === 0 && (
          <div className="text-center py-12">
            <p className="text-white/70 text-lg">No modules found matching "{searchQuery}"</p>
          </div>
        )}
      </div>
      {/* Change Password Modal */}
      {showChangePassword && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-800">Change Password</h2>
              <button
                onClick={() => {
                  setShowChangePassword(false);
                  setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                  setPasswordError('');
                  setPasswordSuccess('');
                  setShowCurrentPassword(false);
                  setShowNewPassword(false);
                  setShowConfirmPassword(false);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleChangePassword} className="px-6 py-4 space-y-4">
              {passwordError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {passwordError}
                </div>
              )}
              {passwordSuccess && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
                  {passwordSuccess}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                <div className="relative">
                  <input
                    type={showCurrentPassword ? 'text' : 'password'}
                    value={passwordForm.current_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                    placeholder="Enter current password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                <div className="relative">
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    value={passwordForm.new_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                    placeholder="Enter new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={passwordForm.confirm_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                    placeholder="Confirm new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowChangePassword(false);
                    setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                    setPasswordError('');
                    setPasswordSuccess('');
                  }}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  disabled={passwordLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={passwordLoading}
                >
                  {passwordLoading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
