import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Search, ChevronLeft, ChevronRight, User, Filter, Printer, RefreshCw, X, AlertTriangle, Download, FileText, Archive } from 'lucide-react';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';

const AwardsList = () => {
  const navigate = useNavigate();
  const [awards, setAwards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState(() => {
    return localStorage.getItem('awards_search') || '';
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [selectAllFiltered, setSelectAllFiltered] = useState(false);
  const [printing, setPrinting] = useState(false);
  const [reprinting, setReprinting] = useState(false);
  const [showReprintModal, setShowReprintModal] = useState(false);
  const [reprintReasons, setReprintReasons] = useState([]);
  const [selectedReprintReason, setSelectedReprintReason] = useState('');
  const [showValidationError, setShowValidationError] = useState(false);
  const [uniqueCenters, setUniqueCenters] = useState([]);
  const [uniqueOccupations, setUniqueOccupations] = useState([]);
  const [exporting, setExporting] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [batchAction, setBatchAction] = useState(null); // 'print' or 'zip'
  const [batchSize, setBatchSize] = useState(100);
  const [batchOffset, setBatchOffset] = useState(0);
  const itemsPerPage = 50;
  const MAX_BATCH_SIZE = 300; // Safe limit to avoid timeouts
  const searchTimerRef = useRef(null);

  // Filter states - load from localStorage
  const [filters, setFilters] = useState(() => {
    const saved = localStorage.getItem('awards_filters');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return {
          registration_category: '',
          entry_year: '',
          intake: '',
          center: '',
          printed: '',
          occupation: '',
        };
      }
    }
    return {
      registration_category: '',
      entry_year: '',
      intake: '',
      center: '',
      printed: '',
      occupation: '',
    };
  });

  const buildQueryParams = useCallback((page = 1, overrides = {}) => {
    const params = new URLSearchParams();
    params.set('page', page);
    params.set('page_size', itemsPerPage);
    const search = overrides.search !== undefined ? overrides.search : searchQuery;
    if (search) params.set('search', search);
    const f = overrides.filters || filters;
    if (f.registration_category) params.set('category', f.registration_category);
    if (f.entry_year) params.set('entry_year', f.entry_year);
    if (f.intake) params.set('intake', f.intake);
    if (f.center) params.set('center', f.center);
    if (f.occupation) params.set('occupation', f.occupation);
    if (f.printed) params.set('printed', f.printed);
    return params.toString();
  }, [searchQuery, filters]);

  const fetchAwards = useCallback(async (page = 1, overrides = {}) => {
    try {
      setLoading(true);
      const qs = buildQueryParams(page, overrides);
      const response = await apiClient.get(`/awards/?${qs}`);
      setAwards(response.data.results || []);
      setTotalCount(response.data.count || 0);
      setTotalPages(response.data.num_pages || 1);
      setCurrentPage(response.data.current_page || page);
      setError(null);
    } catch (err) {
      console.error('Error fetching awards:', err);
      setError('Failed to load awards data');
    } finally {
      setLoading(false);
    }
  }, [buildQueryParams]);

  const fetchFilterOptions = async () => {
    try {
      const response = await apiClient.get('/awards/filter-options/');
      setUniqueCenters(response.data.centers || []);
      setUniqueOccupations(response.data.occupations || []);
    } catch (err) {
      console.error('Error fetching filter options:', err);
    }
  };

  useEffect(() => {
    fetchAwards(1);
    fetchFilterOptions();
    fetchReprintReasons();
  }, []);

  const fetchReprintReasons = async () => {
    try {
      const response = await apiClient.get('/configurations/reprint-reasons/');
      const data = response.data.results || response.data;
      setReprintReasons(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching reprint reasons:', err);
      setReprintReasons([]);
    }
  };

  // Debounced search
  const handleSearchChange = (value) => {
    setSearchQuery(value);
    localStorage.setItem('awards_search', value);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setCurrentPage(1);
      setSelectedCandidates([]);
      setSelectAllFiltered(false);
      fetchAwards(1, { search: value });
    }, 400);
  };

  // Apply filters
  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    localStorage.setItem('awards_filters', JSON.stringify(newFilters));
    setCurrentPage(1);
    setSelectedCandidates([]);
    setSelectAllFiltered(false);
    fetchAwards(1, { filters: newFilters });
  };

  // Clear filters
  const handleClearFilters = () => {
    const empty = {
      registration_category: '',
      entry_year: '',
      intake: '',
      center: '',
      printed: '',
      occupation: '',
    };
    setFilters(empty);
    setSearchQuery('');
    localStorage.removeItem('awards_filters');
    localStorage.removeItem('awards_search');
    setCurrentPage(1);
    setSelectedCandidates([]);
    setSelectAllFiltered(false);
    fetchAwards(1, { search: '', filters: empty });
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    setSelectedCandidates([]);
    fetchAwards(page);
  };

  const startIndex = (currentPage - 1) * itemsPerPage;

  // Selection handlers
  const handleSelectAll = () => {
    if (selectedCandidates.length === awards.length && !selectAllFiltered) {
      setSelectedCandidates([]);
      setSelectAllFiltered(false);
    } else {
      setSelectedCandidates(awards.map((a) => a.id));
    }
  };

  const handleSelectAllFiltered = () => {
    setSelectAllFiltered(true);
    setSelectedCandidates(awards.map((a) => a.id));
  };

  const handleClearSelection = () => {
    setSelectedCandidates([]);
    setSelectAllFiltered(false);
  };

  const handleSelectCandidate = (id, e) => {
    e.stopPropagation();
    setSelectAllFiltered(false);
    if (selectedCandidates.includes(id)) {
      setSelectedCandidates(selectedCandidates.filter((cId) => cId !== id));
    } else {
      setSelectedCandidates([...selectedCandidates, id]);
    }
  };

  // Export to Excel handler
  const handleExportExcel = async (exportType) => {
    try {
      setExporting(true);
      let dataToExport = [];

      if (exportType === 'selected' && !selectAllFiltered) {
        dataToExport = awards.filter((a) => selectedCandidates.includes(a.id));
      } else {
        // Fetch all matching records for export
        const qs = buildQueryParams(1);
        const params = new URLSearchParams(qs);
        params.set('page_size', '0');
        const response = await apiClient.get(`/awards/?${params.toString()}`);
        dataToExport = response.data.results || [];
      }

      if (dataToExport.length === 0) {
        toast.error('No data to export');
        return;
      }

      const exportData = dataToExport.map((award, index) => ({
        '#': index + 1,
        'Reg No': award.registration_number || '',
        'Full Name': award.full_name || '',
        'Center': award.center_name || '',
        'Reg Category': award.registration_category || '',
        'Occupation': award.occupation_name || '',
        'Entry Year': award.entry_year || '',
        'Assessment Intake': award.assessment_intake || '',
        'Award': award.award || '',
        'Completion Date': award.completion_date || '',
        'Printed': award.printed ? 'Yes' : 'No',
        'TR SNo': award.tr_sno || '',
      }));

      const worksheet = XLSX.utils.json_to_sheet(exportData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Awards');

      const colWidths = Object.keys(exportData[0]).map((key) => ({
        wch: Math.max(key.length, ...exportData.map((row) => String(row[key]).length)) + 2,
      }));
      worksheet['!cols'] = colWidths;

      const filename = exportType === 'selected'
        ? `Awards_Selected_${dataToExport.length}_${new Date().toISOString().slice(0, 10)}.xlsx`
        : `Awards_All_${dataToExport.length}_${new Date().toISOString().slice(0, 10)}.xlsx`;

      XLSX.writeFile(workbook, filename);
      toast.success(`Exported ${dataToExport.length} record(s) to Excel`);
    } catch (err) {
      console.error('Export error:', err);
      toast.error('Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  // Check if batch modal needed and show it
  const handlePrintClick = () => {
    const count = selectAllFiltered ? totalCount : selectedCandidates.length;
    if (count > MAX_BATCH_SIZE) {
      setBatchAction('print');
      setBatchOffset(0);
      setShowBatchModal(true);
    } else {
      handlePrintTranscripts(0, count);
    }
  };

  const handleZipClick = () => {
    const count = selectAllFiltered ? totalCount : selectedCandidates.length;
    if (count > MAX_BATCH_SIZE) {
      setBatchAction('zip');
      setBatchOffset(0);
      setShowBatchModal(true);
    } else {
      handleDownloadZip(false, 0, count);
    }
  };

  // Execute batch action
  const executeBatchAction = () => {
    setShowBatchModal(false);
    if (batchAction === 'print') {
      handlePrintTranscripts(batchOffset, batchSize);
    } else if (batchAction === 'zip') {
      handleDownloadZip(false, batchOffset, batchSize);
    }
  };

  // Print transcripts handler
  const handlePrintTranscripts = async (offset = 0, limit = null) => {
    // For non-select-all, check locally if any are already printed
    if (!selectAllFiltered) {
      const selectedAwards = awards.filter((a) => selectedCandidates.includes(a.id));
      const alreadyPrinted = selectedAwards.filter((a) => a.printed);
      if (alreadyPrinted.length > 0) {
        setShowValidationError(true);
        return;
      }
    }

    try {
      setPrinting(true);

      const requestData = {};

      if (selectAllFiltered) {
        requestData.select_all = true;
        requestData.filters = {
          search: searchQuery,
          category: filters.registration_category,
          entry_year: filters.entry_year,
          intake: filters.intake,
          center: filters.center,
          occupation: filters.occupation,
          printed: filters.printed,
        };
        if (limit) {
          requestData.limit = limit;
          requestData.offset = offset;
        }
      } else {
        requestData.candidate_ids = selectedCandidates;
      }

      const response = await apiClient.post('/awards/bulk-print-transcripts/', requestData, {
        responseType: 'blob',
        timeout: 600000, // 10 minute timeout for large batches
      });

      // Create download link for PDF
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const batchLabel = limit ? `_batch${Math.floor(offset / limit) + 1}` : '';
      link.download = `Transcripts${batchLabel}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      const count = limit || (selectAllFiltered ? totalCount : selectedCandidates.length);
      toast.success(`Generated transcripts for ${count} candidate(s) (offset ${offset})`);
      
      // Update offset for next batch
      if (limit) {
        setBatchOffset(offset + limit);
      }
      
      fetchAwards(currentPage); // Refresh to update printed status
    } catch (err) {
      console.error('Error printing transcripts:', err);
      if (err.response?.data) {
        try {
          const text = await err.response.data.text();
          const errorData = JSON.parse(text);
          toast.error(errorData.error || 'Failed to generate transcripts');
        } catch {
          toast.error('Failed to generate transcripts');
        }
      } else {
        toast.error('Failed to generate transcripts');
      }
    } finally {
      setPrinting(false);
    }
  };

  // Download transcripts as ZIP handler
  const handleDownloadZip = async (isReprint = false, offset = 0, limit = null) => {
    if (isReprint && !selectedReprintReason) {
      toast.error('Please select a reprint reason');
      return;
    }

    try {
      setDownloadingZip(true);
      
      const requestData = {
        is_reprint: isReprint,
      };

      if (selectAllFiltered) {
        requestData.select_all = true;
        requestData.filters = {
          search: searchQuery,
          category: filters.registration_category,
          entry_year: filters.entry_year,
          intake: filters.intake,
          center: filters.center,
          occupation: filters.occupation,
          printed: filters.printed,
        };
        if (limit) {
          requestData.limit = limit;
          requestData.offset = offset;
        }
      } else {
        requestData.candidate_ids = selectedCandidates;
      }

      if (isReprint) {
        requestData.reason_id = selectedReprintReason;
      }

      const response = await apiClient.post('/awards/bulk-transcripts-zip/', requestData, {
        responseType: 'blob',
        timeout: 600000, // 10 minute timeout for large batches
      });

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'Transcripts.zip';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) filename = match[1];
      }
      
      // Add batch number to filename if batching
      if (limit) {
        const batchNum = Math.floor(offset / limit) + 1;
        filename = filename.replace('.zip', `_batch${batchNum}.zip`);
      }

      // Create download link
      const blob = new Blob([response.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      const count = limit || (selectAllFiltered ? totalCount : selectedCandidates.length);
      toast.success(`Downloaded ${count} transcript(s) as ZIP (batch starting at ${offset})`);
      
      // Update offset for next batch
      if (limit) {
        setBatchOffset(offset + limit);
      }
      
      if (isReprint) {
        setShowReprintModal(false);
        setSelectedReprintReason('');
      }
      fetchAwards(currentPage);
    } catch (err) {
      console.error('Error downloading transcripts:', err);
      if (err.response?.data) {
        // Try to parse error from blob
        try {
          const text = await err.response.data.text();
          const errorData = JSON.parse(text);
          toast.error(errorData.error || 'Failed to download transcripts');
        } catch {
          toast.error('Failed to download transcripts');
        }
      } else {
        toast.error('Failed to download transcripts');
      }
    } finally {
      setDownloadingZip(false);
    }
  };

  // Reprint transcripts handler
  const handleReprintTranscripts = async () => {
    if (!selectedReprintReason) {
      toast.error('Please select a reprint reason');
      return;
    }

    const ids = selectAllFiltered
      ? awards.map((a) => a.id)
      : selectedCandidates;

    try {
      setReprinting(true);

      const response = await apiClient.post('/awards/reprint-transcripts/',
        { candidate_ids: ids, reason_id: selectedReprintReason },
        { responseType: 'blob' }
      );

      // Create download link for PDF
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'Reprinted_Transcripts.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success(`Reprinted transcripts for ${ids.length} candidate(s)`);
      setShowReprintModal(false);
      setSelectedReprintReason('');
      handleClearSelection();
    } catch (err) {
      console.error('Error reprinting transcripts:', err);
      if (err.response?.data?.error) {
        toast.error(err.response.data.error);
      } else {
        toast.error('Failed to reprint transcripts');
      }
    } finally {
      setReprinting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-600 p-4 rounded-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-amber-100 rounded-lg">
            <Award className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Awards</h1>
            <p className="text-sm text-gray-500">
              Candidates who have successfully completed their assessments
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/awards/transcript-logs')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
          >
            <FileText className="w-4 h-4 mr-2" />
            Transcript Logs
          </button>
          <button
            onClick={() => handleExportExcel('all')}
            className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export All ({totalCount})
          </button>
          <div className="text-sm text-gray-500">
            Total: <span className="font-semibold text-gray-900">{totalCount}</span> candidates
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="space-y-4">
          {/* Search Bar */}
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, reg no, center, occupation..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center px-4 py-2 rounded-lg border ${showFilters ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 pt-4 border-t">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category
                </label>
                <select
                  value={filters.registration_category}
                  onChange={(e) => handleFilterChange({ ...filters, registration_category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  onChange={(e) => handleFilterChange({ ...filters, entry_year: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 2025"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Intake
                </label>
                <select
                  value={filters.intake}
                  onChange={(e) => handleFilterChange({ ...filters, intake: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="M">March</option>
                  <option value="J">June</option>
                  <option value="A">August</option>
                  <option value="S">September</option>
                  <option value="D">December</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Center
                </label>
                <select
                  value={filters.center}
                  onChange={(e) => handleFilterChange({ ...filters, center: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {uniqueCenters.map((center) => (
                    <option key={center} value={center}>{center}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Occupation
                </label>
                <select
                  value={filters.occupation}
                  onChange={(e) => handleFilterChange({ ...filters, occupation: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {uniqueOccupations.map((occ) => (
                    <option key={occ} value={occ}>{occ}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Printed
                </label>
                <select
                  value={filters.printed}
                  onChange={(e) => handleFilterChange({ ...filters, printed: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleClearFilters}
                  className="w-full px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {(selectedCandidates.length > 0 || selectAllFiltered) && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-blue-900">
                {selectAllFiltered ? (
                  <>All {totalCount} candidates selected</>
                ) : (
                  <>{selectedCandidates.length} candidate(s) selected</>
                )}
              </span>
              {selectedCandidates.length === awards.length && !selectAllFiltered && totalCount > itemsPerPage && (
                <button
                  onClick={handleSelectAllFiltered}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Select all {totalCount} candidates
                </button>
              )}
              {(selectedCandidates.length > 0 || selectAllFiltered) && (
                <button
                  onClick={handleClearSelection}
                  className="text-sm text-gray-600 hover:text-gray-800 underline"
                >
                  Clear selection
                </button>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handlePrintClick}
                disabled={printing}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Printer className="w-4 h-4 mr-2" />
                {printing ? 'Printing...' : 'Print Transcripts'}
              </button>
              <button
                onClick={handleZipClick}
                disabled={downloadingZip}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Archive className="w-4 h-4 mr-2" />
                {downloadingZip ? 'Generating ZIP...' : 'Download ZIP'}
              </button>
              <button
                onClick={() => setShowReprintModal(true)}
                disabled={reprinting || downloadingZip}
                className="flex items-center px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reprint Transcript
              </button>
              <button
                onClick={() => handleExportExcel('selected')}
                className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                <Download className="w-4 h-4 mr-2" />
                Export Selected
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={awards.length > 0 && selectedCandidates.length === awards.length}
                    onChange={handleSelectAll}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
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
                  Reg Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occupation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry Year
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Intake
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Award
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completion Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Printed
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  TR SNo
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {awards.length === 0 ? (
                <tr>
                  <td colSpan="13" className="px-4 py-8 text-center text-gray-500">
                    No candidates found
                  </td>
                </tr>
              ) : (
                awards.map((award) => (
                  <tr
                    key={award.id}
                    className={`hover:bg-gray-50 cursor-pointer ${selectedCandidates.includes(award.id) ? 'bg-blue-50' : ''}`}
                    onClick={() => navigate(`/candidates/${award.id}`, { state: { from: 'awards' } })}
                  >
                    <td className="px-4 py-3 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedCandidates.includes(award.id)}
                        onChange={(e) => handleSelectCandidate(award.id, e)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {award.passport_photo ? (
                        <img
                          src={award.passport_photo}
                          alt={award.full_name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <User className="w-5 h-5 text-gray-400" />
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600">
                      {award.registration_number || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {award.full_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.center_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${award.registration_category === 'Modular'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-green-100 text-green-700'
                        }`}>
                        {award.registration_category || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.occupation_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.entry_year || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.assessment_intake || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate" title={award.award}>
                      {award.award || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.completion_date || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${award.printed
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                        }`}>
                        {award.printed ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.tr_sno || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, totalCount)} of {totalCount} results
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                <ChevronLeft className="w-4 h-4" />
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
                    onClick={() => handlePageChange(pageNum)}
                    className={`px-3 py-1 rounded-lg ${currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-100'
                      }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Validation Error Modal */}
      {showValidationError && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShowValidationError(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-red-800">Validation Error</h3>
            </div>
            <p className="text-gray-700 mb-2">
              All selected candidate(s) already have printed transcripts.
            </p>
            <p className="text-gray-600 text-sm mb-6">
              Only reprints are allowed through the reprint process.
            </p>
            <button
              onClick={() => setShowValidationError(false)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              OK
            </button>
          </div>
        </div>
      )}

      {/* Reprint Reason Modal */}
      {showReprintModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => {
              setShowReprintModal(false);
              setSelectedReprintReason('');
            }}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Reprint Transcript</h3>
              <button
                onClick={() => {
                  setShowReprintModal(false);
                  setSelectedReprintReason('');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reprint Reason
              </label>
              <select
                value={selectedReprintReason}
                onChange={(e) => setSelectedReprintReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">-- Select Reason --</option>
                {reprintReasons.map((reason) => (
                  <option key={reason.id} value={reason.id}>
                    {reason.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowReprintModal(false);
                  setSelectedReprintReason('');
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleReprintTranscripts}
                disabled={reprinting || !selectedReprintReason}
                className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {reprinting ? 'Reprinting...' : 'Reprint'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Size Modal */}
      {showBatchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShowBatchModal(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {batchAction === 'print' ? 'Print Transcripts' : 'Download ZIP'} - Batch Processing
              </h3>
              <button
                onClick={() => setShowBatchModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800">
                <strong>Note:</strong> You have selected {totalCount} candidates. 
                Processing more than {MAX_BATCH_SIZE} at once may timeout. 
                Please process in batches.
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Batch Size
              </label>
              <select
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={50}>50 candidates</option>
                <option value={100}>100 candidates</option>
                <option value={200}>200 candidates</option>
                <option value={300}>300 candidates (max recommended)</option>
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Starting Position (Offset)
              </label>
              <input
                type="number"
                value={batchOffset}
                onChange={(e) => setBatchOffset(Number(e.target.value))}
                min={0}
                max={totalCount - 1}
                step={batchSize}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Processing candidates {batchOffset + 1} to {Math.min(batchOffset + batchSize, totalCount)} of {totalCount}
              </p>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowBatchModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={executeBatchAction}
                disabled={printing || downloadingZip}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {batchAction === 'print' ? 'Print Batch' : 'Download Batch'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AwardsList;
