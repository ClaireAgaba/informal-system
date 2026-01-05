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
  LogOut,
  ChevronDown,
  MessageSquare,
  BarChart3,
} from 'lucide-react';

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
    name: 'Statistics',
    icon: BarChart3,
    path: '/statistics',
    color: 'bg-blue-600',
    description: 'System Analytics & Reports',
  },
];

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const dropdownRef = useRef(null);

  // Load user from localStorage
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setCurrentUser(user);
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

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
    let accessibleModules = modules;
    
    // Filter by user type
    if (currentUser?.user_type === 'center_representative') {
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
    </div>
  );
};

export default Dashboard;
