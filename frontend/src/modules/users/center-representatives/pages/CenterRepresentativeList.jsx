import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Search, Eye, Edit, Trash2, RefreshCw, Power, PowerOff, AlertTriangle, Link } from 'lucide-react';
import centerRepresentativeApi from '../../services/centerRepresentativeApi';

const CenterRepresentativeList = () => {
  const navigate = useNavigate();
  const [representatives, setRepresentatives] = useState([]);
  const [orphanedUsers, setOrphanedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showOrphaned, setShowOrphaned] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    fetchRepresentatives();
    fetchOrphanedUsers();
  }, [currentPage, debouncedSearchTerm, statusFilter]);

  const fetchOrphanedUsers = async () => {
    try {
      const response = await centerRepresentativeApi.getOrphanedUsers();
      setOrphanedUsers(response.data.results || []);
    } catch (error) {
      console.error('Error fetching orphaned users:', error);
    }
  };

  const fetchRepresentatives = async () => {
    try {
      setLoading(true);
      const params = { page: currentPage };
      if (debouncedSearchTerm.trim()) {
        params.search = debouncedSearchTerm.trim();
      }
      if (statusFilter !== 'all') {
        params.account_status = statusFilter;
      }
      const response = await centerRepresentativeApi.getAll(params);
      const data = response.data;
      
      if (data.results) {
        setRepresentatives(data.results);
        setTotalCount(data.count || 0);
        setTotalPages(Math.ceil((data.count || 0) / pageSize));
      } else {
        setRepresentatives(data || []);
        setTotalCount(data?.length || 0);
        setTotalPages(1);
      }
    } catch (error) {
      console.error('Error fetching center representatives:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this center representative?')) {
      try {
        await centerRepresentativeApi.delete(id);
        fetchRepresentatives();
      } catch (error) {
        console.error('Error deleting center representative:', error);
        alert('Failed to delete center representative');
      }
    }
  };

  const handleResetPassword = async (id, fullname) => {
    if (window.confirm(`Reset password for ${fullname} to default (uvtab)?`)) {
      try {
        await centerRepresentativeApi.resetPassword(id);
        alert('Password reset successfully to uvtab');
      } catch (error) {
        console.error('Error resetting password:', error);
        alert('Failed to reset password');
      }
    }
  };

  const handleToggleStatus = async (rep) => {
    try {
      if (rep.account_status === 'active') {
        await centerRepresentativeApi.deactivate(rep.id);
      } else {
        await centerRepresentativeApi.activate(rep.id);
      }
      fetchRepresentatives();
    } catch (error) {
      console.error('Error toggling status:', error);
      alert('Failed to update status');
    }
  };

  const filteredRepresentatives = representatives;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading center representatives...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Center Representatives</h1>
            <p className="text-gray-600 mt-1">Manage assessment center representatives</p>
          </div>
          <button
            onClick={() => navigate('/users/center-representatives/create')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add Representative
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by name, email, center, or contact..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>
      </div>

      {/* Orphaned Users Warning */}
      {orphanedUsers.length > 0 && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
              <span className="text-yellow-800">
                <strong>{orphanedUsers.length}</strong> user(s) with type "center_representative" have no profile record. 
                These users can login but won't appear in searches.
              </span>
            </div>
            <button
              onClick={() => setShowOrphaned(!showOrphaned)}
              className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
            >
              {showOrphaned ? 'Hide' : 'Show'} Details
            </button>
          </div>
          
          {showOrphaned && (
            <div className="mt-4">
              <table className="min-w-full divide-y divide-yellow-200">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Username/Email</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Name</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Status</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Date Joined</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-yellow-800 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-yellow-100">
                  {orphanedUsers.map(user => (
                    <tr key={user.id}>
                      <td className="px-4 py-2 text-sm text-yellow-900">{user.email || user.username}</td>
                      <td className="px-4 py-2 text-sm text-yellow-900">
                        {user.first_name} {user.last_name}
                      </td>
                      <td className="px-4 py-2 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm text-yellow-900">
                        {new Date(user.date_joined).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button
                          onClick={() => navigate(`/users/center-representatives/link/${user.id}`)}
                          className="inline-flex items-center px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          <Link className="w-3 h-3 mr-1" />
                          Create Profile
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Representatives</p>
              <p className="text-2xl font-bold text-gray-900">{totalCount}</p>
            </div>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {representatives.filter(r => r.account_status === 'active').length}
              </p>
            </div>
            <Power className="w-8 h-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Inactive</p>
              <p className="text-2xl font-bold text-gray-600">
                {representatives.filter(r => r.account_status !== 'active').length}
              </p>
            </div>
            <PowerOff className="w-8 h-8 text-gray-600" />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Representative
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Center
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRepresentatives.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    No center representatives found
                  </td>
                </tr>
              ) : (
                filteredRepresentatives.map((rep) => (
                  <tr key={rep.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 font-semibold">
                            {rep.fullname?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{rep.fullname}</div>
                          <div className="text-sm text-gray-500">{rep.center_number}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{rep.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{rep.contact}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{rep.center_name}</div>
                      {rep.branch_name && (
                        <div className="text-sm text-gray-500">{rep.branch_name}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        rep.account_status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : rep.account_status === 'suspended'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {rep.account_status_display}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate(`/users/center-representatives/${rep.id}`)}
                          className="text-blue-600 hover:text-blue-900"
                          title="View Details"
                        >
                          <Eye className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => navigate(`/users/center-representatives/${rep.id}/edit`)}
                          className="text-yellow-600 hover:text-yellow-900"
                          title="Edit"
                        >
                          <Edit className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleResetPassword(rep.id, rep.fullname)}
                          className="text-purple-600 hover:text-purple-900"
                          title="Reset Password"
                        >
                          <RefreshCw className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleToggleStatus(rep)}
                          className={rep.account_status === 'active' ? 'text-orange-600 hover:text-orange-900' : 'text-green-600 hover:text-green-900'}
                          title={rep.account_status === 'active' ? 'Deactivate' : 'Activate'}
                        >
                          {rep.account_status === 'active' ? (
                            <PowerOff className="w-5 h-5" />
                          ) : (
                            <Power className="w-5 h-5" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(rep.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Page {currentPage} of {totalPages} ({totalCount} total)
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Previous
              </button>
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1 border rounded-md ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'border-gray-300 hover:bg-gray-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CenterRepresentativeList;
