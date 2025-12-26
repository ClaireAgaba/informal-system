import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Printer, FileText, Users } from 'lucide-react';
import feesApi from '../api/feesApi';
import { formatCurrency } from '../../../shared/utils/formatters';

export default function CenterFeeView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: feeData, isLoading } = useQuery({
    queryKey: ['center-fee', id],
    queryFn: () => feesApi.getCenterFee(id),
  });

  const fee = feeData?.data;

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

        {/* Print Options */}
        <div className="flex gap-2">
          <button
            onClick={handlePrintCenterInvoice}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <FileText className="h-4 w-4" />
            Center Invoice
          </button>
          <button
            onClick={handlePrintCandidateSummary}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
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

      {/* Invoice Preview Info */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Printer className="h-5 w-5" />
          Available Documents
        </h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-white rounded border border-gray-200">
            <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Center Invoice</h3>
              <p className="text-sm text-gray-600">
                Summary invoice showing total candidates breakdown by registration category
                (Modular, Formal, etc.) with amounts billed, paid, and due.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-white rounded border border-gray-200">
            <Users className="h-5 w-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Candidate Summary Invoice</h3>
              <p className="text-sm text-gray-600">
                Detailed invoice with complete list of all candidates, their registration numbers,
                occupations, modules, and individual billing information.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
