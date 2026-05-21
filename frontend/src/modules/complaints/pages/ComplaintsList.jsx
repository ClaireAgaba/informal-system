import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Plus, Search, Filter, Eye, Clock, CheckCircle, XCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import complaintsApi from '../services/complaintsApi';

const getUserFromStorage = () => {
  try {
    const userStr = localStorage.getItem('user');
    if (userStr) return JSON.parse(userStr);
  } catch (error) {
    console.error('Error parsing user data:', error);
  }
  return null;
};

const ComplaintsList = () => {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [assignedToFilter, setAssignedToFilter] = useState('');
  const [categories, setCategories] = useState([]);
  const [statistics, setStatistics] = useState(null);
  
  // Security / Role checks
  const currentUser = getUserFromStorage();
  const isCenterRep = currentUser?.user_type === 'center_representative';
  
  // Bulk Assign State
  const [staffUsers, setStaffUsers] = useState([]);
  const [selectedComplaints, setSelectedComplaints] = useState([]);
  const [selectedAssignee, setSelectedAssignee] = useState('');
  const [assigning, setAssigning] = useState(false);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    fetchCategories();
    fetchStatistics();
    if (!isCenterRep) {
      fetchStaffUsers();
    }
  }, []);

  useEffect(() => {
    fetchComplaints();
  }, [statusFilter, categoryFilter, assignedToFilter, currentPage]);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const params = { page: currentPage };
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (searchQuery) params.search = searchQuery;
      if (assignedToFilter) params.helpdesk_team = assignedToFilter;
      
      const response = await complaintsApi.getComplaints(params);
      if (response.data && response.data.results !== undefined) {
        setComplaints(response.data.results);
        setTotalItems(response.data.count || 0);
      } else {
        setComplaints(response.data || []);
        setTotalItems((response.data || []).length);
      }
    } catch (error) {
      console.error('Error fetching complaints:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await complaintsApi.getCategories();
      setCategories(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await complaintsApi.getStatistics();
      setStatistics(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchStaffUsers = async () => {
    try {
      const response = await complaintsApi.getStaffUsers();
      setStaffUsers(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching staff users:', error);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (currentPage === 1) {
      fetchComplaints();
    } else {
      setCurrentPage(1);
    }
  };

  const handleBulkAssign = async () => {
    if (!selectedAssignee || selectedComplaints.length === 0) return;
    try {
      setAssigning(true);
      await complaintsApi.bulkAssignComplaints(selectedComplaints, selectedAssignee);
      setSelectedComplaints([]);
      setSelectedAssignee('');
      fetchComplaints();
      fetchStatistics();
    } catch (error) {
      console.error('Error bulk assigning complaints:', error);
      alert('Failed to assign complaints');
    } finally {
      setAssigning(false);
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedComplaints(displayedComplaints.map(c => c.id));
    } else {
      setSelectedComplaints([]);
    }
  };

  const handleSelectOne = (id) => {
    if (selectedComplaints.includes(id)) {
      setSelectedComplaints(selectedComplaints.filter(cId => cId !== id));
    } else {
      setSelectedComplaints([...selectedComplaints, id]);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  const getStatusBadge = (status) => {
    const statusConfig = {
      new: { color: 'bg-blue-100 text-blue-800', icon: Clock, label: 'New' },
      in_progress: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'In Progress' },
      done: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Done' },
      cancelled: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Cancelled' },
    };

    const config = statusConfig[status] || statusConfig.new;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
  };

  // Using complaints directly since API handles searching and pagination
  const displayedComplaints = complaints;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Complaints</h1>
            <p className="text-gray-600 mt-1">Manage and track complaints from assessment centers</p>
          </div>
          <button
            onClick={() => navigate('/complaints/create')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Complaint
          </button>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.total}</p>
                </div>
                <FileText className="w-8 h-8 text-gray-400" />
              </div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg shadow border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600">New</p>
                  <p className="text-2xl font-bold text-blue-900">{statistics.new}</p>
                </div>
                <Clock className="w-8 h-8 text-blue-400" />
              </div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg shadow border border-yellow-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-yellow-600">In Progress</p>
                  <p className="text-2xl font-bold text-yellow-900">{statistics.in_progress}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-400" />
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg shadow border border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600">Done</p>
                  <p className="text-2xl font-bold text-green-900">{statistics.done}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>
            </div>
            <div className="bg-red-50 p-4 rounded-lg shadow border border-red-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-600">Cancelled</p>
                  <p className="text-2xl font-bold text-red-900">{statistics.cancelled}</p>
                </div>
                <XCircle className="w-8 h-8 text-red-400" />
              </div>
            </div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            <div className="md:col-span-3 lg:col-span-3">
              <form onSubmit={handleSearch} className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search ticket, center..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </form>
            </div>
            <div className="md:col-span-2 lg:col-span-2">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  if (currentPage !== 1) setCurrentPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Status</option>
                <option value="new">New</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div className="md:col-span-2 lg:col-span-2">
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  if (currentPage !== 1) setCurrentPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>
            
            {!isCenterRep ? (
              <div className="md:col-span-2 lg:col-span-2">
                <select
                  value={assignedToFilter}
                  onChange={(e) => {
                    setAssignedToFilter(e.target.value);
                    if (currentPage !== 1) setCurrentPage(1);
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Assignees</option>
                  <option value={currentUser?.id}>Assigned to Me</option>
                  {staffUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.first_name} {user.last_name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="md:col-span-2 lg:col-span-2"></div>
            )}

            <div className="md:col-span-3 lg:col-span-3 flex justify-end items-center space-x-3">
              <div className="text-sm text-gray-600 hidden xl:block">
                <span>{totalItems} total</span>
              </div>
              <div className="text-sm font-medium text-gray-700 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex border border-gray-300 rounded-lg overflow-hidden shrink-0">
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-2 py-2 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Previous Page"
                >
                  <ChevronLeft className="w-5 h-5 text-gray-600" />
                </button>
                <div className="w-px bg-gray-300"></div>
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages || totalPages === 0}
                  className="px-2 py-2 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Next Page"
                >
                  <ChevronRight className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bulk Action Bar */}
      {!isCenterRep && selectedComplaints.length > 0 && (
        <div className="bg-blue-50 p-4 rounded-lg shadow border border-blue-200 mb-6 flex items-center justify-between">
           <span className="text-blue-800 font-medium">{selectedComplaints.length} selected</span>
           <div className="flex items-center space-x-3">
             <select 
               value={selectedAssignee}
               onChange={(e) => setSelectedAssignee(e.target.value)}
               className="px-4 py-2 border border-blue-300 rounded-lg bg-white"
             >
                <option value="">Select Officer...</option>
                {staffUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.first_name} {user.last_name}
                  </option>
                ))}
             </select>
             <button
               onClick={handleBulkAssign}
               disabled={!selectedAssignee || assigning}
               className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
             >
               {assigning ? 'Assigning...' : 'Assign Selected'}
             </button>
           </div>
        </div>
      )}

      {/* Complaints Table */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-x-auto">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : displayedComplaints.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No complaints found</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new complaint.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {!isCenterRep && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-10">
                    <input type="checkbox" 
                      onChange={handleSelectAll} 
                      checked={displayedComplaints.length > 0 && selectedComplaints.length === displayedComplaints.length}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
                    />
                  </th>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Ticket
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Center
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Series
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Occupation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Category
                </th>
                {!isCenterRep && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Assigned Officer
                  </th>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedComplaints.map((complaint) => (
                <tr 
                  key={complaint.id} 
                  className="hover:bg-blue-50 transition-colors"
                >
                  {!isCenterRep && (
                    <td className="px-4 py-3 whitespace-nowrap">
                      <input type="checkbox"
                        checked={selectedComplaints.includes(complaint.id)}
                        onChange={() => handleSelectOne(complaint.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                  )}
                  <td className="px-4 py-3 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    <div className="text-sm font-medium text-blue-600">{complaint.ticket_number}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    <div className="text-sm text-gray-900">
                      {new Date(complaint.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-4 py-3 cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    <div className="text-sm text-gray-900 truncate max-w-[200px]" title={complaint.exam_center_name}>
                      {complaint.exam_center_name}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    <div className="text-sm text-gray-900">{complaint.exam_series_name}</div>
                  </td>
                  <td className="px-4 py-3 cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    <div className="text-sm text-gray-900 truncate max-w-[150px]" title={complaint.program_name}>
                      {complaint.program_name}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    <div className="text-sm text-gray-900">{complaint.category_name}</div>
                  </td>
                  {!isCenterRep && (
                    <td className="px-4 py-3 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                      <div className="text-sm text-gray-900">{complaint.helpdesk_team_name || 'Unassigned'}</div>
                    </td>
                  )}
                  <td className="px-4 py-3 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/complaints/${complaint.id}`)}>
                    {getStatusBadge(complaint.status)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        
        {/* Bottom Pagination */}
        {displayedComplaints.length > 0 && totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing <span className="font-medium">{((currentPage - 1) * pageSize) + 1}</span> to <span className="font-medium">{Math.min(currentPage * pageSize, totalItems)}</span> of <span className="font-medium">{totalItems}</span> results
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
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

export default ComplaintsList;
