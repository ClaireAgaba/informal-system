import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import Button from '@shared/components/Button';
import { getGrade, getComment } from '../utils/gradingSystem';

const FormalEditResultsModal = ({ isOpen, onClose, candidateId, results }) => {
  const queryClient = useQueryClient();
  const [editedResults, setEditedResults] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && results) {
      // Initialize with current results
      setEditedResults(results.map(r => ({
        result_id: r.id,
        mark: r.mark !== null && r.mark !== undefined ? r.mark : '',
        originalMark: r.mark,
      })));
    }
  }, [isOpen, results]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data) => candidateApi.updateFormalResults(candidateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-results', candidateId]);
      handleClose();
    },
    onError: (error) => {
      setError(error.response?.data?.error || 'Failed to update results');
    },
  });

  const handleClose = () => {
    setEditedResults([]);
    setError('');
    onClose();
  };

  const updateMark = (index, value) => {
    const updated = [...editedResults];
    updated[index] = { ...updated[index], mark: value };
    setEditedResults(updated);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    // Only send results that have changed
    const changedResults = editedResults.filter((r, index) => {
      const newMark = parseFloat(r.mark);
      const oldMark = r.originalMark;
      return !isNaN(newMark) && newMark !== oldMark;
    });

    if (changedResults.length === 0) {
      setError('No changes detected');
      return;
    }

    updateMutation.mutate({
      results: changedResults.map(r => ({
        result_id: r.result_id,
        mark: parseFloat(r.mark),
      })),
    });
  };

  if (!isOpen) return null;

  // Group results by level
  const groupedResults = results?.reduce((acc, result, index) => {
    const levelKey = result.level?.name || 'Unknown Level';
    if (!acc[levelKey]) {
      acc[levelKey] = {
        level: result.level,
        items: []
      };
    }
    acc[levelKey].items.push({ ...result, editIndex: index });
    return acc;
  }, {}) || {};

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={handleClose} />

        <div className="inline-block w-full max-w-5xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white rounded-lg shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Edit Formal Results</h3>
            <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <form onSubmit={handleSubmit} className="px-6 py-4">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Update marks for existing results. Changes will be highlighted.
              </p>
            </div>

            {/* Results Table */}
            <div className="max-h-96 overflow-y-auto space-y-6">
              {Object.entries(groupedResults).map(([levelName, levelData]) => (
                <div key={levelName} className="border border-gray-200 rounded-lg overflow-hidden">
                  {/* Level Header */}
                  <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-900">
                      {levelName}
                      <span className="ml-2 text-xs font-normal text-gray-500">
                        ({levelData.level?.structure_type === 'modules' ? 'Module-based' : 'Paper-based'})
                      </span>
                    </h4>
                  </div>

                  {/* Results */}
                  <div className="divide-y divide-gray-200">
                    {levelData.items.map((result) => {
                      const editIndex = result.editIndex;
                      const currentMark = editedResults[editIndex]?.mark;
                      const hasChanged = currentMark !== '' && parseFloat(currentMark) !== result.mark;
                      const type = result.type?.toLowerCase() || 'practical';
                      const newGrade = currentMark !== '' ? getGrade(parseFloat(currentMark), type) : '-';
                      const newComment = currentMark !== '' ? getComment(parseFloat(currentMark), type) : '-';

                      return (
                        <div key={result.id} className={`p-4 ${hasChanged ? 'bg-yellow-50' : 'bg-white'}`}>
                          <div className="grid grid-cols-12 gap-4 items-center">
                            {/* Series & Type */}
                            <div className="col-span-3">
                              <div className="text-sm font-medium text-gray-900">
                                {result.assessment_series?.name}
                              </div>
                              <div className="text-xs text-gray-500 capitalize mt-1">
                                {result.type}
                              </div>
                            </div>

                            {/* Current Mark */}
                            <div className="col-span-2">
                              <label className="block text-xs font-medium text-gray-500 mb-1">
                                Current Mark
                              </label>
                              <div className="text-sm font-semibold text-gray-900">
                                {result.mark !== null && result.mark !== undefined ? result.mark : '-'}
                              </div>
                            </div>

                            {/* New Mark Input */}
                            <div className="col-span-2">
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                New Mark *
                              </label>
                              <input
                                type="number"
                                min="-1"
                                max="100"
                                step="0.01"
                                value={currentMark}
                                onChange={(e) => updateMark(editIndex, e.target.value)}
                                className={`w-full px-2 py-1 text-sm border rounded-md ${
                                  hasChanged 
                                    ? 'border-yellow-400 bg-yellow-50' 
                                    : 'border-gray-300'
                                }`}
                                placeholder="0-100"
                              />
                            </div>

                            {/* Current Grade */}
                            <div className="col-span-2">
                              <label className="block text-xs font-medium text-gray-500 mb-1">
                                Current Grade
                              </label>
                              <div className="text-sm font-semibold text-gray-900">
                                {result.grade || '-'}
                              </div>
                            </div>

                            {/* New Grade Preview */}
                            <div className="col-span-2">
                              <label className="block text-xs font-medium text-gray-500 mb-1">
                                New Grade
                              </label>
                              <div className={`text-sm font-semibold ${hasChanged ? 'text-yellow-700' : 'text-gray-400'}`}>
                                {hasChanged ? newGrade : '-'}
                              </div>
                            </div>

                            {/* Comment Preview */}
                            <div className="col-span-1">
                              <label className="block text-xs font-medium text-gray-500 mb-1">
                                Status
                              </label>
                              <div className={`text-xs ${hasChanged ? 'text-yellow-700' : 'text-gray-400'}`}>
                                {hasChanged ? newComment : result.comment}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <p className="mt-4 text-xs text-gray-500">
              * Use -1 for missing marks. Only changed results will be updated.
            </p>

            {/* Footer */}
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={updateMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? 'Updating...' : 'Update Results'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FormalEditResultsModal;
