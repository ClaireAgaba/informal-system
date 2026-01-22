import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { X, Briefcase, AlertTriangle } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import Button from '@shared/components/Button';

const ChangeOccupationModal = ({ candidate, onClose }) => {
  const queryClient = useQueryClient();
  const [selectedOccupation, setSelectedOccupation] = useState('');

  // Fetch all occupations with large page size to get all
  const { data: occupationsData, isLoading } = useQuery({
    queryKey: ['all-occupations'],
    queryFn: () => occupationApi.getAll({ page_size: 1000 }),
  });

  const allOccupations = occupationsData?.data?.results || occupationsData?.data || [];
  
  // Filter occupations based on candidate's registration category
  const occupationsList = allOccupations.filter(occ => {
    const candidateRegCat = candidate.registration_category;
    
    if (candidateRegCat === 'workers_pas') {
      return occ.occ_category === 'workers_pas';
    } else if (candidateRegCat === 'formal') {
      return occ.occ_category === 'formal';
    } else if (candidateRegCat === 'modular') {
      return occ.occ_category === 'formal' && occ.has_modular;
    }
    return true;
  });

  // Change occupation mutation
  const changeOccupationMutation = useMutation({
    mutationFn: (newOccupationId) => candidateApi.changeOccupation(candidate.id, newOccupationId),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', candidate.id]);
      
      const { old_registration_number, new_registration_number, new_occupation } = response.data;
      
      let message = response.data.message;
      if (old_registration_number !== new_registration_number) {
        message += `\nReg No: ${old_registration_number} → ${new_registration_number}`;
      }
      
      toast.success(message, { duration: 5000 });
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to change occupation');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedOccupation) {
      toast.error('Please select an occupation');
      return;
    }
    changeOccupationMutation.mutate(selectedOccupation);
  };

  const currentOccupation = candidate.occupation;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Change Occupation
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
              <p className="text-sm text-blue-600 mt-1">
                <strong>Registration Category:</strong> {candidate.registration_category === 'workers_pas' ? "Worker's PAS" : candidate.registration_category === 'modular' ? 'Modular' : 'Formal'}
              </p>
              {currentOccupation && (
                <p className="text-sm text-blue-600 mt-1">
                  <strong>Current Occupation:</strong> {currentOccupation.occ_name} ({currentOccupation.occ_code})
                </p>
              )}
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Important:</p>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  <li>Registration number will be regenerated</li>
                  <li>Existing results may not match new occupation</li>
                </ul>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Briefcase className="w-4 h-4 inline mr-1" />
                Select New Occupation
              </label>
              {isLoading ? (
                <div className="text-sm text-gray-500">Loading occupations...</div>
              ) : (
                <select
                  value={selectedOccupation}
                  onChange={(e) => setSelectedOccupation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">-- Select Occupation --</option>
                  {occupationsList
                    .filter(occ => !currentOccupation || occ.id !== currentOccupation.id)
                    .map((occ) => (
                      <option key={occ.id} value={occ.id}>
                        {occ.occ_name} ({occ.occ_code})
                      </option>
                    ))}
                </select>
              )}
              {!isLoading && (
                <p className="text-xs text-gray-500 mt-1">
                  {occupationsList.length} compatible occupation(s) for {candidate.registration_category === 'workers_pas' ? "Worker's PAS" : candidate.registration_category === 'modular' ? 'Modular' : 'Formal'} registration
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
              loading={changeOccupationMutation.isPending}
              disabled={changeOccupationMutation.isPending || !selectedOccupation}
            >
              Change Occupation
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangeOccupationModal;
