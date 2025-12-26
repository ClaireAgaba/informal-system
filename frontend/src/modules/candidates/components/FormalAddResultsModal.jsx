import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Plus, Trash2 } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import Button from '@shared/components/Button';

const FormalAddResultsModal = ({ isOpen, onClose, candidateId, enrollments }) => {
  const queryClient = useQueryClient();
  const [selectedSeries, setSelectedSeries] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [structureType, setStructureType] = useState('');
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  // Debug and extract enrollment data
  console.log('Enrollments in modal:', enrollments);
  const enrollment = enrollments?.[0];
  console.log('First enrollment:', enrollment);
  console.log('Enrollment keys:', enrollment ? Object.keys(enrollment) : 'no enrollment');
  
  const seriesId = enrollment?.assessment_series;
  const seriesName = enrollment?.assessment_series_name;
  
  // Try different possible field names for level
  const levelData = enrollment?.level || enrollment?.qualification_level || enrollment?.occupation_level;
  const levelId = levelData?.id || enrollment?.level_id;
  const levelName = levelData?.level_name || enrollment?.level_name;
  const structureTypeFromEnrollment = levelData?.structure_type || enrollment?.structure_type;

  console.log('Level data:', levelData);
  console.log('Extracted data:', { seriesId, seriesName, levelId, levelName, structureTypeFromEnrollment });

  // Auto-select series and level if available
  React.useEffect(() => {
    if (enrollment && !selectedSeries && seriesId) {
      console.log('Auto-selecting:', seriesId, levelId, 'structure:', structureTypeFromEnrollment);
      setSelectedSeries(seriesId.toString());
      if (levelId) {
        setSelectedLevel(levelId.toString());
      }
      // Set structure type from enrollment
      if (structureTypeFromEnrollment) {
        setStructureType(structureTypeFromEnrollment);
      } else {
        console.error('No structure_type found in enrollment data!');
      }
    }
  }, [enrollment, selectedSeries, seriesId, levelId, structureTypeFromEnrollment]);

  // Get exams/papers from enrollment
  const items = structureType === 'modules' 
    ? enrollment?.modules || []
    : enrollment?.papers || [];
  
  console.log('Structure type:', structureType);
  console.log('Items (papers/modules):', items);
  console.log('Enrollment papers:', enrollment?.papers);
  console.log('Enrollment modules:', enrollment?.modules);

  // Add mutation
  const addMutation = useMutation({
    mutationFn: (data) => candidateApi.addFormalResults(candidateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-results', candidateId]);
      handleClose();
    },
    onError: (error) => {
      setError(error.response?.data?.error || 'Failed to add results');
    },
  });

  const handleClose = () => {
    setSelectedSeries('');
    setSelectedLevel('');
    setStructureType('');
    setResults([]);
    setError('');
    onClose();
  };

  const handleSeriesChange = (seriesId) => {
    setSelectedSeries(seriesId);
    setSelectedLevel('');
    setStructureType('');
    setResults([]);
  };

  const handleLevelChange = (levelId) => {
    setSelectedLevel(levelId);
    const level = levels.find(l => l?.id === parseInt(levelId));
    setStructureType(level?.structure_type || '');
    setResults([]);
  };

  const addResult = () => {
    // Just add a single result row with type and mark
    setResults([...results, { 
      type: 'theory', 
      mark: '' 
    }]);
  };

  const removeResult = (index) => {
    setResults(results.filter((_, i) => i !== index));
  };

  const updateResult = (index, field, value) => {
    const updated = [...results];
    updated[index] = { ...updated[index], [field]: value };
    
    // If paper is selected, auto-set the type based on paper's type
    if (field === 'paper_id' && value && structureType === 'papers') {
      const selectedPaper = items.find(p => p.paper === parseInt(value));
      if (selectedPaper && selectedPaper.paper_type) {
        // Convert paper_type to lowercase to match our type values
        updated[index].type = selectedPaper.paper_type.toLowerCase();
      }
    }
    
    setResults(updated);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!selectedSeries || results.length === 0) {
      setError('Please fill in all required fields');
      return;
    }

    // Validate all results have required fields
    const invalidResults = results.filter(r => {
      if (structureType === 'papers') {
        return !r.paper_id || !r.type || r.mark === '';
      }
      return !r.type || r.mark === '';
    });

    if (invalidResults.length > 0) {
      setError('Please fill in all result fields');
      return;
    }

    // Use levelId from enrollment, default to 1 if not found
    const finalLevelId = levelId || 1;

    addMutation.mutate({
      assessment_series: parseInt(selectedSeries),
      level_id: finalLevelId,
      structure_type: structureType || 'modules',
      results: results.map(r => ({
        ...(structureType === 'papers' && r.paper_id ? { paper_id: parseInt(r.paper_id) } : {}),
        type: r.type,
        mark: parseFloat(r.mark),
      })),
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={handleClose} />

        <div className="inline-block w-full max-w-4xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white rounded-lg shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Add Formal Results</h3>
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

            {/* Enrollment Info - Auto-selected */}
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Assessment Series
                  </label>
                  <p className="text-sm font-semibold text-gray-900">{seriesName || 'Not enrolled'}</p>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Level
                  </label>
                  <p className="text-sm font-semibold text-gray-900">
                    {levelName || 'Not enrolled'} 
                    {structureType && <span className="text-xs text-gray-500 ml-2">({structureType === 'modules' ? 'Module-based' : 'Paper-based'})</span>}
                  </p>
                </div>
              </div>
            </div>

            {/* Results Entry */}
            {(levelId || seriesId) && (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-medium text-gray-700">
                    Results ({structureType === 'modules' ? 'Module-based: 2 rows per exam' : 'Paper-based: 1 row per paper'})
                  </h4>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addResult}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add {structureType === 'modules' ? 'Exam' : 'Paper'}
                  </Button>
                </div>

                {results.length === 0 ? (
                  <div className="text-center py-8 border border-dashed border-gray-300 rounded-md">
                    <p className="text-sm text-gray-500">
                      No results added yet. Click "Add {structureType === 'modules' ? 'Exam' : 'Paper'}" to start.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {results.map((result, index) => (
                      <div key={index} className="p-4 border border-gray-200 rounded-md bg-gray-50">
                        <div className="flex items-start gap-4">
                          <div className={`flex-1 grid ${structureType === 'papers' ? 'grid-cols-3' : 'grid-cols-2'} gap-4`}>
                            {/* Paper Selection (only for paper-based) */}
                            {structureType === 'papers' && (
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">
                                  Paper *
                                </label>
                                <select
                                  value={result.paper_id || ''}
                                  onChange={(e) => updateResult(index, 'paper_id', e.target.value)}
                                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                                  required
                                >
                                  <option value="">Select paper</option>
                                  {items.map(paper => (
                                    <option key={paper.paper} value={paper.paper}>
                                      {paper.paper_code} - {paper.paper_name}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            )}

                            {/* Type */}
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Type * {structureType === 'papers' && <span className="text-xs text-gray-500">(Auto-set)</span>}
                              </label>
                              <select
                                value={result.type}
                                onChange={(e) => updateResult(index, 'type', e.target.value)}
                                className={`w-full px-2 py-1 text-sm border border-gray-300 rounded-md ${structureType === 'papers' ? 'bg-gray-100' : ''}`}
                                disabled={structureType === 'papers'}
                                required
                              >
                                <option value="theory">Theory</option>
                                <option value="practical">Practical</option>
                              </select>
                            </div>

                            {/* Mark */}
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Mark (0-100) *
                              </label>
                              <input
                                type="number"
                                min="-1"
                                max="100"
                                step="0.01"
                                value={result.mark}
                                onChange={(e) => updateResult(index, 'mark', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md"
                                placeholder="Enter mark"
                                required
                              />
                            </div>
                          </div>

                          {/* Remove Button */}
                          <button
                            type="button"
                            onClick={() => removeResult(index)}
                            className="mt-6 text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <p className="mt-2 text-xs text-gray-500">
                  * Use -1 for missing marks
                </p>
              </>
            )}

            {/* Footer */}
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={addMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={addMutation.isPending || !selectedSeries || results.length === 0}
              >
                {addMutation.isPending ? 'Adding...' : 'Add Results'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FormalAddResultsModal;
