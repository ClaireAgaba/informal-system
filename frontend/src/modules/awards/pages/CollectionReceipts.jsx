import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Search, ChevronLeft, ChevronRight, ArrowLeft, Receipt, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';

const CollectionReceipts = () => {
  const navigate = useNavigate();
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [revoking, setRevoking] = useState(null);

  const handleRevoke = async (e, receipt) => {
    e.stopPropagation();
    const confirmed = window.confirm(
      `Are you sure you want to revoke receipt ${receipt.receipt_number}?\n\nThis will delete this collection record and reset ${receipt.candidate_count} candidate(s) back to \"Not Taken\" status.\n\nThis action cannot be undone.`
    );
    if (!confirmed) return;

    setRevoking(receipt.id);
    try {
      const res = await apiClient.delete(`/awards/collection-receipts/${receipt.id}/revoke/`);
      toast.success(res.data.message || 'Receipt revoked successfully');
      fetchReceipts();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to revoke receipt');
    } finally {
      setRevoking(null);
    }
  };

  const fetchReceipts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', currentPage);
      params.append('page_size', 20);
      if (searchQuery) params.append('search', searchQuery);

      const res = await apiClient.get(`/awards/collection-receipts/?${params.toString()}`);
      setReceipts(res.data.results || []);
      setTotalCount(res.data.count || 0);
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      console.error('Error fetching collection receipts:', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchQuery]);

  useEffect(() => {
    fetchReceipts();
  }, [fetchReceipts]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/awards/transcript-logs')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Back to Transcript Logs"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <Receipt className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Collection Receipts</h1>
            <p className="text-sm text-gray-500">
              All transcript collection records
            </p>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          Total: <span className="font-semibold text-gray-900">{totalCount}</span> collections
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search by reference, collector, NIN, center..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Created On</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Reference</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Collector Name</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">NIN</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Center</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Candidates</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-gray-400">Loading...</td>
                </tr>
              ) : receipts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-gray-400">
                    {searchQuery ? 'No receipts match your search' : 'No collection receipts yet'}
                  </td>
                </tr>
              ) : (
                receipts.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => navigate(`/awards/collection-receipts/${r.id}`)}
                    className="border-b border-gray-100 hover:bg-purple-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 text-sm text-gray-600">{formatDate(r.created_at)}</td>
                    <td className="px-4 py-3 text-sm font-medium text-purple-700">{r.receipt_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-800">{r.collector_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 font-mono">{r.nin}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{r.center_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-800 text-center font-semibold">{r.candidate_count}</td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={(e) => handleRevoke(e, r)}
                        disabled={revoking === r.id}
                        className="inline-flex items-center px-2.5 py-1 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded-md hover:bg-red-100 hover:text-red-700 transition-colors disabled:opacity-50"
                        title="Revoke this receipt"
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-1" />
                        {revoking === r.id ? 'Revoking...' : 'Revoke'}
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
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-500">
              Page {currentPage} of {totalPages} ({totalCount} total)
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-gray-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-gray-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CollectionReceipts;
