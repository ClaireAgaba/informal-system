import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Search, Eye, Edit, Trash2, RefreshCw, Power, PowerOff } from 'lucide-react';
import centerRepresentativeApi from '../../services/centerRepresentativeApi';

const CenterRepresentativeList = () => {
  const navigate = useNavigate();
  const [representatives, setRepresentatives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchRepresentatives();
  }, []);

  const fetchRepresentatives = async () => {
    try {
      setLoading(true);
      const response = await centerRepresentativeApi.getAll();
      setRepresentatives(response.data.results || response.data || []);
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
    if (window.confirm(`Reset password for ${fullname} to default (uvtab@2025)?`)) {
      try {
        await centerRepresentativeApi.resetPassword(id);
        alert('Password reset successfully to uvtab@2025');
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

  const filteredRepresentatives = representatives.filter(rep => {
    const matchesSearch = 
      rep.fullname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rep.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rep.center_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rep.contact?.includes(searchTerm);
    
    const matchesStatus = statusFilter === 'all' || rep.account_status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

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
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Representatives</p>
              <p className="text-2xl font-bold text-gray-900">{representatives.length}</p>
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
      </div>
    </div>
  );
};

export default CenterRepresentativeList;
