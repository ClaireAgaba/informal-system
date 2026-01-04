import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Briefcase, 
  Building2, 
  FileText, 
  Menu,
  X,
  Banknote,
  FileSpreadsheet,
  MessageSquare,
  BarChart3
} from 'lucide-react';
import { useState, useEffect } from 'react';

const allNavigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
  { name: 'Candidates', href: '/candidates', icon: Users, roles: ['all'] },
  { name: 'Occupations', href: '/occupations', icon: Briefcase, roles: ['staff', 'support_staff'] },
  { name: 'Assessment Centers', href: '/assessment-centers', icon: Building2, roles: ['staff', 'support_staff'] },
  { name: 'Assessment Series', href: '/assessment-series', icon: FileText, roles: ['staff', 'support_staff'] },
  { name: 'Reports', href: '/reports', icon: FileText, roles: ['all'] },
  { name: 'UVTAB Fees', href: '/fees', icon: Banknote, roles: ['all'] },
  { name: 'Marksheets', href: '/marksheets', icon: FileSpreadsheet, roles: ['staff', 'support_staff'] },
  { name: 'Complaints', href: '/complaints', icon: MessageSquare, roles: ['all'] },
  { name: 'Statistics', href: '/statistics', icon: BarChart3, roles: ['staff', 'support_staff'] },
  { name: 'Users', href: '/users', icon: Users, roles: ['staff', 'support_staff'] },
];

const DashboardLayout = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    // Get user from localStorage
    const userStr = localStorage.getItem('user');
    console.log('DashboardLayout - Raw user string:', userStr);
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        console.log('DashboardLayout - Parsed user:', user);
        setCurrentUser(user);
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  // Get user display name based on user type
  const getUserDisplayName = () => {
    console.log('getUserDisplayName called, currentUser:', currentUser);
    if (!currentUser) {
      console.log('No current user, returning "User"');
      return 'User';
    }
    
    console.log('User type:', currentUser.user_type);
    if (currentUser.user_type === 'center_representative') {
      // For center reps, show their full name from the profile
      console.log('Center rep data:', currentUser.center_representative);
      if (currentUser.center_representative?.fullname) {
        console.log('Returning fullname:', currentUser.center_representative.fullname);
        return currentUser.center_representative.fullname;
      }
      const name = currentUser.first_name && currentUser.last_name 
        ? `${currentUser.first_name} ${currentUser.last_name}`
        : currentUser.username;
      console.log('Returning name:', name);
      return name;
    } else if (currentUser.user_type === 'staff') {
      return currentUser.first_name && currentUser.last_name
        ? `${currentUser.first_name} ${currentUser.last_name}`
        : 'Staff User';
    } else if (currentUser.user_type === 'support_staff') {
      return currentUser.first_name && currentUser.last_name
        ? `${currentUser.first_name} ${currentUser.last_name}`
        : 'Support Staff';
    }
    
    return currentUser.username || 'User';
  };

  // Get user role/center for display
  const getUserRole = () => {
    if (!currentUser) return '';
    
    if (currentUser.user_type === 'center_representative' && currentUser.center_representative?.assessment_center) {
      return currentUser.center_representative.assessment_center.center_name;
    } else if (currentUser.user_type === 'staff') {
      return 'Staff';
    } else if (currentUser.user_type === 'support_staff') {
      return 'Support Staff';
    }
    
    return '';
  };

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!currentUser) return 'U';
    
    if (currentUser.first_name && currentUser.last_name) {
      return `${currentUser.first_name.charAt(0)}${currentUser.last_name.charAt(0)}`.toUpperCase();
    } else if (currentUser.first_name) {
      return currentUser.first_name.charAt(0).toUpperCase();
    } else if (currentUser.username) {
      return currentUser.username.charAt(0).toUpperCase();
    }
    
    return 'U';
  };

  // Filter navigation based on user role
  const getAccessibleNavigation = () => {
    if (!currentUser) return allNavigation;
    
    return allNavigation.filter(item => {
      // If item is accessible to all roles
      if (item.roles.includes('all')) return true;
      
      // Check if user's role is in the allowed roles
      return item.roles.includes(currentUser.user_type);
    });
  };

  const navigation = getAccessibleNavigation();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-primary-600">EMIS</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <nav className="px-4 py-6 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.href);
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex items-center justify-between h-16 px-6 bg-white border-b border-gray-200">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex items-center ml-auto space-x-4">
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">{getUserDisplayName()}</div>
              {getUserRole() && (
                <div className="text-xs text-gray-500">{getUserRole()}</div>
              )}
            </div>
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-medium">
              {getUserInitials()}
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
