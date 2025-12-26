import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Button from '@shared/components/Button';
import candidateApi from '../services/candidateApi';

const EditResultsModal = ({ isOpen, onClose, candidateId, results }) => {
  const queryClient = useQueryClient();
  const [editedMarks, setEditedMarks] = useState({});

  // Initialize marks from existing results
  useEffect(() => {
    if (results && results.length > 0) {
      const initialMarks = {};
      results.forEach(result => {
        initialMarks[result.id] = result.mark !== null ? result.mark : '';
      });
      setEditedMarks(initialMarks);
    }
  }, [results]);

  const updateResultsMutation = useMutation({
    mutationFn: (data) => candidateApi.updateResults(candidateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-results', candidateId]);
      toast.success('Results updated successfully!');
      onClose();
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.error || error.message;
      toast.error(`Failed to update results: ${errorMsg}`);
    },
  });

  const handleMarkChange = (resultId, value) => {
    // Validate mark is between 0-100 or -1 for missing
    const numValue = parseFloat(value);
    if (value === '' || value === '-1' || (numValue >= 0 && numValue <= 100)) {
      setEditedMarks(prev => ({
        ...prev,
        [resultId]: value
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Prepare data - only send changed marks
    const updatedResults = Object.entries(editedMarks)
      .map(([resultId, mark]) => ({
        result_id: parseInt(resultId),
        mark: mark === '' ? null : parseFloat(mark)
      }));

    updateResultsMutation.mutate({ results: updatedResults });
  };

  const handleCancel = () => {
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Edit Results</h2>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 px-3 py-2 bg-gray-50 rounded-lg font-medium text-sm text-gray-700">
              <div className="col-span-3">Assessment Series</div>
              <div className="col-span-3">Module</div>
              <div className="col-span-2">Type</div>
              <div className="col-span-2">Current Mark</div>
              <div className="col-span-2">New Mark</div>
            </div>

            {/* Results List */}
            {results && results.length > 0 ? (
              results.map((result) => (
                <div key={result.id} className="grid grid-cols-12 gap-4 items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="col-span-3 text-sm text-gray-900">
                    {result.assessment_series_name}
                  </div>
                  <div className="col-span-3">
                    <div className="text-sm font-medium text-gray-900">
                      {result.module_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {result.module_code}
                    </div>
                  </div>
                  <div className="col-span-2 text-sm text-gray-900 capitalize">
                    {result.type}
                  </div>
                  <div className="col-span-2 text-sm font-semibold text-gray-900">
                    {result.mark === -1 ? 'Missing' : (result.mark !== null ? result.mark : '-')}
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      min="-1"
                      max="100"
                      step="0.01"
                      value={editedMarks[result.id] !== undefined ? editedMarks[result.id] : ''}
                      onChange={(e) => handleMarkChange(result.id, e.target.value)}
                      placeholder="0-100"
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                No results to edit
              </div>
            )}
          </div>

          {/* Help Text */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Enter marks between 0-100, or -1 for missing marks. Leave blank to keep current value.
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 mt-6">
            <Button
              type="button"
              variant="secondary"
              onClick={handleCancel}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={updateResultsMutation.isPending}
              disabled={updateResultsMutation.isPending}
            >
              Update Marks
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditResultsModal;
