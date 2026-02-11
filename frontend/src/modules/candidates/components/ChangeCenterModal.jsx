import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { X, Building2, AlertTriangle, Search } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import Button from '@shared/components/Button';

const ChangeCenterModal = ({ candidate, onClose }) => {
  const queryClient = useQueryClient();
  const [selectedCenter, setSelectedCenter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchAllPagesApi = async (fetchPage, params = {}, page = 1, acc = []) => {
    const response = await fetchPage({ ...params, page, page_size: 1000 });
    const data = response?.data;

    if (Array.isArray(data)) {
      return [...acc, ...data];
    }

    const results = data?.results || [];
    const nextAcc = [...acc, ...results];

    if (!data?.next) {
      return nextAcc;
    }

    return fetchAllPagesApi(fetchPage, params, page + 1, nextAcc);
  };

  // Fetch all assessment centers
  const { data: centersData, isLoading } = useQuery({
    queryKey: ['assessment-centers-list'],
    queryFn: () => fetchAllPagesApi(assessmentCenterApi.getAll),
  });

  const centersList = centersData || [];

  // Change center mutation
  const changeCenterMutation = useMutation({
    mutationFn: (newCenterId) => candidateApi.changeCenter(candidate.id, newCenterId),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', candidate.id]);
      queryClient.invalidateQueries(['candidate-enrollments', candidate.id]);

      const { old_registration_number, new_registration_number, fees_moved } = response.data;

      let message = response.data.message;
      if (old_registration_number !== new_registration_number) {
        message += `\nReg No: ${old_registration_number} → ${new_registration_number}`;
      }
      if (fees_moved > 0) {
        message += `\n${fees_moved} fee record(s) moved`;
      }

      toast.success(message, { duration: 5000 });
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to change center');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedCenter) {
      toast.error('Please select an assessment center');
      return;
    }
    changeCenterMutation.mutate(selectedCenter);
  };

  const currentCenter = candidate.assessment_center;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Change Assessment Center
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
                <strong>Candidate:</strong> {candidate.full_name}
              </p>
              {currentCenter?.center_name && (
                <p className="text-sm text-blue-600 mt-1">
                  <strong>Current Center:</strong> {currentCenter.center_name} ({currentCenter.center_number})
                </p>
              )}
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Important:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Registration number will be regenerated</li>
                  <li>Fees will be transferred to the new center</li>
                  <li>Branch assignment will be reset</li>
                </ul>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Building2 className="w-4 h-4 inline mr-1" />
                Select New Assessment Center
              </label>
              {isLoading ? (
                <div className="text-sm text-gray-500">Loading centers...</div>
              ) : (
                <div className="space-y-2">
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search center name or number..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full px-3 py-2 pl-9 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                    />
                    <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                  </div>

                  <div className="border border-gray-300 rounded-lg max-h-60 overflow-y-auto bg-white">
                    {centersList
                      .filter(center =>
                        (!currentCenter || center.id !== currentCenter.id) &&
                        (
                          center.center_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          center.center_number?.toLowerCase().includes(searchTerm.toLowerCase())
                        )
                      )
                      .length > 0 ? (
                      <div className="divide-y divide-gray-100">
                        {centersList
                          .filter(center =>
                            (!currentCenter || center.id !== currentCenter.id) &&
                            (
                              center.center_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                              center.center_number?.toLowerCase().includes(searchTerm.toLowerCase())
                            )
                          )
                          .map((center) => (
                            <div
                              key={center.id}
                              onClick={() => setSelectedCenter(center.id)}
                              className={`px-4 py-2 text-sm cursor-pointer transition-colors ${selectedCenter === center.id
                                  ? 'bg-blue-50 text-blue-900 font-medium'
                                  : 'text-gray-700 hover:bg-gray-50'
                                }`}
                            >
                              {center.center_name} ({center.center_number})
                            </div>
                          ))}
                      </div>
                    ) : (
                      <div className="p-4 text-center text-sm text-gray-500">
                        No centers found matching "{searchTerm}"
                      </div>
                    )}
                  </div>

                  {selectedCenter && (
                    <p className="text-xs text-blue-600 font-medium text-right">
                      Selection active
                    </p>
                  )}
                </div>
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
              loading={changeCenterMutation.isPending}
              disabled={changeCenterMutation.isPending || !selectedCenter}
            >
              Change Center
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangeCenterModal;
