import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Building2, Banknote } from 'lucide-react';
import feesApi from '../api/feesApi';
import { formatCurrency } from '../../../shared/utils/formatters';

export default function CenterFees() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    search: '',
    assessment_series: '',
  });

  const { data: feesData, isLoading } = useQuery({
    queryKey: ['center-fees', filters],
    queryFn: () => feesApi.getCenterFees(filters),
  });

  const fees = feesData?.data?.results || [];
  const totalCandidates = fees.reduce((sum, fee) => sum + (fee.total_candidates || 0), 0);
  const totalAmount = fees.reduce((sum, fee) => sum + parseFloat(fee.total_amount || 0), 0);
  const totalPaid = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_paid || 0), 0);
  const totalDue = fees.reduce((sum, fee) => sum + parseFloat(fee.amount_due || 0), 0);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Banknote className="h-8 w-8 text-green-600" />
          Center Fees
        </h1>
        <p className="text-gray-600 mt-1">Manage and track assessment center fees</p>
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
    </div>
  );
}
