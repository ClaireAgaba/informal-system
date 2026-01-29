import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Search,
  Filter,
  Eye,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  CheckSquare,
  Square,
  Calendar,
  UserMinus,
  Trash2,
  Edit,
} from 'lucide-react';
import candidateApi from '../services/candidateApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import assessmentSeriesApi from '@modules/assessment-series/services/assessmentSeriesApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const EnrollmentList = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [showFilters, setShowFilters] = useState(true);
  const [selectedEnrollments, setSelectedEnrollments] = useState([]);
  const [selectAllPages, setSelectAllPages] = useState(false);
  
  // Modal states
  const [showChangeSeriesModal, setShowChangeSeriesModal] = useState(false);
  const [showDeEnrollModal, setShowDeEnrollModal] = useState(false);
  const [showClearDataModal, setShowClearDataModal] = useState(false);
  const [showUpdateEnrollmentModal, setShowUpdateEnrollmentModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedNewSeries, setSelectedNewSeries] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [selectedModules, setSelectedModules] = useState([]);
  const [selectedPapers, setSelectedPapers] = useState([]);
  const [availableLevels, setAvailableLevels] = useState([]);
  const [availableModules, setAvailableModules] = useState([]);
  const [availablePapers, setAvailablePapers] = useState([]);
  
  const [filters, setFilters] = useState({
    registration_category: '',
    assessment_series: '',
    assessment_center: '',
    occupation: '',
  });

  // Fetch enrollments
  const { data, isLoading, error } = useQuery({
    queryKey: ['enrollments', currentPage, pageSize, searchQuery, filters],
    queryFn: () => candidateApi.getAllEnrollments({
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

  const { data: seriesData } = useQuery({
    queryKey: ['series-filter'],
    queryFn: () => assessmentSeriesApi.getAll({ page_size: 100 }),
  });

  const centers = centersData?.data?.results || centersData?.data || [];
  const occupations = occupationsData?.data?.results || occupationsData?.data || [];
  const seriesList = seriesData?.data?.results || seriesData?.data || [];

  const enrollments = data?.data?.results || [];
  const totalCount = data?.data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  const handleClearFilters = () => {
    setFilters({
      registration_category: '',
      assessment_series: '',
      assessment_center: '',
      occupation: '',
    });
    setSearchQuery('');
  };

  // Select all enrollments on current page
  const handleSelectAll = () => {
    if (selectedEnrollments.length === enrollments.length && !selectAllPages) {
      setSelectedEnrollments([]);
      setSelectAllPages(false);
    } else {
      setSelectedEnrollments(enrollments.map((e) => e.id));
    }
  };

  // Select all enrollments across all pages
  const handleSelectAllPages = () => {
    setSelectAllPages(true);
    setSelectedEnrollments(enrollments.map((e) => e.id));
  };

  // Clear selection
  const handleClearSelection = () => {
    setSelectedEnrollments([]);
    setSelectAllPages(false);
  };

  // Toggle individual enrollment selection
  const handleSelectEnrollment = (id) => {
    setSelectAllPages(false);
    if (selectedEnrollments.includes(id)) {
      setSelectedEnrollments(selectedEnrollments.filter((eId) => eId !== id));
    } else {
      setSelectedEnrollments([...selectedEnrollments, id]);
    }
  };

  const getCategoryBadge = (category) => {
    const badges = {
      modular: 'bg-blue-100 text-blue-800',
      formal: 'bg-green-100 text-green-800',
      workers_pas: 'bg-purple-100 text-purple-800',
    };
    const labels = {
      modular: 'Modular',
      formal: 'Formal',
      workers_pas: "Worker's PAS",
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${badges[category] || 'bg-gray-100 text-gray-800'}`}>
        {labels[category] || category}
      </span>
    );
  };

  // Get selection count for display
  const getSelectionCount = () => {
    return selectAllPages ? totalCount : selectedEnrollments.length;
  };

  // Handle bulk change series
  const handleBulkChangeSeries = async () => {
    if (!selectedNewSeries) {
      toast.error('Please select a new assessment series');
      return;
    }
    
    setIsProcessing(true);
    try {
      const payload = {
        new_series_id: selectedNewSeries,
        select_all: selectAllPages,
        enrollment_ids: selectAllPages ? [] : selectedEnrollments,
        filters: selectAllPages ? { ...filters, search: searchQuery } : {},
      };
      
      const response = await candidateApi.bulkChangeEnrollmentSeries(payload);
      toast.success(response.data.message);
      
      // Reset state
      setShowChangeSeriesModal(false);
      setSelectedNewSeries('');
      handleClearSelection();
      queryClient.invalidateQueries(['enrollments']);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to change series');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle bulk de-enroll
  const handleBulkDeEnroll = async () => {
    setIsProcessing(true);
    try {
      const payload = {
        select_all: selectAllPages,
        enrollment_ids: selectAllPages ? [] : selectedEnrollments,
        filters: selectAllPages ? { ...filters, search: searchQuery } : {},
      };
      
      const response = await candidateApi.bulkDeEnrollByEnrollment(payload);
      
      if (response.data.skipped_with_marks?.length > 0) {
        toast.warning(
          `${response.data.success_count} de-enrolled, ${response.data.skipped_with_marks.length} skipped (have marks)`
        );
      } else {
        toast.success(response.data.message);
      }
      
      // Reset state
      setShowDeEnrollModal(false);
      handleClearSelection();
      queryClient.invalidateQueries(['enrollments']);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to de-enroll');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle bulk clear data
  const handleBulkClearData = async () => {
    setIsProcessing(true);
    try {
      const payload = {
        select_all: selectAllPages,
        enrollment_ids: selectAllPages ? [] : selectedEnrollments,
        filters: selectAllPages ? { ...filters, search: searchQuery } : {},
      };
      
      const response = await candidateApi.bulkClearEnrollmentData(payload);
      toast.success(response.data.message);
      
      // Reset state
      setShowClearDataModal(false);
      handleClearSelection();
      queryClient.invalidateQueries(['enrollments']);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to clear data');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle opening update enrollment modal - fetch levels/modules for selected occupation
  const handleOpenUpdateEnrollment = async () => {
    // Get the occupation from filter or from first selected enrollment
    const occupationId = filters.occupation;
    if (!occupationId) {
      toast.error('Please filter by occupation first to load levels/modules');
      return;
    }
    
    try {
      // Fetch occupation details for levels
      const occResponse = await occupationApi.getById(occupationId);
      const occupation = occResponse.data;
      
      if (occupation.levels) {
        setAvailableLevels(occupation.levels);
      }
      
      // Fetch modules directly for this occupation
      const modulesResponse = await occupationApi.modules.getAll({ occupation: occupationId });
      setAvailableModules(modulesResponse.data.results || modulesResponse.data || []);
      
      // Fetch papers for Worker's PAS
      const papersResponse = await occupationApi.papers.getAll({ occupation: occupationId });
      setAvailablePapers(papersResponse.data.results || papersResponse.data || []);
      
      setShowUpdateEnrollmentModal(true);
    } catch (error) {
      toast.error('Failed to load occupation data');
    }
  };

  // Handle bulk update enrollment
  const handleBulkUpdateEnrollment = async () => {
    if (!selectedLevel && selectedModules.length === 0 && selectedPapers.length === 0) {
      toast.error('Please select a level, modules, or papers');
      return;
    }
    
    setIsProcessing(true);
    try {
      const payload = {
        select_all: selectAllPages,
        enrollment_ids: selectAllPages ? [] : selectedEnrollments,
        filters: selectAllPages ? { ...filters, search: searchQuery } : {},
        level_id: selectedLevel || null,
        module_ids: selectedModules,
        paper_ids: selectedPapers,
      };
      
      const response = await candidateApi.bulkUpdateEnrollment(payload);
      
      if (response.data.skipped?.length > 0) {
        toast.warning(
          `${response.data.updated_count} updated, ${response.data.skipped.length} skipped`
        );
      } else {
        toast.success(response.data.message);
      }
      
      // Reset state
      setShowUpdateEnrollmentModal(false);
      setSelectedLevel('');
      setSelectedModules([]);
      setSelectedPapers([]);
      handleClearSelection();
      queryClient.invalidateQueries(['enrollments']);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to update enrollments');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Enrollments</h1>
          <p className="text-sm text-gray-600 mt-1">
            View all candidate enrollments across assessment series
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/candidates')}
          >
            <ClipboardList className="w-4 h-4 mr-2" />
            Back to Candidates
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
                  placeholder="Search by registration number or name..."
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 pt-4 border-t">
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
                    Assessment Series
                  </label>
                  <select
                    value={filters.assessment_series}
                    onChange={(e) => setFilters({ ...filters, assessment_series: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    {seriesList.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Assessment Center
                  </label>
                  <select
                    value={filters.assessment_center}
                    onChange={(e) => setFilters({ ...filters, assessment_center: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    {centers.map((c) => (
                      <option key={c.id} value={c.id}>{c.center_number} - {c.center_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Occupation
                  </label>
                  <select
                    value={filters.occupation}
                    onChange={(e) => setFilters({ ...filters, occupation: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    {occupations.map((o) => (
                      <option key={o.id} value={o.id}>{o.occ_code} - {o.occ_name}</option>
                    ))}
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

      {/* Selection indicator with bulk actions */}
      {(selectedEnrollments.length > 0 || selectAllPages) && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-primary-900">
                {selectAllPages ? (
                  <>All {totalCount} enrollments selected</>
                ) : (
                  <>{selectedEnrollments.length} enrollment(s) selected</>
                )}
              </span>
              {selectedEnrollments.length === enrollments.length && !selectAllPages && totalCount > pageSize && (
                <button 
                  onClick={handleSelectAllPages}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Select all {totalCount} enrollments
                </button>
              )}
              {(selectAllPages || selectedEnrollments.length > 0) && (
                <button 
                  onClick={handleClearSelection}
                  className="text-sm text-gray-600 hover:text-gray-800 underline"
                >
                  Clear selection
                </button>
              )}
            </div>
            {/* Bulk Action Buttons */}
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowChangeSeriesModal(true)}
              >
                <Calendar className="w-4 h-4 mr-1" />
                Change Series
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeEnrollModal(true)}
                className="text-orange-600 border-orange-300 hover:bg-orange-50"
              >
                <UserMinus className="w-4 h-4 mr-1" />
                De-enroll
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowClearDataModal(true)}
                className="text-red-600 border-red-300 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Clear Data
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleOpenUpdateEnrollment}
                className="text-green-600 border-green-300 hover:bg-green-50"
              >
                <Edit className="w-4 h-4 mr-1" />
                Update Enrollment
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Results count */}
      <div className="text-sm text-gray-600">
        Showing {enrollments.length} of {totalCount} enrollments
      </div>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <button onClick={handleSelectAll}>
                    {selectedEnrollments.length === enrollments.length && enrollments.length > 0 ? (
                      <CheckSquare className="w-5 h-5 text-primary-600" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reg No
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occupation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Series
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Modules
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Level(s)
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                    Loading enrollments...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-red-500">
                    Error loading enrollments: {error.message}
                  </td>
                </tr>
              ) : enrollments.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                    No enrollments found
                  </td>
                </tr>
              ) : (
                enrollments.map((enrollment) => (
                  <tr 
                    key={enrollment.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/candidates/${enrollment.candidate_id}`)}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => handleSelectEnrollment(enrollment.id)}>
                        {selectedEnrollments.includes(enrollment.id) ? (
                          <CheckSquare className="w-5 h-5 text-primary-600" />
                        ) : (
                          <Square className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-primary-600">
                        {enrollment.registration_number}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-900">
                        {enrollment.candidate_name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {getCategoryBadge(enrollment.registration_category)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-900">
                        {enrollment.occupation_code && (
                          <span className="font-medium">{enrollment.occupation_code}</span>
                        )}
                        {enrollment.occupation_code && enrollment.occupation_name && ' - '}
                        {enrollment.occupation_name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-900">
                        {enrollment.assessment_series_name}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">
                        {enrollment.registration_category === 'modular' || enrollment.registration_category === 'workers_pas' 
                          ? (enrollment.modules_display || '-')
                          : '-'
                        }
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">
                        {enrollment.registration_category === 'formal' || enrollment.registration_category === 'workers_pas'
                          ? (enrollment.level_name || '-')
                          : '-'
                        }
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/candidates/${enrollment.candidate_id}`)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination - always show */}
        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-700">
              {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalCount)} of {totalCount}
            </span>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-gray-700">
                Page {currentPage} of {totalPages || 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage >= totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Change Series Modal */}
      {showChangeSeriesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                Change Assessment Series
              </h2>
              <button
                onClick={() => {
                  setShowChangeSeriesModal(false);
                  setSelectedNewSeries('');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>{getSelectionCount()}</strong> enrollment(s) selected
                </p>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-sm text-amber-800">
                  This will move selected enrollments and their results to the new series.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select New Assessment Series
                </label>
                <select
                  value={selectedNewSeries}
                  onChange={(e) => setSelectedNewSeries(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">-- Select Series --</option>
                  {seriesList.map((series) => (
                    <option key={series.id} value={series.id}>
                      {series.name} {series.is_active ? '(Active)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
              <Button
                variant="outline"
                onClick={() => {
                  setShowChangeSeriesModal(false);
                  setSelectedNewSeries('');
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleBulkChangeSeries}
                loading={isProcessing}
                disabled={isProcessing || !selectedNewSeries}
              >
                Change Series
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* De-enroll Modal */}
      {showDeEnrollModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                Confirm De-enrollment
              </h2>
              <button
                onClick={() => setShowDeEnrollModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>{getSelectionCount()}</strong> enrollment(s) selected
                </p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800 font-medium">Warning: This action will:</p>
                <ul className="text-sm text-red-800 list-disc list-inside mt-1">
                  <li>Delete the selected enrollments</li>
                  <li>Remove associated fees</li>
                  <li>Skip candidates with existing marks</li>
                </ul>
              </div>
              <p className="text-sm text-gray-600">
                Are you sure you want to de-enroll the selected candidates?
              </p>
            </div>
            <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
              <Button
                variant="outline"
                onClick={() => setShowDeEnrollModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleBulkDeEnroll}
                loading={isProcessing}
                disabled={isProcessing}
                className="bg-red-600 hover:bg-red-700"
              >
                De-enroll
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Clear Data Modal */}
      {showClearDataModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                Clear Results, Enrollments & Fees
              </h2>
              <button
                onClick={() => setShowClearDataModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>{getSelectionCount()}</strong> enrollment(s) selected
                </p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800 font-medium">⚠️ Warning: This action will permanently delete:</p>
                <ul className="text-sm text-red-800 list-disc list-inside mt-1">
                  <li>All results (marks) for the selected enrollments</li>
                  <li>The enrollments themselves</li>
                  <li>All associated fees/payments</li>
                </ul>
              </div>
              <p className="text-sm text-gray-600 font-medium">
                This action cannot be undone. Are you sure you want to proceed?
              </p>
            </div>
            <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
              <Button
                variant="outline"
                onClick={() => setShowClearDataModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleBulkClearData}
                loading={isProcessing}
                disabled={isProcessing}
                className="bg-red-600 hover:bg-red-700"
              >
                Clear All Data
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Update Enrollment Modal */}
      {showUpdateEnrollmentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                Update Enrollment
              </h2>
              <button
                onClick={() => {
                  setShowUpdateEnrollmentModal(false);
                  setSelectedLevel('');
                  setSelectedModules([]);
                  setSelectedPapers([]);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  <strong>{getSelectionCount()}</strong> enrollment(s) selected
                </p>
              </div>
              
              {/* For Formal - Select Level */}
              {filters.registration_category === 'formal' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Level (for Formal candidates)
                  </label>
                  <select
                    value={selectedLevel}
                    onChange={(e) => setSelectedLevel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">-- Select Level --</option>
                    {availableLevels.map((level) => (
                      <option key={level.id} value={level.id}>
                        {level.level_name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              {/* For Modular - Select Modules */}
              {filters.registration_category === 'modular' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Modules (for Modular candidates)
                  </label>
                  <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-lg p-2 space-y-2">
                    {availableModules.map((module) => (
                      <label key={module.id} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedModules.includes(module.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedModules([...selectedModules, module.id]);
                            } else {
                              setSelectedModules(selectedModules.filter(id => id !== module.id));
                            }
                          }}
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm text-gray-700">
                          {module.module_code} - {module.module_name}
                        </span>
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Selected: {selectedModules.length} module(s)
                  </p>
                </div>
              )}
              
              {/* For Worker's PAS - Select Papers */}
              {filters.registration_category === 'workers_pas' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Papers (for Worker's PAS candidates)
                  </label>
                  <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-lg p-2 space-y-2">
                    {availablePapers.map((paper) => (
                      <label key={paper.id} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedPapers.includes(paper.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedPapers([...selectedPapers, paper.id]);
                            } else {
                              setSelectedPapers(selectedPapers.filter(id => id !== paper.id));
                            }
                          }}
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="text-sm text-gray-700">
                          {paper.paper_code} - {paper.paper_name}
                        </span>
                      </label>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Selected: {selectedPapers.length} paper(s)
                  </p>
                </div>
              )}
              
              {/* General message if no category filter */}
              {!filters.registration_category && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-sm text-amber-800">
                    Please filter by Category (Formal/Modular/Worker's PAS) to select appropriate level, modules, or papers.
                  </p>
                </div>
              )}
            </div>
            <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
              <Button
                variant="outline"
                onClick={() => {
                  setShowUpdateEnrollmentModal(false);
                  setSelectedLevel('');
                  setSelectedModules([]);
                  setSelectedPapers([]);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleBulkUpdateEnrollment}
                loading={isProcessing}
                disabled={isProcessing || (!selectedLevel && selectedModules.length === 0 && selectedPapers.length === 0)}
              >
                Update Enrollments
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnrollmentList;
