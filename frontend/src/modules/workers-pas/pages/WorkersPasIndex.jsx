import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Search, ChevronLeft, ChevronRight, Plus, Download, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../../../services/apiClient';

const WorkersPasIndex = () => {
  const navigate = useNavigate();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('page_size', 20);
      if (search) params.append('search', search);
      const res = await apiClient.get(`/workers-pas/books/?${params.toString()}`);
      setBooks(res.data.results || res.data || []);
      setCount(res.data.count || (Array.isArray(res.data) ? res.data.length : 0));
      setTotalPages(res.data.total_pages || 1);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load Worker\'s PAS books');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { fetch(); }, [fetch]);
  useEffect(() => { setPage(1); }, [search]);

  const downloadBook = async (book) => {
    try {
      const res = await apiClient.get(`/workers-pas/books/${book.id}/download/`, {
        responseType: 'blob',
      });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (err) {
      toast.error('Failed to download PDF');
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary-600" />
            Worker's PAS Booklets
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Generated Worker's PAS booklets for assessed candidates.
          </p>
        </div>
        <button
          onClick={() => navigate('/workers-pas/generate')}
          className="inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium"
        >
          <Plus className="w-4 h-4 mr-2" /> Generate booklets
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 mb-4 p-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by book number, candidate name or reg no…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <button
          onClick={fetch}
          className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <span className="text-sm text-gray-500 ml-auto">{count} total</span>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading…</div>
        ) : books.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No books yet. Click "Generate booklets" to start.</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Book No.</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Candidate</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reg No</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Occupation</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Series</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Issued</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reprints</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {books.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono text-gray-900">{b.book_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{b.candidate_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{b.candidate_reg_no || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{b.occupation_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{b.series_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{b.issued_date}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{b.reprint_count}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => downloadBook(b)}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-xs hover:bg-gray-50"
                    >
                      <Download className="w-3.5 h-3.5 mr-1" /> PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-50"
            >
              <ChevronLeft className="w-4 h-4 mr-1" /> Previous
            </button>
            <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm disabled:opacity-50"
            >
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkersPasIndex;
