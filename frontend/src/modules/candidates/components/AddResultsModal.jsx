import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Button from '@shared/components/Button';
import candidateApi from '../services/candidateApi';

const AddResultsModal = ({ isOpen, onClose, candidateId, enrollments }) => {
  const queryClient = useQueryClient();
  const [selectedSeries, setSelectedSeries] = useState('');
  const [moduleMarks, setModuleMarks] = useState({});
  const [modules, setModules] = useState([]);

  // Get unique assessment series from enrollments
  const assessmentSeries = [...new Set(enrollments.map(e => ({
    id: e.assessment_series,
    name: e.assessment_series_name
  })))];

  // Fetch modules for selected series
  useEffect(() => {
    if (selectedSeries && candidateId) {
      // Fetch enrollment modules for this candidate and series
      candidateApi.getEnrollmentModules(candidateId, selectedSeries)
        .then(response => {
          setModules(response.data || []);
        })
        .catch(error => {
          console.error('Error fetching modules:', error);
          toast.error('Failed to load modules');
        });
    } else {
      setModules([]);
    }
  }, [selectedSeries, candidateId]);

  // Initialize marks when modules change
  useEffect(() => {
    if (modules.length > 0) {
      const initialMarks = {};
      modules.forEach(module => {
        initialMarks[module.id] = '';
      });
      setModuleMarks(initialMarks);
    }
  }, [modules]);

  const addResultsMutation = useMutation({
    mutationFn: (data) => candidateApi.addResults(candidateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-results', candidateId]);
      toast.success('Results added successfully!');
      onClose();
      resetForm();
    },
    onError: (error) => {
      const errorMsg = error.response?.data?.error || error.message;
      toast.error(`Failed to add results: ${errorMsg}`);
    },
  });

  const resetForm = () => {
    setSelectedSeries('');
    setModuleMarks({});
  };

  const handleMarkChange = (moduleId, value) => {
    // Validate mark is between 0-100 or -1 for missing
    const numValue = parseFloat(value);
    if (value === '' || value === '-1' || (numValue >= 0 && numValue <= 100)) {
      setModuleMarks(prev => ({
        ...prev,
        [moduleId]: value
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate at least one mark is entered
    const hasMarks = Object.values(moduleMarks).some(mark => mark !== '');
    if (!hasMarks) {
      toast.error('Please enter at least one mark');
      return;
    }

    // Prepare data
    const resultsData = {
      assessment_series: selectedSeries,
      results: Object.entries(moduleMarks)
        .filter(([_, mark]) => mark !== '')
        .map(([moduleId, mark]) => ({
          module_id: moduleId,
          mark: parseFloat(mark),
          type: 'practical' // Default to practical for modular
        }))
    };

    addResultsMutation.mutate(resultsData);
  };

  const handleCancel = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Add Results</h2>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Assessment Series */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series
            </label>
            <select
              value={selectedSeries}
              onChange={(e) => setSelectedSeries(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="">Select Assessment Series</option>
              {assessmentSeries.map((series) => (
                <option key={series.id} value={series.id}>
                  {series.name}
                </option>
              ))}
            </select>
            {selectedSeries && (
              <p className="mt-1 text-sm text-gray-500">
                Current candidate series: {assessmentSeries.find(s => s.id === parseInt(selectedSeries))?.name}
              </p>
            )}
          </div>

          {/* Assessment Month and Year (Read-only display) */}
          {selectedSeries && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Assessment Month
                </label>
                <input
                  type="text"
                  value={assessmentSeries.find(s => s.id === parseInt(selectedSeries))?.name.split(' ')[0] || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Assessment Year
                </label>
                <input
                  type="text"
                  value={assessmentSeries.find(s => s.id === parseInt(selectedSeries))?.name.split(' ')[1] || ''}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50"
                  readOnly
                />
              </div>
            </div>
          )}

          {/* Modules and Marks */}
          {selectedSeries && modules.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Modules & Marks (Practical)
              </label>
              <div className="space-y-3">
                {modules.map((module) => (
                  <div key={module.id} className="grid grid-cols-2 gap-4 items-center p-3 border border-gray-200 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">
                        {module.module_code} - {module.module_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {assessmentSeries.find(s => s.id === parseInt(selectedSeries))?.name}
                      </div>
                    </div>
                    <div>
                      <input
                        type="number"
                        min="-1"
                        max="100"
                        step="0.01"
                        value={moduleMarks[module.id] || ''}
                        onChange={(e) => handleMarkChange(module.id, e.target.value)}
                        placeholder="Enter mark (0-100, -1 for missing)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        0-100 or -1 for missing
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedSeries && modules.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No modules found for this assessment series
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
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
              loading={addResultsMutation.isPending}
              disabled={!selectedSeries || addResultsMutation.isPending}
            >
              Save Marks
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddResultsModal;
