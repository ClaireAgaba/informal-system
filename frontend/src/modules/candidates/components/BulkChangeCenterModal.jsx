import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Building, AlertTriangle } from 'lucide-react';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import Button from '@shared/components/Button';

const BulkChangeCenterModal = ({ selectedCount, onClose, onConfirm, isLoading }) => {
  const [selectedCenter, setSelectedCenter] = useState('');

  // Fetch all assessment centers (no pagination limit, include inactive)
  const { data: centerData, isLoading: loadingCenters } = useQuery({
    queryKey: ['assessment-centers-all'],
    queryFn: () => assessmentCenterApi.getAll({ page_size: 1000 }),
  });

  const centerList = centerData?.data?.results || centerData?.data || [];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedCenter) {
      onConfirm(selectedCenter);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Bulk Change Assessment Center
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                <strong>{selectedCount}</strong> candidate(s) selected
              </p>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">This will update:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Candidate's assessment center</li>
                  <li>Registration number (new center code)</li>
                  <li>Payment code</li>
                  <li>Fee records (moved to new center)</li>
                </ul>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Building className="w-4 h-4 inline mr-1" />
                Select New Assessment Center
              </label>
              {loadingCenters ? (
                <div className="text-sm text-gray-500">Loading centers...</div>
              ) : (
                <select
                  value={selectedCenter}
                  onChange={(e) => setSelectedCenter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">-- Select Center --</option>
                  {centerList.map((center) => (
                    <option key={center.id} value={center.id}>
                      {center.center_number} - {center.center_name}
                    </option>
                  ))}
                </select>
              )}
              {!loadingCenters && (
                <p className="text-xs text-gray-500 mt-1">
                  {centerList.length} centers available
                </p>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t bg-gray-50 rounded-b-lg">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={isLoading}
              disabled={isLoading || !selectedCenter}
            >
              Change Center
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BulkChangeCenterModal;
