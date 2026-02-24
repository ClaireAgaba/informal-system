import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
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
  ClipboardList,
  ExternalLink,
} from 'lucide-react';
import candidateApi from '../services/candidateApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';
import { INTAKE_LABELS } from '@shared/constants';
import BulkEnrollModal from '../components/BulkEnrollModal';
import BulkChangeOccupationModal from '../components/BulkChangeOccupationModal';
import BulkChangeRegCategoryModal from '../components/BulkChangeRegCategoryModal';
import BulkChangeSeriesModal from '../components/BulkChangeSeriesModal';
import BulkChangeCenterModal from '../components/BulkChangeCenterModal';

const FILTER_KEYS = [
  'registration_category', 'assessment_center', 'assessment_center_branch',
  'occupation', 'sector', 'has_disability', 'is_refugee',
  'verification_status', 'is_enrolled', 'has_marks', 'entry_year', 'intake',
];

const CandidateList = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();

  // Initialize state from URL params
  const initFilters = () => {
    const f = {};
    FILTER_KEYS.forEach((k) => { f[k] = searchParams.get(k) || ''; });
    return f;
  };

  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [currentPage, setCurrentPage] = useState(Number(searchParams.get('page')) || 1);
  const [pageSize, setPageSize] = useState(Number(searchParams.get('page_size')) || 20);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [selectAllPages, setSelectAllPages] = useState(false);
  const [showFilters, setShowFilters] = useState(() => FILTER_KEYS.some((k) => searchParams.get(k)));
  const [exporting, setExporting] = useState(false);
  const [deEnrolling, setDeEnrolling] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [showBulkEnrollModal, setShowBulkEnrollModal] = useState(false);
  const [showBulkChangeOccupationModal, setShowBulkChangeOccupationModal] = useState(false);
  const [changingOccupation, setChangingOccupation] = useState(false);
  const [showBulkChangeRegCategoryModal, setShowBulkChangeRegCategoryModal] = useState(false);
  const [changingRegCategory, setChangingRegCategory] = useState(false);
  const [showBulkChangeSeriesModal, setShowBulkChangeSeriesModal] = useState(false);
  const [changingSeries, setChangingSeries] = useState(false);
  const [showBulkChangeCenterModal, setShowBulkChangeCenterModal] = useState(false);
  const [changingCenter, setChangingCenter] = useState(false);
  const [regeneratingRegNo, setRegeneratingRegNo] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // Load current user from localStorage
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        setCurrentUser(JSON.parse(userStr));
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  // Filter states — initialized from URL
  const [filters, setFilters] = useState(initFilters);

  // Sync filters from URL params on navigation (e.g., from center details "View All")
  useEffect(() => {
    const newFilters = {};
    let hasChanges = false;
    FILTER_KEYS.forEach((k) => {
      const urlValue = searchParams.get(k) || '';
      newFilters[k] = urlValue;
      if (urlValue !== filters[k]) hasChanges = true;
    });
    if (hasChanges) {
      setFilters(newFilters);
      if (FILTER_KEYS.some((k) => searchParams.get(k))) {
        setShowFilters(true);
      }
    }
  }, [searchParams]);

  // Sync state → URL params
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (currentPage > 1) params.set('page', String(currentPage));
    if (pageSize !== 20) params.set('page_size', String(pageSize));
    FILTER_KEYS.forEach((k) => {
      if (filters[k]) params.set(k, filters[k]);
    });
    setSearchParams(params, { replace: true });
  }, [searchQuery, currentPage, pageSize, filters]);

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

  // Fetch branches for selected center
  const { data: branchesData } = useQuery({
    queryKey: ['branches-filter', filters.assessment_center],
    queryFn: () => assessmentCenterApi.branches.getByCenter(filters.assessment_center),
    enabled: !!filters.assessment_center,
  });

  const centers = centersData?.data?.results || centersData?.data || [];
  const branches = branchesData?.data?.results || branchesData?.data || [];
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
      link.download = `candidates_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
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

  // Handle bulk enroll
  const handleBulkEnroll = () => {
    console.log('handleBulkEnroll called, selectedCandidates:', selectedCandidates);
    if (selectedCandidates.length === 0) {
      alert('Please select candidates to enroll');
      return;
    }
    console.log('Setting showBulkEnrollModal to true');
    setShowBulkEnrollModal(true);
  };

  // Handle bulk de-enroll
  const handleBulkDeEnroll = async () => {
    if (selectedCandidates.length === 0) {
      alert('Please select candidates to de-enroll');
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to de-enroll ${selectedCandidates.length} candidate(s)? This will remove their enrollments and reset fees. Candidates with marks cannot be de-enrolled.`
    );

    if (!confirmed) return;

    try {
      setDeEnrolling(true);
      const response = await candidateApi.bulkDeEnroll(selectedCandidates);
      const { success_count, skipped_with_marks, failed } = response.data;

      // Show results
      if (success_count > 0) {
        toast.success(`Successfully de-enrolled ${success_count} candidate(s)`);
      }

      if (skipped_with_marks?.length > 0) {
        toast.error(
          `${skipped_with_marks.length} candidate(s) skipped - they have marks`,
          { duration: 5000 }
        );
      }

      if (failed?.length > 0) {
        toast.error(`${failed.length} candidate(s) failed to de-enroll`);
      }

      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
    } catch (error) {
      console.error('Bulk de-enroll failed:', error);
      toast.error(error.response?.data?.error || 'Failed to de-enroll candidates');
    } finally {
      setDeEnrolling(false);
    }
  };

  // Handle bulk clear data (results, enrollments, fees)
  const handleBulkClearData = async () => {
    if (selectedCandidates.length === 0) {
      alert('Please select candidates to clear data');
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to clear ALL results, enrollments, and fees for ${selectedCandidates.length} candidate(s)? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      setClearing(true);
      const response = await candidateApi.bulkClearData(selectedCandidates);
      const { cleared } = response.data;

      const totalResults = cleared.modular_results + cleared.formal_results + cleared.workers_pas_results;
      toast.success(
        `Cleared ${totalResults} results and ${cleared.enrollments} enrollments for ${cleared.candidates_processed} candidate(s)`
      );

      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
    } catch (error) {
      console.error('Bulk clear data failed:', error);
      toast.error(error.response?.data?.error || 'Failed to clear data');
    } finally {
      setClearing(false);
    }
  };

  // Handle bulk change occupation
  const handleBulkChangeOccupation = () => {
    if (selectedCandidates.length === 0) {
      toast.error('Please select candidates to change occupation');
      return;
    }
    setShowBulkChangeOccupationModal(true);
  };

  // Process bulk change occupation
  const processBulkChangeOccupation = async (newOccupationId) => {
    try {
      setChangingOccupation(true);
      const response = await candidateApi.bulkChangeOccupation(selectedCandidates, newOccupationId);
      const { successful, failed, failed_details } = response.data;

      if (successful > 0) {
        toast.success(`Changed occupation for ${successful} candidate(s)`);
      }

      if (failed > 0) {
        const reasons = failed_details.slice(0, 3).map(f => `${f.name}: ${f.reason}`).join('\n');
        toast.error(`Failed for ${failed} candidate(s):\n${reasons}${failed > 3 ? `\n...and ${failed - 3} more` : ''}`);
      }

      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
      setShowBulkChangeOccupationModal(false);
    } catch (error) {
      console.error('Bulk change occupation failed:', error);
      toast.error(error.response?.data?.error || 'Failed to change occupation');
    } finally {
      setChangingOccupation(false);
    }
  };

  // Handle bulk change registration category
  const handleBulkChangeRegCategory = () => {
    if (selectedCandidates.length === 0) {
      toast.error('Please select candidates to change registration category');
      return;
    }
    setShowBulkChangeRegCategoryModal(true);
  };

  // Process bulk change registration category
  const processBulkChangeRegCategory = async (newRegCategory) => {
    try {
      setChangingRegCategory(true);
      const response = await candidateApi.bulkChangeRegistrationCategory(selectedCandidates, newRegCategory);
      const { successful, failed, failed_details } = response.data;

      if (successful > 0) {
        toast.success(`Changed registration category for ${successful} candidate(s)`);
      }

      if (failed > 0) {
        const reasons = failed_details.slice(0, 3).map(f => `${f.name}: ${f.reason}`).join('\n');
        toast.error(`Failed for ${failed} candidate(s):\n${reasons}${failed > 3 ? `\n...and ${failed - 3} more` : ''}`);
      }

      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
      setShowBulkChangeRegCategoryModal(false);
    } catch (error) {
      console.error('Bulk change registration category failed:', error);
      toast.error(error.response?.data?.error || 'Failed to change registration category');
    } finally {
      setChangingRegCategory(false);
    }
  };

  // Handle bulk change series
  const handleBulkChangeSeries = () => {
    if (selectedCandidates.length === 0) {
      toast.error('Please select candidates to change assessment series');
      return;
    }
    setShowBulkChangeSeriesModal(true);
  };

  // Process bulk change series
  const processBulkChangeSeries = async (newSeriesId) => {
    try {
      setChangingSeries(true);
      const response = await candidateApi.bulkChangeSeries(selectedCandidates, newSeriesId);
      const { updated } = response.data;

      toast.success(
        `Moved ${updated.candidates} candidate(s): ${updated.enrollments} enrollments, ${updated.modular_results + updated.formal_results + updated.workers_pas_results} results updated`
      );

      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
      setShowBulkChangeSeriesModal(false);
    } catch (error) {
      console.error('Bulk change series failed:', error);
      toast.error(error.response?.data?.error || 'Failed to change assessment series');
    } finally {
      setChangingSeries(false);
    }
  };

  // Handle bulk change center
  const handleBulkChangeCenter = () => {
    if (selectedCandidates.length === 0) {
      toast.error('Please select candidates to change assessment center');
      return;
    }
    setShowBulkChangeCenterModal(true);
  };

  // Process bulk change center
  const processBulkChangeCenter = async (newCenterId) => {
    try {
      setChangingCenter(true);
      const payload = selectAllPages
        ? { select_all: true, filters: { ...filters, search: searchQuery }, new_center_id: newCenterId }
        : { candidate_ids: selectedCandidates, new_center_id: newCenterId };
      const response = await candidateApi.bulkChangeCenter(payload);
      const { updated } = response.data;

      toast.success(
        `Moved ${updated.candidates} candidate(s) to new center. ${updated.fees_moved} fee record(s) updated.`
      );

      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
      setShowBulkChangeCenterModal(false);
    } catch (error) {
      console.error('Bulk change center failed:', error);
      toast.error(error.response?.data?.error || 'Failed to change assessment center');
    } finally {
      setChangingCenter(false);
    }
  };

  // Handle bulk regenerate registration numbers
  const handleBulkRegenerateRegNo = async () => {
    if (selectedCandidates.length === 0 && !selectAllPages) {
      toast.error('Please select candidates to regenerate registration numbers');
      return;
    }
    
    const count = selectAllPages ? totalCount : selectedCandidates.length;
    if (!window.confirm(`Regenerate registration numbers for ${count} candidate(s)?\n\nThis will update registration numbers based on current center, occupation, and other details.\n\nCandidates with no changes needed will be skipped.`)) {
      return;
    }
    
    try {
      setRegeneratingRegNo(true);
      const payload = selectAllPages
        ? { select_all: true, filters: { ...filters, search: searchQuery } }
        : { candidate_ids: selectedCandidates };
      const response = await candidateApi.bulkRegenerateRegNo(payload);
      const { updated, skipped } = response.data;
      
      toast.success(`Regenerated ${updated} registration number(s). ${skipped} skipped (no change needed).`);
      
      // Refresh the list
      queryClient.invalidateQueries(['candidates']);
      setSelectedCandidates([]);
      setSelectAllPages(false);
    } catch (error) {
      console.error('Bulk regenerate regno failed:', error);
      toast.error(error.response?.data?.error || 'Failed to regenerate registration numbers');
    } finally {
      setRegeneratingRegNo(false);
    }
  };

  // Clear filters
  const handleClearFilters = () => {
    setFilters({
      registration_category: '',
      assessment_center: '',
      assessment_center_branch: '',
      occupation: '',
      sector: '',
      has_disability: '',
      is_refugee: '',
      verification_status: '',
      is_enrolled: '',
      has_marks: '',
      entry_year: '',
      intake: '',
    });
    setSearchQuery('');
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Candidates</h1>
          <p className="text-sm text-gray-600">Manage and view all registered candidates</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/candidates/enrollments')}
          >
            <ClipboardList className="w-4 h-4 mr-2" />
            Enrollments
          </Button>
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
                    Entry Year
                  </label>
                  <input
                    type="number"
                    value={filters.entry_year}
                    onChange={(e) => setFilters({ ...filters, entry_year: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g. 2026"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Assessment Intake
                  </label>
                  <select
                    value={filters.intake}
                    onChange={(e) => setFilters({ ...filters, intake: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">All</option>
                    <option value="M">March</option>
                    <option value="J">June</option>
                    <option value="S">September</option>
                    <option value="D">December</option>
                    <option value="A">August</option>
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
                  } else if (e.target.value === 'enroll') {
                    handleBulkEnroll();
                  } else if (e.target.value === 'de-enroll') {
                    handleBulkDeEnroll();
                  } else if (e.target.value === 'clear-data') {
                    handleBulkClearData();
                  } else if (e.target.value === 'change-occupation') {
                    handleBulkChangeOccupation();
                  } else if (e.target.value === 'change-reg-category') {
                    handleBulkChangeRegCategory();
                  } else if (e.target.value === 'change-series') {
                    handleBulkChangeSeries();
                  } else if (e.target.value === 'change-center') {
                    handleBulkChangeCenter();
                  } else if (e.target.value === 'regenerate-regno') {
                    handleBulkRegenerateRegNo();
                  }
                  e.target.value = '';
                }}
                disabled={exporting || deEnrolling || clearing || changingOccupation || changingRegCategory || changingSeries || changingCenter || regeneratingRegNo}
                defaultValue=""
              >
                <option value="" disabled>⚙ Action</option>
                <option value="export">{exporting ? 'Exporting...' : 'Export'}</option>
                <option value="enroll">Enroll</option>
                <option value="de-enroll">{deEnrolling ? 'De-enrolling...' : 'De-enroll'}</option>
                <option value="change-series">{changingSeries ? 'Changing...' : 'Change Assessment Series'}</option>
                {currentUser?.user_type !== 'center_representative' && (
                  <option value="change-center">{changingCenter ? 'Changing...' : 'Change Assessment Center'}</option>
                )}
                <option value="change-occupation">{changingOccupation ? 'Changing...' : 'Change Occupation'}</option>
                <option value="change-reg-category">{changingRegCategory ? 'Changing...' : 'Change Registration Category'}</option>
                <option value="regenerate-regno">{regeneratingRegNo ? 'Regenerating...' : 'Regenerate Reg No'}</option>
                {currentUser?.user_type !== 'center_representative' && (
                  <option value="clear-data">{clearing ? 'Clearing...' : 'Clear Results, Enrollments & Fees'}</option>
                )}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
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
                    onChange={(e) => setFilters({ ...filters, assessment_center: e.target.value, assessment_center_branch: '' })}
                  >
                    <option value="">Select</option>
                    {centers.map((c) => (
                      <option key={c.id} value={c.id}>{c.center_number} - {c.center_name}</option>
                    ))}
                  </select>
                  {filters.assessment_center && branches.length > 0 && (
                    <select
                      className="w-full mt-1 px-2 py-1 text-xs border border-indigo-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-indigo-50"
                      value={filters.assessment_center_branch}
                      onChange={(e) => setFilters({ ...filters, assessment_center_branch: e.target.value })}
                    >
                      <option value="">All Branches</option>
                      {branches.map((b) => (
                        <option key={b.id} value={b.id}>{b.branch_code}</option>
                      ))}
                    </select>
                  )}
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
                  <input
                    type="number"
                    placeholder="Year"
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.entry_year}
                    onChange={(e) => setFilters({ ...filters, entry_year: e.target.value })}
                  />
                </th>
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.intake}
                    onChange={(e) => setFilters({ ...filters, intake: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="M">March</option>
                    <option value="J">June</option>
                    <option value="S">September</option>
                    <option value="D">December</option>
                    <option value="A">August</option>
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
                <th className="px-2 py-2">
                  <select
                    className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                    value={filters.is_enrolled}
                    onChange={(e) => setFilters({ ...filters, is_enrolled: e.target.value })}
                  >
                    <option value="">Select</option>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </th>
                {currentUser?.user_type !== 'center_representative' && (
                  <th className="px-2 py-2">
                    <select
                      className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                      value={filters.has_marks}
                      onChange={(e) => setFilters({ ...filters, has_marks: e.target.value })}
                    >
                      <option value="">Select</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </th>
                )}
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
                  Entry Year
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Intake
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
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Is Enrolled
                </th>
                {currentUser?.user_type !== 'center_representative' && (
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Has Marks
                  </th>
                )}
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="16" className="px-4 py-8 text-center text-gray-500">
                    Loading candidates...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="16" className="px-4 py-8 text-center text-red-500">
                    Error loading candidates: {error.message}
                  </td>
                </tr>
              ) : candidates.length === 0 ? (
                <tr>
                  <td colSpan="16" className="px-4 py-8 text-center text-gray-500">
                    No candidates found
                  </td>
                </tr>
              ) : (
                candidates.map((candidate) => (
                  <tr
                    key={candidate.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/candidates/${candidate.id}`, { state: { fromList: true, filters, searchQuery, currentPage, pageSize } })}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center space-x-2">
                        <button onClick={() => handleSelectCandidate(candidate.id)}>
                          {selectedCandidates.includes(candidate.id) ? (
                            <CheckSquare className="w-5 h-5 text-primary-600" />
                          ) : (
                            <Square className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`/candidates/${candidate.id}`, '_blank');
                          }}
                          className="text-gray-400 hover:text-indigo-600"
                          title="Open in new tab"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
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
                      {candidate.assessment_center?.branch_code && (
                        <span className="ml-1 inline-flex px-1.5 py-0.5 text-xs font-medium rounded bg-indigo-100 text-indigo-700" title={`Branch: ${candidate.assessment_center.branch_code}`}>
                          {candidate.assessment_center.branch_code}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${candidate.registration_category === 'modular'
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
                      {candidate.entry_year || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {candidate.intake ? (INTAKE_LABELS?.[candidate.intake] || candidate.intake) : '-'}
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
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${candidate.verification_status === 'verified'
                        ? 'bg-green-100 text-green-800'
                        : candidate.verification_status === 'declined'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                        }`}>
                        {candidate.verification_status === 'verified' ? 'Verified' :
                          candidate.verification_status === 'declined' ? 'Declined' : 'Pending'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {candidate.is_enrolled ? (
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          Yes
                        </span>
                      ) : (
                        <span className="text-gray-400 text-sm">No</span>
                      )}
                    </td>
                    {currentUser?.user_type !== 'center_representative' && (
                      <td className="px-4 py-3 text-center">
                        {candidate.has_marks ? (
                          <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                            Yes
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">No</span>
                        )}
                      </td>
                    )}
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => navigate(`/candidates/${candidate.id}`, { state: { fromList: true, filters, searchQuery, currentPage, pageSize } })}
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
                          onClick={() => {/* Handle delete */ }}
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

      {/* Bulk Enroll Modal */}
      <BulkEnrollModal
        isOpen={showBulkEnrollModal}
        onClose={() => setShowBulkEnrollModal(false)}
        candidateIds={selectedCandidates}
        filters={filters}
      />

      {/* Bulk Change Occupation Modal */}
      {showBulkChangeOccupationModal && (
        <BulkChangeOccupationModal
          selectedCount={selectedCandidates.length}
          onClose={() => setShowBulkChangeOccupationModal(false)}
          onConfirm={processBulkChangeOccupation}
          isLoading={changingOccupation}
        />
      )}

      {/* Bulk Change Registration Category Modal */}
      {showBulkChangeRegCategoryModal && (
        <BulkChangeRegCategoryModal
          selectedCount={selectedCandidates.length}
          onClose={() => setShowBulkChangeRegCategoryModal(false)}
          onConfirm={processBulkChangeRegCategory}
          isLoading={changingRegCategory}
        />
      )}

      {/* Bulk Change Series Modal */}
      {showBulkChangeSeriesModal && (
        <BulkChangeSeriesModal
          selectedCount={selectedCandidates.length}
          onClose={() => setShowBulkChangeSeriesModal(false)}
          onConfirm={processBulkChangeSeries}
          isLoading={changingSeries}
        />
      )}

      {/* Bulk Change Center Modal */}
      {showBulkChangeCenterModal && (
        <BulkChangeCenterModal
          selectedCount={selectAllPages ? totalCount : selectedCandidates.length}
          onClose={() => setShowBulkChangeCenterModal(false)}
          onConfirm={processBulkChangeCenter}
          isLoading={changingCenter}
        />
      )}
    </div>
  );
};

export default CandidateList;
