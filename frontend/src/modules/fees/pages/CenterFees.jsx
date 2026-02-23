import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Building2, Banknote, FileSpreadsheet, X } from 'lucide-react';
import { toast } from 'sonner';
import feesApi from '../api/feesApi';
import assessmentSeriesApi from '../../assessment-series/services/assessmentSeriesApi';
import { formatCurrency } from '../../../shared/utils/formatters';

export default function CenterFees() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    search: '',
    assessment_series: '',
  });
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportParams, setReportParams] = useState({ quarter: '', assessment_series: '' });
  const [reportLoading, setReportLoading] = useState(false);

  const { data: feesData, isLoading } = useQuery({
    queryKey: ['center-fees', filters],
    queryFn: () => feesApi.getCenterFees(filters),
  });

  const { data: seriesData } = useQuery({
    queryKey: ['assessment-series-all'],
    queryFn: () => assessmentSeriesApi.getAll(),
    enabled: showReportDialog,
  });

  const allSeries = seriesData?.data?.results || seriesData?.data || [];
  const filteredSeries = reportParams.quarter
    ? allSeries.filter((s) => s.quarter === reportParams.quarter)
    : allSeries;

  const fees = feesData?.data?.results || [];
  const totalCandidates = fees.reduce((sum, fee) => sum + (fee.total_candidates || 0), 0);
  const totalAmount = fees.reduce((sum, fee) => sum + parseFloat(fee.total_amount || 0), 0);
  const totalPaid = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_paid || 0), 0);
  const totalDue = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_due || 0), 0);

  const handleGenerateReport = async () => {
    if (!reportParams.quarter) {
      toast.error('Please select a quarter');
      return;
    }
    setReportLoading(true);
    try {
      const params = { quarter: reportParams.quarter };
      if (reportParams.assessment_series) {
        params.assessment_series = reportParams.assessment_series;
      }
      const response = await feesApi.getQuarterlyReport(params);
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `UVTAB_Quarterly_Report_${reportParams.quarter}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded successfully');
      setShowReportDialog(false);
      setReportParams({ quarter: '', assessment_series: '' });
    } catch (error) {
      const msg = error.response?.data?.error || 'Failed to generate report';
      toast.error(typeof msg === 'string' ? msg : 'Failed to generate report');
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Banknote className="h-8 w-8 text-green-600" />
            Center Fees
          </h1>
          <p className="text-gray-600 mt-1">Manage and track assessment center fees</p>
        </div>
        <button
          onClick={() => setShowReportDialog(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
        >
          <FileSpreadsheet className="h-4 w-4" />
          Reports
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm text-purple-600 font-medium">Total Candidates</div>
          <div className="text-2xl font-bold text-purple-900 mt-1">
            {totalCandidates.toLocaleString()}
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-600 font-medium">Total Amount</div>
          <div className="text-2xl font-bold text-blue-900 mt-1">
            {formatCurrency(totalAmount)}
          </div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium">Amount Paid</div>
          <div className="text-2xl font-bold text-green-900 mt-1">
            {formatCurrency(totalPaid)}
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 font-medium">Amount Due</div>
          <div className="text-2xl font-bold text-red-900 mt-1">
            {formatCurrency(totalDue)}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Search by center name..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Series
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Center
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Candidates
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Amount
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount Paid
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount Due
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : fees.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No center fees found
                  </td>
                </tr>
              ) : (
                fees.map((fee) => (
                  <tr 
                    key={fee.id} 
                    onClick={() => navigate(`/fees/center-fees/${fee.id}`)}
                    className="hover:bg-blue-50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {fee.assessment_series_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {fee.assessment_center_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {fee.total_candidates.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatCurrency(fee.total_amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
                      {formatCurrency(fee.amount_paid)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
                      {formatCurrency(fee.amount_due)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {fees.length > 0 && (
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan="2" className="px-6 py-4 text-sm font-bold text-gray-900 text-right">
                    TOTALS:
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-right text-gray-900">
                    {totalCandidates.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-right text-gray-900">
                    {formatCurrency(totalAmount)}
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-right text-green-600">
                    {formatCurrency(totalPaid)}
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-right text-red-600">
                    {formatCurrency(totalDue)}
                  </td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>

      {/* Quarterly Report Dialog */}
      {showReportDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                Generate Quarterly Report
              </h2>
              <button
                onClick={() => { setShowReportDialog(false); setReportParams({ quarter: '', assessment_series: '' }); }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quarter <span className="text-red-500">*</span>
                </label>
                <select
                  value={reportParams.quarter}
                  onChange={(e) => setReportParams({ ...reportParams, quarter: e.target.value, assessment_series: '' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">Select Quarter</option>
                  <option value="Q1">Q1 (July - September)</option>
                  <option value="Q2">Q2 (October - December)</option>
                  <option value="Q3">Q3 (January - March)</option>
                  <option value="Q4">Q4 (April - June)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Series <span className="text-gray-400 text-xs">(optional — filter within quarter)</span>
                </label>
                <select
                  value={reportParams.assessment_series}
                  onChange={(e) => setReportParams({ ...reportParams, assessment_series: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  disabled={!reportParams.quarter}
                >
                  <option value="">All series in this quarter</option>
                  {filteredSeries.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                {reportParams.quarter && filteredSeries.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">No series assigned to this quarter yet. Set quarters on assessment series.</p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowReportDialog(false); setReportParams({ quarter: '', assessment_series: '' }); }}
                className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={reportLoading || !reportParams.quarter}
                className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2"
              >
                {reportLoading ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Generating...
                  </>
                ) : (
                  <>
                    <FileSpreadsheet className="h-4 w-4" />
                    Generate Report
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
