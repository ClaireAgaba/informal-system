import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Search, ChevronLeft, ChevronRight, User, Filter, ArrowLeft, Download, X, Edit2 } from 'lucide-react';
import * as XLSX from 'xlsx';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';

const TranscriptLogs = () => {
  const navigate = useNavigate();
  const [awards, setAwards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [selectedAward, setSelectedAward] = useState(null);
  const [collectionForm, setCollectionForm] = useState({
    collected: false,
    collector_name: '',
    collector_phone: '',
    collection_date: '',
  });
  const [saving, setSaving] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [selectAllFiltered, setSelectAllFiltered] = useState(false);
  const itemsPerPage = 20;

  // Filter states
  const [filters, setFilters] = useState({
    center: '',
    collection_status: '',
  });

  // Get unique centers for filter dropdown
  const uniqueCenters = [...new Set(awards.map((a) => a.center_name).filter(Boolean))].sort();

  useEffect(() => {
    fetchPrintedAwards();
  }, []);

  const fetchPrintedAwards = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/awards/');
      const data = response.data.results || response.data;
      // Only keep candidates whose transcripts have been printed
      const printedOnly = (Array.isArray(data) ? data : []).filter((a) => a.printed);
      setAwards(printedOnly);
      setError(null);
    } catch (err) {
      console.error('Error fetching awards:', err);
      setError('Failed to load transcript logs');
    } finally {
      setLoading(false);
    }
  };

  // Clear filters
  const handleClearFilters = () => {
    setFilters({
      center: '',
      collection_status: '',
    });
    setSearchQuery('');
    setCurrentPage(1);
  };

  // Open collection modal
  const handleOpenCollectionModal = (award, e) => {
    e.stopPropagation();
    setSelectedAward(award);
    setCollectionForm({
      collected: award.transcript_collected || false,
      collector_name: award.transcript_collector_name || '',
      collector_phone: award.transcript_collector_phone || '',
      collection_date: award.transcript_collection_date || '',
    });
    setShowCollectionModal(true);
  };

  // Save collection status
  const handleSaveCollection = async () => {
    if (collectionForm.collected && !collectionForm.collector_name) {
      toast.error('Collector name is required');
      return;
    }
    try {
      setSaving(true);
      await apiClient.post('/awards/update-collection-status/', {
        candidate_id: selectedAward.id,
        collected: collectionForm.collected,
        collector_name: collectionForm.collector_name,
        collector_phone: collectionForm.collector_phone,
        collection_date: collectionForm.collection_date || null,
      });
      toast.success('Collection status updated');
      setShowCollectionModal(false);
      fetchPrintedAwards();
    } catch (err) {
      console.error('Error updating collection status:', err);
      toast.error(err.response?.data?.error || 'Failed to update collection status');
    } finally {
      setSaving(false);
    }
  };

  // Filter awards based on search and filters
  const filteredAwards = awards.filter((award) => {
    const searchLower = searchQuery.toLowerCase();

    const matchesSearch = !searchQuery || (
      award.full_name?.toLowerCase().includes(searchLower) ||
      award.registration_number?.toLowerCase().includes(searchLower) ||
      award.center_name?.toLowerCase().includes(searchLower) ||
      award.tr_sno?.toLowerCase().includes(searchLower) ||
      award.transcript_collector_name?.toLowerCase().includes(searchLower)
    );

    const matchesCenter = !filters.center ||
      award.center_name === filters.center;

    const matchesCollection = !filters.collection_status ||
      (filters.collection_status === 'taken' && award.transcript_collected) ||
      (filters.collection_status === 'not_taken' && !award.transcript_collected);

    return matchesSearch && matchesCenter && matchesCollection;
  });

  // Pagination
  const totalPages = Math.ceil(filteredAwards.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedAwards = filteredAwards.slice(startIndex, startIndex + itemsPerPage);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // Selection handlers
  const handleSelectAll = () => {
    if (selectedCandidates.length === paginatedAwards.length && !selectAllFiltered) {
      setSelectedCandidates([]);
      setSelectAllFiltered(false);
    } else {
      setSelectedCandidates(paginatedAwards.map((a) => a.id));
    }
  };

  const handleSelectAllFiltered = () => {
    setSelectAllFiltered(true);
    setSelectedCandidates(paginatedAwards.map((a) => a.id));
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
  const handleExportExcel = (exportType) => {
    let dataToExport = [];

    if (exportType === 'selected') {
      const ids = selectAllFiltered
        ? filteredAwards.map((a) => a.id)
        : selectedCandidates;
      dataToExport = filteredAwards.filter((a) => ids.includes(a.id));
    } else {
      dataToExport = filteredAwards;
    }

    if (dataToExport.length === 0) {
      toast.error('No data to export');
      return;
    }

    const exportData = dataToExport.map((award, index) => ({
      '#': index + 1,
      'Reg No': award.registration_number || '',
      'Name': award.full_name || '',
      'Center': award.center_name || '',
      'TR SNo': award.tr_sno || '',
      'Collection Status': award.transcript_collected ? 'Taken' : 'Not Taken',
      'Collector Name': award.transcript_collector_name || '',
      'Collector No': award.transcript_collector_phone || '',
      'Collection Date': award.transcript_collection_date || '',
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Transcript Logs');

    const colWidths = Object.keys(exportData[0]).map((key) => ({
      wch: Math.max(key.length, ...exportData.map((row) => String(row[key]).length)) + 2,
    }));
    worksheet['!cols'] = colWidths;

    const filename = exportType === 'selected'
      ? `Transcript_Logs_Selected_${dataToExport.length}_${new Date().toISOString().slice(0, 10)}.xlsx`
      : `Transcript_Logs_All_${dataToExport.length}_${new Date().toISOString().slice(0, 10)}.xlsx`;
    XLSX.writeFile(workbook, filename);
    toast.success(`Exported ${dataToExport.length} record(s) to Excel`);
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
          <button
            onClick={() => navigate('/awards')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="p-2 bg-blue-100 rounded-lg">
            <FileText className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transcript Logs</h1>
            <p className="text-sm text-gray-500">
              Candidates whose transcripts have been printed
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleExportExcel('all')}
            className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export All ({filteredAwards.length})
          </button>
          <div className="text-sm text-gray-500">
            Total: <span className="font-semibold text-gray-900">{filteredAwards.length}</span> printed
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, reg no, center, TR SNo, collector name..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center px-4 py-2 rounded-lg border ${
                showFilters ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Center</label>
                <select
                  value={filters.center}
                  onChange={(e) => {
                    setFilters({ ...filters, center: e.target.value });
                    setCurrentPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {uniqueCenters.map((center) => (
                    <option key={center} value={center}>{center}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Collection Status</label>
                <select
                  value={filters.collection_status}
                  onChange={(e) => {
                    setFilters({ ...filters, collection_status: e.target.value });
                    setCurrentPage(1);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  <option value="taken">Taken</option>
                  <option value="not_taken">Not Taken</option>
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
                  <>All {filteredAwards.length} candidates selected</>
                ) : (
                  <>{selectedCandidates.length} candidate(s) selected</>
                )}
              </span>
              {selectedCandidates.length === paginatedAwards.length && !selectAllFiltered && filteredAwards.length > itemsPerPage && (
                <button
                  onClick={handleSelectAllFiltered}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Select all {filteredAwards.length} candidates
                </button>
              )}
              <button
                onClick={handleClearSelection}
                className="text-sm text-gray-600 hover:text-gray-800 underline"
              >
                Clear selection
              </button>
            </div>
            <button
              onClick={() => handleExportExcel('selected')}
              className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Selected
            </button>
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
                    checked={paginatedAwards.length > 0 && selectedCandidates.length === paginatedAwards.length}
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
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Center
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  TR SNo
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collector Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collector No
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedAwards.length === 0 ? (
                <tr>
                  <td colSpan="11" className="px-4 py-8 text-center text-gray-500">
                    No printed transcripts found
                  </td>
                </tr>
              ) : (
                paginatedAwards.map((award) => (
                  <tr
                    key={award.id}
                    className={`hover:bg-gray-50 ${selectedCandidates.includes(award.id) ? 'bg-blue-50' : ''}`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
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
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.tr_sno || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        award.transcript_collected
                          ? 'bg-green-100 text-green-700'
                          : 'bg-orange-100 text-orange-700'
                      }`}>
                        {award.transcript_collected ? 'Taken' : 'Not Taken'}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.transcript_collector_name || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.transcript_collector_phone || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {award.transcript_collection_date || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <button
                        onClick={(e) => handleOpenCollectionModal(award, e)}
                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="Update collection status"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
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
              Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredAwards.length)} of {filteredAwards.length} results
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
                    className={`px-3 py-1 rounded-lg ${
                      currentPage === pageNum
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

      {/* Collection Status Modal */}
      {showCollectionModal && selectedAward && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setShowCollectionModal(false)}
          />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Update Collection Status</h3>
              <button
                onClick={() => setShowCollectionModal(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">{selectedAward.full_name}</span> — {selectedAward.registration_number}
              </p>
              <p className="text-xs text-gray-500">TR SNo: {selectedAward.tr_sno}</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Collection Status</label>
                <select
                  value={collectionForm.collected ? 'taken' : 'not_taken'}
                  onChange={(e) => {
                    const isTaken = e.target.value === 'taken';
                    setCollectionForm({
                      ...collectionForm,
                      collected: isTaken,
                      collector_name: isTaken ? collectionForm.collector_name : '',
                      collector_phone: isTaken ? collectionForm.collector_phone : '',
                      collection_date: isTaken ? collectionForm.collection_date : '',
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="not_taken">Not Taken</option>
                  <option value="taken">Taken</option>
                </select>
              </div>

              {collectionForm.collected && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Collector Name *</label>
                    <input
                      type="text"
                      value={collectionForm.collector_name}
                      onChange={(e) => setCollectionForm({ ...collectionForm, collector_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Name of person collecting"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Collector Phone No</label>
                    <input
                      type="text"
                      value={collectionForm.collector_phone}
                      onChange={(e) => setCollectionForm({ ...collectionForm, collector_phone: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g. 0700000000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Collection Date</label>
                    <input
                      type="date"
                      value={collectionForm.collection_date}
                      onChange={(e) => setCollectionForm({ ...collectionForm, collection_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCollectionModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCollection}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptLogs;
