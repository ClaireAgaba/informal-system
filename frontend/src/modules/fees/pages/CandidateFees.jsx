import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Banknote } from 'lucide-react';
import feesApi from '../api/feesApi';
import { formatCurrency, formatDate } from '../../../shared/utils/formatters';

export default function CandidateFees() {
  const [filters, setFilters] = useState({
    search: '',
    assessment_series: '',
    payment_status: '',
    attempt_status: '',
  });

  const { data: feesData, isLoading } = useQuery({
    queryKey: ['candidate-fees', filters],
    queryFn: () => feesApi.getCandidateFees(filters),
  });

  const fees = feesData?.data?.results || [];
  const totalAmount = fees.reduce((sum, fee) => sum + parseFloat(fee.total_amount || 0), 0);
  const totalPaid = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_paid || 0), 0);
  const totalDue = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_due || 0), 0);

  const getPaymentStatusBadge = (status) => {
    const badges = {
      not_paid: 'bg-red-100 text-red-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      successful: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  const getAttemptStatusBadge = (status) => {
    const badges = {
      no_attempt: 'bg-gray-100 text-gray-800',
      failed: 'bg-red-100 text-red-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      successful: 'bg-green-100 text-green-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Banknote className="h-8 w-8 text-blue-600" />
          Candidate Fees
        </h1>
        <p className="text-gray-600 mt-1">Manage and track candidate fee payments</p>
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
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Reg No
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Occupation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Code
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Assessment Series
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Attempt Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan="11" className="px-6 py-4 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : fees.length === 0 ? (
                <tr>
                  <td colSpan="11" className="px-6 py-4 text-center text-gray-500">
                    No candidate fees found
                  </td>
                </tr>
              ) : (
                fees.map((fee) => (
                  <tr key={fee.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {fee.registration_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {fee.candidate_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {fee.occupation_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {fee.payment_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {fee.assessment_series_name}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {fee.payment_date ? formatDate(fee.payment_date) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPaymentStatusBadge(fee.payment_status)}`}>
                        {fee.payment_status?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getAttemptStatusBadge(fee.attempt_status)}`}>
                        {fee.attempt_status?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {fees.length > 0 && (
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-sm font-bold text-gray-900 text-right">
                    TOTALS:
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
                  <td colSpan="3"></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>
    </div>
  );
}
