import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileText, Users, Banknote, CheckCircle, ShieldCheck, X } from 'lucide-react';
import feesApi from '../api/feesApi';
import { formatCurrency, formatDate } from '../../../shared/utils/formatters';

export default function CenterFeeView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState([]);
  const [showRefDialog, setShowRefDialog] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const { data: feeData, isLoading } = useQuery({
    queryKey: ['center-fee', id],
    queryFn: () => feesApi.getCenterFee(id),
  });

  const { data: candidatesData, isLoading: candidatesLoading } = useQuery({
    queryKey: ['center-fee-candidates', id],
    queryFn: () => feesApi.getCenterFeeCandidates(id),
    enabled: !!id,
  });

  const fee = feeData?.data;
  const candidates = candidatesData?.data || [];

  const markMutation = useMutation({
    mutationFn: ({ feeIds, ref }) => feesApi.markAsPaid(feeIds, ref),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['center-fee-candidates', id] });
      queryClient.invalidateQueries({ queryKey: ['center-fee', id] });
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
      queryClient.invalidateQueries({ queryKey: ['center-fee-candidates', id] });
      queryClient.invalidateQueries({ queryKey: ['center-fee', id] });
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

  const toggleSelect = (feeId) => {
    setSelectedIds((prev) =>
      prev.includes(feeId) ? prev.filter((i) => i !== feeId) : [...prev, feeId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === candidates.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(candidates.map((c) => c.id));
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

  const selectedPendingCount = selectedIds.filter((feeId) => {
    const c = candidates.find((f) => f.id === feeId);
    return c && c.verification_status === 'pending';
  }).length;

  const selectedMarkedCount = selectedIds.filter((feeId) => {
    const c = candidates.find((f) => f.id === feeId);
    return c && c.verification_status === 'marked';
  }).length;

  // Check if all selected pending fees are already paid via SchoolPay
  const selectedPendingFees = selectedIds
    .map((feeId) => candidates.find((f) => f.id === feeId))
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
    const labels = { pending: 'PENDING', marked: 'MARKED', approved: 'PAID' };
    return labels[status] || status?.toUpperCase();
  };

  const handlePrintCenterInvoice = () => {
    window.open(`/api/fees/center-fees/${id}/center_invoice/`, '_blank');
  };

  const handlePrintCandidateSummary = () => {
    window.open(`/api/fees/center-fees/${id}/candidate_summary_invoice/`, '_blank');
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!fee) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-gray-500">Center fee not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/fees/center-fees')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Center Fee Details</h1>
            <p className="text-gray-600 mt-1">
              {fee.assessment_center_name} - {fee.assessment_series_name}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedIds.length > 0 && (
            <div className="flex items-center gap-3 mr-4">
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
          <button
            onClick={handlePrintCenterInvoice}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            <FileText className="h-4 w-4" />
            Center Invoice
          </button>
          <button
            onClick={handlePrintCandidateSummary}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
          >
            <Users className="h-4 w-4" />
            Candidate Summary
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm text-purple-600 font-medium">Total Candidates</div>
          <div className="text-2xl font-bold text-purple-900 mt-1">
            {fee.total_candidates}
          </div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-600 font-medium">Total Amount</div>
          <div className="text-2xl font-bold text-blue-900 mt-1">
            {formatCurrency(fee.total_amount)}
          </div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium">Amount Paid</div>
          <div className="text-2xl font-bold text-green-900 mt-1">
            {formatCurrency(fee.amount_paid)}
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 font-medium">Amount Due</div>
          <div className="text-2xl font-bold text-red-900 mt-1">
            {formatCurrency(fee.amount_due)}
          </div>
        </div>
      </div>

      {/* Center Information */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Center Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600">Center Number</label>
            <p className="text-gray-900 font-medium">{fee.assessment_center_number}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Center Name</label>
            <p className="text-gray-900 font-medium">{fee.assessment_center_name}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Assessment Series</label>
            <p className="text-gray-900 font-medium">{fee.assessment_series_name}</p>
          </div>
          <div>
            <label className="text-sm text-gray-600">Created Date</label>
            <p className="text-gray-900 font-medium">
              {new Date(fee.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Candidates Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Users className="h-5 w-5" />
            Candidates ({candidates.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 text-center">
                  <input
                    type="checkbox"
                    checked={candidates.length > 0 && selectedIds.length === candidates.length}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reg No</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Occupation</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Paid</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Due</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Verification</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {candidatesLoading ? (
                <tr>
                  <td colSpan="9" className="px-6 py-4 text-center text-gray-500">Loading candidates...</td>
                </tr>
              ) : candidates.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-6 py-4 text-center text-gray-500">No candidates found</td>
                </tr>
              ) : (
                candidates.map((c) => (
                  <tr key={c.id} className={`hover:bg-gray-50 ${selectedIds.includes(c.id) ? 'bg-blue-50' : ''}`}>
                    <td className="px-3 py-3 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(c.id)}
                        onChange={() => toggleSelect(c.id)}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{c.registration_number}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{c.candidate_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{c.occupation_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">{formatCurrency(c.total_amount)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-green-600 font-medium">{formatCurrency(c.amount_paid)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600 font-medium">{formatCurrency(c.amount_due)}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentStatusBadge(c.payment_status)}`}>
                        {c.payment_status?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getVerificationBadge(c.verification_status)}`}>
                        {getVerificationLabel(c.verification_status)}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
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
