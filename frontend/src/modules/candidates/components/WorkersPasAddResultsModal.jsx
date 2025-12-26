import React, { useState, useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Button from '@shared/components/Button';
import axios from 'axios';

const WorkersPasAddResultsModal = ({ isOpen, onClose, candidate, enrollments }) => {
  const queryClient = useQueryClient();
  const [selectedSeries, setSelectedSeries] = useState('');
  const [paperMarks, setPaperMarks] = useState({});
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Get unique assessment series from enrollments
  const assessmentSeries = enrollments && enrollments.length > 0
    ? [...new Map(enrollments.map(e => [e.assessment_series, { id: e.assessment_series, name: e.assessment_series_name }])).values()]
    : [];

  // Fetch enrolled papers for selected series
  useEffect(() => {
    if (selectedSeries && candidate?.id) {
      setLoading(true);
      // Get the enrollment for this series
      const enrollment = enrollments.find(e => e.assessment_series === parseInt(selectedSeries));
      
      if (enrollment && enrollment.papers && enrollment.papers.length > 0) {
        setPapers(enrollment.papers);
        
        // Initialize marks
        const initialMarks = {};
        enrollment.papers.forEach(paper => {
          initialMarks[paper.paper] = {
            mark: '',
            status: 'normal'
          };
        });
        setPaperMarks(initialMarks);
      } else {
        setPapers([]);
        setPaperMarks({});
      }
      setLoading(false);
    } else {
      setPapers([]);
      setPaperMarks({});
    }
  }, [selectedSeries, candidate, enrollments]);

  const addResultsMutation = useMutation({
    mutationFn: async (data) => {
      const response = await axios.post('/api/results/workers-pas/add/', {
        candidate_id: candidate.id,
        ...data
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['candidate-results', candidate.id]);
      queryClient.invalidateQueries(['workers-pas-results', candidate.id]);
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
    setPaperMarks({});
  };

  const handleMarkChange = (paperId, value) => {
    // Validate mark is between 0-100 or -1 for missing
    const numValue = parseFloat(value);
    if (value === '' || value === '-1' || (numValue >= 0 && numValue <= 100)) {
      setPaperMarks(prev => ({
        ...prev,
        [paperId]: {
          ...prev[paperId],
          mark: value
        }
      }));
    }
  };

  const handleStatusChange = (paperId, status) => {
    setPaperMarks(prev => ({
      ...prev,
      [paperId]: {
        ...prev[paperId],
        status
      }
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!selectedSeries) {
      toast.error('Please select an assessment series');
      return;
    }

    // Validate at least one mark is entered
    const hasMarks = Object.values(paperMarks).some(data => data.mark !== '');
    if (!hasMarks) {
      toast.error('Please enter at least one mark');
      return;
    }

    // Prepare data
    const resultsData = {
      assessment_series: selectedSeries,
      results: Object.entries(paperMarks)
        .filter(([_, data]) => data.mark !== '')
        .map(([paperId, data]) => ({
          paper_id: parseInt(paperId),
          mark: parseFloat(data.mark),
          status: data.status
        }))
    };

    addResultsMutation.mutate(resultsData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Add Worker's PAS Results</h2>
            <p className="text-sm text-gray-600 mt-1">
              {candidate?.full_name} - {candidate?.registration_number}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">Worker's PAS Assessment</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>All assessments are <strong>Practical</strong> only</li>
                  <li>Enter marks between <strong>0-100</strong></li>
                  <li>Use <strong>-1</strong> for missing/absent candidates</li>
                  <li>Pass mark: <strong>65%</strong></li>
                </ul>
              </div>
            </div>
          </div>

          {/* Assessment Series Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedSeries}
              onChange={(e) => setSelectedSeries(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            >
              <option value="">Select assessment series</option>
              {assessmentSeries.map((series) => (
                <option key={series.id} value={series.id}>
                  {series.name}
                </option>
              ))}
            </select>
          </div>

          {/* Papers List */}
          {selectedSeries && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Enter Marks for Enrolled Papers
              </label>
              
              {loading ? (
                <div className="text-center py-8 text-gray-500">Loading papers...</div>
              ) : papers.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No papers enrolled for this assessment series
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Level
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Module
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Paper
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Mark (0-100)
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {papers.map((paper) => (
                        <tr key={paper.paper} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {paper.level_name || '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            <div>
                              <div className="font-medium">{paper.module_code || '-'}</div>
                              <div className="text-xs text-gray-500">{paper.module_name || '-'}</div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            <div>
                              <div className="font-medium">{paper.paper_code}</div>
                              <div className="text-xs text-gray-500">{paper.paper_name}</div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                              Practical
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <input
                              type="number"
                              step="0.01"
                              min="-1"
                              max="100"
                              value={paperMarks[paper.paper]?.mark || ''}
                              onChange={(e) => handleMarkChange(paper.paper, e.target.value)}
                              className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                              placeholder="0-100"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <select
                              value={paperMarks[paper.paper]?.status || 'normal'}
                              onChange={(e) => handleStatusChange(paper.paper, e.target.value)}
                              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
                            >
                              <option value="normal">Normal</option>
                              <option value="retake">Retake</option>
                              <option value="missing">Missing</option>
                            </select>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={addResultsMutation.isPending || !selectedSeries || papers.length === 0}
            >
              {addResultsMutation.isPending ? 'Saving...' : 'Save Results'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WorkersPasAddResultsModal;
