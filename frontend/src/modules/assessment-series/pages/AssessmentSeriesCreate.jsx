import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import assessmentSeriesApi from '../services/assessmentSeriesApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const AssessmentSeriesCreate = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: '',
      start_date: '',
      end_date: '',
      date_of_release: '',
      is_current: false,
      results_released: false,
      is_active: true,
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => assessmentSeriesApi.create(data),
    onSuccess: (response) => {
      console.log('Create response:', response);
      queryClient.invalidateQueries(['assessment-series']);
      toast.success('Assessment series created successfully!');
      
      // Navigate to the created series view page or list
      const seriesId = response?.data?.id || response?.id;
      if (seriesId) {
        navigate(`/assessment-series/${seriesId}`);
      } else {
        navigate('/assessment-series');
      }
    },
    onError: (error) => {
      console.error('Create error:', error);
      toast.error(`Failed to create series: ${error.response?.data?.error || error.message}`);
    },
  });

  const onSubmit = (formData) => {
    // Validate required fields
    if (!formData.name || !formData.start_date || !formData.end_date) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Clean up data
    const cleanedData = {
      name: formData.name,
      start_date: formData.start_date,
      end_date: formData.end_date,
      date_of_release: formData.date_of_release || null,
      is_current: formData.is_current || false,
      results_released: formData.results_released || false,
      dont_charge: formData.dont_charge || false,
      is_active: formData.is_active !== false,
    };

    console.log('Creating assessment series:', cleanedData);
    createMutation.mutate(cleanedData);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/assessment-series')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to List
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Assessment Series</h1>
            <p className="text-gray-600 mt-1">Add a new assessment series to the system</p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold text-gray-900">Series Details</h3>
              </Card.Header>
              <Card.Content className="space-y-6">
                {/* Series Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Series Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('name', { required: 'Series name is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., January 2025 Assessment"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                {/* Start Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    {...register('start_date', { required: 'Start date is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.start_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.start_date.message}</p>
                  )}
                </div>

                {/* End Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    {...register('end_date', { required: 'End date is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.end_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.end_date.message}</p>
                  )}
                </div>

                {/* Date of Release */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date of Release
                  </label>
                  <input
                    type="date"
                    {...register('date_of_release')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Optional: When results will be released</p>
                </div>

                {/* Is Current */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('is_current')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    Set as current assessment series
                  </label>
                </div>

                {/* Results Released */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('results_released')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    Results released
                  </label>
                </div>

                {/* Don't Charge */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('dont_charge')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    Don't charge candidates
                  </label>
                </div>

                {/* Is Active */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('is_active')}
                    defaultChecked={true}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">Active</label>
                </div>
              </Card.Content>
            </Card>
          </div>

          {/* Actions Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
              </Card.Header>
              <Card.Content className="space-y-3">
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  className="w-full"
                  loading={createMutation.isPending}
                  disabled={createMutation.isPending}
                >
                  <Save className="w-4 h-4 mr-2" />
                  Create Series
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate('/assessment-series')}
                >
                  Cancel
                </Button>
              </Card.Content>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default AssessmentSeriesCreate;
