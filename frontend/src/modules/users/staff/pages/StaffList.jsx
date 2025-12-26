import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Eye, Edit, Plus, Search } from 'lucide-react';
import userApi from '../../services/userApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';

const StaffList = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ['staff', page, searchTerm, statusFilter],
    queryFn: () =>
      userApi.staff.getAll({
        page,
        page_size: pageSize,
        search: searchTerm,
        account_status: statusFilter,
      }),
  });

  const staff = data?.data?.results || [];
  const totalPages = data?.data?.count ? Math.ceil(data.data.count / pageSize) : 1;

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Staff Members</h1>
            <p className="text-gray-600 mt-1">Manage UVTAB staff members</p>
          </div>
          <Button variant="primary" size="md" onClick={() => navigate('/users/staff/new')}>
            <Plus className="w-4 h-4 mr-2" />
            Add Staff
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <Card.Content className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search by name, email, or contact..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Full Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contact</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date Joined</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr><td colSpan="7" className="px-6 py-4 text-center text-gray-500">Loading...</td></tr>
              ) : error ? (
                <tr><td colSpan="7" className="px-6 py-4 text-center text-red-500">Error: {error.message}</td></tr>
              ) : staff.length === 0 ? (
                <tr><td colSpan="7" className="px-6 py-4 text-center text-gray-500">No staff found</td></tr>
              ) : (
                staff.map((member) => (
                  <tr
                    key={member.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/users/staff/${member.id}`)}
                  >
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{member.full_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{member.email}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{member.contact}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{member.department_name || 'N/A'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        member.account_status === 'active' ? 'bg-green-100 text-green-800' :
                        member.account_status === 'suspended' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {member.account_status_display}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{formatDate(member.date_joined)}</td>
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end space-x-2">
                        <button onClick={() => navigate(`/users/staff/${member.id}`)} className="text-gray-600 hover:text-primary-600">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button onClick={() => navigate(`/users/staff/${member.id}/edit`)} className="text-gray-600 hover:text-primary-600">
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">Page {page} of {totalPages}</div>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                  Previous
                </Button>
                <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default StaffList;
