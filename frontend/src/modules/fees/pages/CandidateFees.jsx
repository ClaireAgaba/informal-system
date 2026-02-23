import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Banknote, CheckCircle, ShieldCheck, X } from 'lucide-react';
import feesApi from '../api/feesApi';
import { formatCurrency, formatDate } from '../../../shared/utils/formatters';

export default function CandidateFees() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    search: '',
    assessment_series: '',
    payment_status: '',
    attempt_status: '',
    verification_status: '',
  });
  const [selectedIds, setSelectedIds] = useState([]);
  const [showRefDialog, setShowRefDialog] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const { data: feesData, isLoading } = useQuery({
    queryKey: ['candidate-fees', filters],
    queryFn: () => feesApi.getCandidateFees(filters),
  });

  const fees = feesData?.data?.results || [];
  const totalAmount = fees.reduce((sum, fee) => sum + parseFloat(fee.total_amount || 0), 0);
  const totalPaid = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_paid || 0), 0);
  const totalDue = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_due || 0), 0);

  const markMutation = useMutation({
    mutationFn: ({ feeIds, ref }) => feesApi.markAsPaid(feeIds, ref),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['candidate-fees'] });
      setSelectedIds([]);
      setShowRefDialog(false);
      setActionLoading(false);
      alert(res.data.message);
    },
    onError: (err) => {
      setActionLoading(false);
      alert(err.response?.data?.error || 'Failed to mark as paid');
    },
  });

  const approveMutation = useMutation({
    mutationFn: (feeIds) => feesApi.approvePayment(feeIds),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['candidate-fees'] });
      setSelectedIds([]);
      setShowApproveDialog(false);
      setActionLoading(false);
      alert(res.data.message);
    },
    onError: (err) => {
      setActionLoading(false);
      alert(err.response?.data?.error || 'Failed to approve payment');
    },
  });

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === fees.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(fees.map((f) => f.id));
    }
  };

  const handleMarkAsPaid = (ref) => {
    setActionLoading(true);
    markMutation.mutate({ feeIds: selectedIds, ref });
  };

  const handleApprovePayment = () => {
    setActionLoading(true);
    approveMutation.mutate(selectedIds);
  };

  const selectedPendingCount = selectedIds.filter((id) => {
    const f = fees.find((fee) => fee.id === id);
    return f && f.verification_status === 'pending';
  }).length;

  const selectedMarkedCount = selectedIds.filter((id) => {
    const f = fees.find((fee) => fee.id === id);
    return f && f.verification_status === 'marked';
  }).length;

  // Check if all selected pending fees are already paid via SchoolPay
  const selectedPendingFees = selectedIds
    .map((id) => fees.find((fee) => fee.id === id))
    .filter((f) => f && f.verification_status === 'pending');
  const allSchoolPay = selectedPendingFees.length > 0 &&
    selectedPendingFees.every((f) => f.payment_status === 'successful');

  // Check if any selected pending fees have unverified candidates
  const hasUnverified = selectedPendingFees.some((f) => f.candidate_verification_status !== 'verified');

  const handleMarkAsPaidClick = () => {
    if (hasUnverified) {
      alert('Cannot mark as paid: some selected candidates are not verified.');
      return;
    }
    if (allSchoolPay) {
      // All are SchoolPay — auto-submit without dialog
      setActionLoading(true);
      markMutation.mutate({ feeIds: selectedIds, ref: 'via_schoolpay' });
    } else {
      setShowRefDialog(true);
    }
  };

  const getPaymentStatusBadge = (status) => {
    const badges = {
      not_paid: 'bg-red-100 text-red-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      successful: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  const getVerificationBadge = (status) => {
    const badges = {
      pending: 'bg-gray-100 text-gray-800',
      marked: 'bg-orange-100 text-orange-800',
      approved: 'bg-green-100 text-green-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  const getVerificationLabel = (status) => {
    const labels = {
      pending: 'PENDING',
      marked: 'MARKED',
      approved: 'PAID',
    };
    return labels[status] || status?.toUpperCase();
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Banknote className="h-8 w-8 text-blue-600" />
            Candidate Fees
          </h1>
          <p className="text-gray-600 mt-1">Manage and track candidate fee payments</p>
        </div>

        {selectedIds.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600 font-medium">
              {selectedIds.length} selected
            </span>
            {selectedPendingCount > 0 && (
              <button
                onClick={handleMarkAsPaidClick}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium"
              >
                <CheckCircle className="h-4 w-4" />
                Mark as Paid ({selectedPendingCount})
              </button>
            )}
            {selectedMarkedCount > 0 && (
              <button
                onClick={() => setShowApproveDialog(true)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                <ShieldCheck className="h-4 w-4" />
                Approve Payment ({selectedMarkedCount})
              </button>
            )}
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <input
            type="text"
            placeholder="Search by payment code, reg no, name..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filters.payment_status}
            onChange={(e) => setFilters({ ...filters, payment_status: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Payment Status</option>
            <option value="not_paid">Not Paid</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="successful">Successful</option>
            <option value="failed">Failed</option>
          </select>
          <select
            value={filters.attempt_status}
            onChange={(e) => setFilters({ ...filters, attempt_status: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Attempt Status</option>
            <option value="no_attempt">No Attempt</option>
            <option value="failed">Failed</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="successful">Successful</option>
          </select>
          <select
            value={filters.verification_status}
            onChange={(e) => setFilters({ ...filters, verification_status: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Verification Status</option>
            <option value="pending">Pending</option>
            <option value="marked">Marked as Paid</option>
            <option value="approved">Approved (Paid)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 text-center">
                  <input
                    type="checkbox"
                    checked={fees.length > 0 && selectedIds.length === fees.length}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reg No
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occupation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Code
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Series
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Amount
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount Paid
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount Due
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Verification
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="12" className="px-6 py-4 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : fees.length === 0 ? (
                <tr>
                  <td colSpan="12" className="px-6 py-4 text-center text-gray-500">
                    No candidate fees found
                  </td>
                </tr>
              ) : (
                fees.map((fee) => (
                  <tr key={fee.id} className={`hover:bg-gray-50 ${selectedIds.includes(fee.id) ? 'bg-blue-50' : ''}`}>
                    <td className="px-3 py-4 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(fee.id)}
                        onChange={() => toggleSelect(fee.id)}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {fee.registration_number}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                      {fee.candidate_name}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                      {fee.occupation_name}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                      {fee.payment_code}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                      {fee.assessment_series_name}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatCurrency(fee.total_amount)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-green-600 font-medium">
                      {formatCurrency(fee.amount_paid)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-red-600 font-medium">
                      {formatCurrency(fee.amount_due)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                      {fee.payment_date ? formatDate(fee.payment_date) : '-'}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentStatusBadge(fee.payment_status)}`}>
                        {fee.payment_status?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getVerificationBadge(fee.verification_status)}`}>
                        {getVerificationLabel(fee.verification_status)}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {fees.length > 0 && (
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-sm font-bold text-gray-900 text-right">
                    TOTALS:
                  </td>
                  <td className="px-4 py-4 text-sm font-bold text-right text-gray-900">
                    {formatCurrency(totalAmount)}
                  </td>
                  <td className="px-4 py-4 text-sm font-bold text-right text-green-600">
                    {formatCurrency(totalPaid)}
                  </td>
                  <td className="px-4 py-4 text-sm font-bold text-right text-red-600">
                    {formatCurrency(totalDue)}
                  </td>
                  <td colSpan="3"></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>

      {/* Mark as Paid Reference Dialog */}
      {showRefDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">Mark as Paid</h3>
              <button onClick={() => setShowRefDialog(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              You are about to mark <strong>{selectedPendingCount}</strong> fee record(s) as paid.
              Select the payment reference:
            </p>
            <div className="space-y-3 mb-6">
              <button
                disabled={actionLoading}
                onClick={() => handleMarkAsPaid('bulk_payment')}
                className="w-full flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-orange-400 hover:bg-orange-50 transition-colors text-left"
              >
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Banknote className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Bulk Payment</div>
                  <div className="text-xs text-gray-500">Direct bank deposit or bulk transfer</div>
                </div>
              </button>
              <button
                disabled={actionLoading}
                onClick={() => handleMarkAsPaid('via_schoolpay')}
                className="w-full flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors text-left"
              >
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Via SchoolPay</div>
                  <div className="text-xs text-gray-500">Payment confirmed through SchoolPay</div>
                </div>
              </button>
            </div>
            {actionLoading && (
              <div className="text-center text-sm text-gray-500">Processing...</div>
            )}
          </div>
        </div>
      )}

      {/* Approve Payment Dialog */}
      {showApproveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">Approve Payment</h3>
              <button onClick={() => setShowApproveDialog(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              You are about to approve <strong>{selectedMarkedCount}</strong> fee record(s).
              This will set their status to <strong className="text-green-700">PAID</strong>.
              This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowApproveDialog(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm font-medium"
              >
                Cancel
              </button>
              <button
                disabled={actionLoading}
                onClick={handleApprovePayment}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium flex items-center gap-2"
              >
                <ShieldCheck className="h-4 w-4" />
                {actionLoading ? 'Approving...' : 'Approve Payment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
