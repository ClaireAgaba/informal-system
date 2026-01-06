import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Eye,
  CheckSquare,
  Square,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import candidateApi from '../services/candidateApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';

const CandidateList = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [selectAllPages, setSelectAllPages] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [exporting, setExporting] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    registration_category: '',
    assessment_center: '',
    occupation: '',
    has_disability: '',
    is_refugee: '',
    verification_status: '',
  });

  // Fetch candidates
  const { data, isLoading, error } = useQuery({
    queryKey: ['candidates', currentPage, pageSize, searchQuery, filters],
    queryFn: () => candidateApi.getAll({
      page: currentPage,
      page_size: pageSize,
      search: searchQuery,
      ...filters,
    }),
  });

  // Fetch filter options
  const { data: centersData } = useQuery({
    queryKey: ['centers-filter'],
    queryFn: () => assessmentCenterApi.getAll({ page_size: 1000 }),
  });

  const { data: occupationsData } = useQuery({
    queryKey: ['occupations-filter'],
    queryFn: () => occupationApi.getAll({ page_size: 500 }),
  });

  const { data: sectorsData } = useQuery({
    queryKey: ['sectors-filter'],
    queryFn: () => occupationApi.sectors.getAll(),
  });

  const centers = centersData?.data?.results || centersData?.data || [];
  const occupations = occupationsData?.data?.results || occupationsData?.data || [];
  const sectors = sectorsData?.data?.results || sectorsData?.data || [];

  const candidates = data?.data?.results || [];
  const totalCount = data?.data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  // Select all candidates on current page
  const handleSelectAll = () => {
    if (selectedCandidates.length === candidates.length && !selectAllPages) {
      setSelectedCandidates([]);
      setSelectAllPages(false);
    } else {
      setSelectedCandidates(candidates.map((c) => c.id));
    }
  };

  // Select all candidates across all pages
  const handleSelectAllPages = () => {
    setSelectAllPages(true);
    setSelectedCandidates(candidates.map((c) => c.id));
  };

  // Clear selection
  const handleClearSelection = () => {
    setSelectedCandidates([]);
    setSelectAllPages(false);
  };

  // Toggle individual candidate selection
  const handleSelectCandidate = (id) => {
    setSelectAllPages(false);
    if (selectedCandidates.includes(id)) {
      setSelectedCandidates(selectedCandidates.filter((cId) => cId !== id));
    } else {
      setSelectedCandidates([...selectedCandidates, id]);
    }
  };

  // Export candidates
  const handleExport = async () => {
    try {
      setExporting(true);
      const payload = selectAllPages 
        ? { export_all: true, ...filters, search: searchQuery }
        : { ids: selectedCandidates };
      
      const response = await candidateApi.export(payload);
      
      // Create download link
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `candidates_export_${new Date().toISOString().slice(0,10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  // Clear filters
  const handleClearFilters = () => {
    setFilters({
      registration_category: '',
      assessment_center: '',
      occupation: '',
      has_disability: '',
      is_refugee: '',
      verification_status: '',
    });
    setSearchQuery('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Candidates</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage and view all registered candidates
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate('/candidates/new')}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Candidate
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <Card.Content>
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex items-center space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search by name, registration number, phone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <Button
                variant={showFilters ? 'primary' : 'outline'}
                size="md"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 pt-4 border-t">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={filters.registration_category}
                    onChange={(e) => setFilters({ ...filters, registration_category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    <option value="modular">Modular</option>
                    <option value="formal">Formal</option>
                    <option value="workers_pas">Worker's PAS</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Disability
                  </label>
                  <select
                    value={filters.has_disability}
                    onChange={(e) => setFilters({ ...filters, has_disability: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Refugee
                  </label>
                  <select
                    value={filters.is_refugee}
                    onChange={(e) => setFilters({ ...filters, is_refugee: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    value={filters.verification_status}
                    onChange={(e) => setFilters({ ...filters, verification_status: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    <option value="pending_verification">Pending</option>
                    <option value="verified">Verified</option>
                    <option value="declined">Declined</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <Button
                    variant="ghost"
                    size="md"
                    onClick={handleClearFilters}
                    className="w-full"
                  >
                    Clear Filters
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card.Content>
      </Card>

      {/* Bulk Actions */}
      {(selectedCandidates.length > 0 || selectAllPages) && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-primary-900">
                {selectAllPages ? (
                  <>All {totalCount} candidates selected</>
                ) : (
                  <>{selectedCandidates.length} candidate(s) selected</>
                )}
              </span>
              {selectedCandidates.length === candidates.length && !selectAllPages && totalCount > pageSize && (
                <button 
                  onClick={handleSelectAllPages}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Select all {totalCount} candidates
                </button>
              )}
              {selectAllPages && (
                <button 
                  onClick={handleClearSelection}
                  className="text-sm text-gray-600 hover:text-gray-800 underline"
                >
                  Clear selection
                </button>
              )}
            </div>
            <div className="relative">
              <select
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 cursor-pointer"
                onChange={(e) => {
                  if (e.target.value === 'export') {
                    handleExport();
                  }
                  e.target.value = '';
                }}
                disabled={exporting}
                defaultValue=""
              >
                <option value="" disabled>⚙ Action</option>
                <option value="export">{exporting ? 'Exporting...' : 'Export'}</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              {/* Filter Row */}
              <tr className="bg-gray-100">
                <th className="px-2 py-2"></th>
                <th className="px-2 py-2"></th>
                <th className="px-2 py-2">
                  <input
                    type="text"
                    placeholder="Reg No"
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </th>
                <th className="px-2 py-2">
                  <input
                    type="text"
                    placeholder="Name"
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.assessment_center}
                    onChange={(e) => setFilters({ ...filters, assessment_center: e.target.value })}
                  >
                    <option value="">Select</option>
                    {centers.map((c) => (
                      <option key={c.id} value={c.id}>{c.center_number} - {c.center_name}</option>
                    ))}
                  </select>
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.registration_category}
                    onChange={(e) => setFilters({ ...filters, registration_category: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="modular">Modular</option>
                    <option value="formal">Formal</option>
                    <option value="workers_pas">Worker's PAS</option>
                  </select>
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.occupation}
                    onChange={(e) => setFilters({ ...filters, occupation: e.target.value })}
                  >
                    <option value="">Select</option>
                    {occupations.map((o) => (
                      <option key={o.id} value={o.id}>{o.occ_code} - {o.occ_name}</option>
                    ))}
                  </select>
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.sector || ''}
                    onChange={(e) => setFilters({ ...filters, sector: e.target.value })}
                  >
                    <option value="">Select</option>
                    {sectors.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.has_disability}
                    onChange={(e) => setFilters({ ...filters, has_disability: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.is_refugee}
                    onChange={(e) => setFilters({ ...filters, is_refugee: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.verification_status}
                    onChange={(e) => setFilters({ ...filters, verification_status: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="pending_verification">Pending</option>
                    <option value="verified">Verified</option>
                    <option value="declined">Declined</option>
                  </select>
                </th>
                <th className="px-2 py-2"></th>
              </tr>
              {/* Header Row */}
              <tr>
                <th className="px-4 py-3 text-left">
                  <button onClick={handleSelectAll}>
                    {selectedCandidates.length === candidates.length && candidates.length > 0 ? (
                      <CheckSquare className="w-5 h-5 text-primary-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Image
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reg No
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Full Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Center
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occupation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sector
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Disability
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Refugee
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="12" className="px-4 py-8 text-center text-gray-500">
                    Loading candidates...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="12" className="px-4 py-8 text-center text-red-500">
                    Error loading candidates: {error.message}
                  </td>
                </tr>
              ) : candidates.length === 0 ? (
                <tr>
                  <td colSpan="12" className="px-4 py-8 text-center text-gray-500">
                    No candidates found
                  </td>
                </tr>
              ) : (
                candidates.map((candidate) => (
                  <tr 
                    key={candidate.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/candidates/${candidate.id}`)}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleSelectCandidate(candidate.id)}>
                        {selectedCandidates.includes(candidate.id) ? (
                          <CheckSquare className="w-5 h-5 text-primary-600" />
                        ) : (
                          <Square className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      {candidate.passport_photo ? (
                        <img
                          src={candidate.passport_photo}
                          alt={candidate.full_name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-sm font-medium">
                          {candidate.full_name?.charAt(0) || '?'}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {candidate.is_submitted ? (
                        candidate.registration_number || '-'
                      ) : (
                        <span className="text-orange-600 font-medium">Not Submitted</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {candidate.full_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {candidate.assessment_center?.center_name || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        candidate.registration_category === 'modular'
                          ? 'bg-blue-100 text-blue-800'
                          : candidate.registration_category === 'formal'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {candidate.registration_category === 'modular' ? 'Modular' :
                         candidate.registration_category === 'formal' ? 'Formal' :
                         candidate.registration_category === 'workers_pas' ? "Worker's PAS" : '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {candidate.occupation?.occ_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {candidate.sector?.name || '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {candidate.has_disability ? (
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-orange-100 text-orange-800">
                          Yes
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">No</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {candidate.is_refugee ? (
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
                          Yes
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">No</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        candidate.verification_status === 'verified'
                          ? 'bg-green-100 text-green-800'
                          : candidate.verification_status === 'declined'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {candidate.verification_status === 'verified' ? 'Verified' :
                         candidate.verification_status === 'declined' ? 'Declined' : 'Pending'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => navigate(`/candidates/${candidate.id}`)}
                          className="text-gray-600 hover:text-primary-600"
                          title="View"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/candidates/${candidate.id}/edit`)}
                          className="text-gray-600 hover:text-primary-600"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {/* Handle delete */}}
                          className="text-gray-600 hover:text-red-600"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
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
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">
              Showing <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> to{' '}
              <span className="font-medium">
                {Math.min(currentPage * pageSize, totalCount)}
              </span>{' '}
              of <span className="font-medium">{totalCount}</span> candidates
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="10">10 per page</option>
              <option value="20">20 per page</option>
              <option value="50">50 per page</option>
              <option value="100">100 per page</option>
            </select>

            <div className="flex items-center space-x-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pageNum = i + 1;
                return (
                  <Button
                    key={pageNum}
                    variant={currentPage === pageNum ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setCurrentPage(pageNum)}
                  >
                    {pageNum}
                  </Button>
                );
              })}
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CandidateList;
