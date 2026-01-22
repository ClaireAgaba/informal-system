import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { X, Calendar } from 'lucide-react';
import candidateApi from '../services/candidateApi';
import assessmentSeriesApi from '@modules/assessment-series/services/assessmentSeriesApi';
import Button from '@shared/components/Button';

const ChangeSeriesModal = ({ candidate, onClose }) => {
  const queryClient = useQueryClient();
  const [selectedSeries, setSelectedSeries] = useState('');

  // Fetch all assessment series
  const { data: seriesData, isLoading } = useQuery({
    queryKey: ['assessment-series-list'],
    queryFn: () => assessmentSeriesApi.getAll(),
  });

  const seriesList = seriesData?.data?.results || seriesData?.data || [];

  // Change series mutation
  const changeSeriesMutation = useMutation({
    mutationFn: (newSeriesId) => candidateApi.changeSeries(candidate.id, newSeriesId),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['candidate', candidate.id]);
      queryClient.invalidateQueries(['candidate-enrollments', candidate.id]);
      toast.success(response.data.message);
      onClose();
    },
    onError: (error) => {
      toast.error(error.response?.data?.error || 'Failed to change series');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedSeries) {
      toast.error('Please select an assessment series');
      return;
    }
    changeSeriesMutation.mutate(selectedSeries);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Change Assessment Series
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
                This will move all enrollments and results to the selected series.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Select New Assessment Series
              </label>
              {isLoading ? (
                <div className="text-sm text-gray-500">Loading series...</div>
              ) : (
                <select
                  value={selectedSeries}
                  onChange={(e) => setSelectedSeries(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">-- Select Series --</option>
                  {seriesList.map((series) => (
                    <option key={series.id} value={series.id}>
                      {series.name} {series.is_active ? '(Active)' : ''}
                    </option>
                  ))}
                </select>
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
              loading={changeSeriesMutation.isPending}
              disabled={changeSeriesMutation.isPending || !selectedSeries}
            >
              Change Series
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangeSeriesModal;
