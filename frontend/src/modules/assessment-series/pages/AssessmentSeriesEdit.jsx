import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import assessmentSeriesApi from '../services/assessmentSeriesApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const AssessmentSeriesEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isNewSeries = id === 'new';

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm();

  // Fetch series details if editing
  const { data, isLoading } = useQuery({
    queryKey: ['assessment-series', id],
    queryFn: () => assessmentSeriesApi.getById(id),
    enabled: !isNewSeries,
  });

  const series = data?.data;

  // Populate form
  useEffect(() => {
    if (series) {
      reset({
        name: series.name,
        start_date: series.start_date,
        end_date: series.end_date,
        date_of_release: series.date_of_release,
        completion_year: series.completion_year || '',
        quarter: series.quarter || '',
        is_current: series.is_current,
        results_released: series.results_released,
        dont_charge: series.dont_charge,
        is_active: series.is_active,
      });
    }
  }, [series, reset]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data) => assessmentSeriesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-series']);
      toast.success('Assessment series updated successfully!');
      navigate(`/assessment-series/${id}`);
    },
    onError: (error) => {
      toast.error(`Failed to update series: ${error.message}`);
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => assessmentSeriesApi.create(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['assessment-series']);
      toast.success('Assessment series created successfully!');
      navigate(`/assessment-series/${response.data.id}`);
    },
    onError: (error) => {
      toast.error(`Failed to create series: ${error.message}`);
    },
  });

  const onSubmit = (formData) => {
    const cleanedData = {
      name: formData.name,
      start_date: formData.start_date,
      end_date: formData.end_date,
      date_of_release: formData.date_of_release,
      completion_year: formData.completion_year || '',
      quarter: formData.quarter || '',
      is_current: formData.is_current || false,
      results_released: formData.results_released || false,
      dont_charge: formData.dont_charge || false,
      is_active: formData.is_active !== false,
    };

    if (isNewSeries) {
      createMutation.mutate(cleanedData);
    } else {
      updateMutation.mutate(cleanedData);
    }
  };

  if (isLoading && !isNewSeries) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading series details...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(isNewSeries ? '/assessment-series' : `/assessment-series/${id}`)}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <h1 className="text-2xl font-bold text-gray-900">
          {isNewSeries ? 'Create New Assessment Series' : 'Edit Assessment Series'}
        </h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold text-gray-900">Series Details</h3>
              </Card.Header>
              <Card.Content className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Series Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('name', { required: 'Series name is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., December 2025 Series"
                  />
                  {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    {...register('start_date', { required: 'Start date is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.start_date && <p className="mt-1 text-sm text-red-600">{errors.start_date.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    {...register('end_date', { required: 'End date is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.end_date && <p className="mt-1 text-sm text-red-600">{errors.end_date.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Results Release Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    {...register('date_of_release', { required: 'Results release date is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.date_of_release && <p className="mt-1 text-sm text-red-600">{errors.date_of_release.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Completion Year
                  </label>
                  <input
                    type="text"
                    {...register('completion_year')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., November, 2025"
                  />
                  <p className="mt-1 text-xs text-gray-500">Optional: Completion year/period for certificates</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fiscal Quarter
                  </label>
                  <select
                    {...register('quarter')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select Quarter</option>
                    <option value="Q1">Q1 (July - September)</option>
                    <option value="Q2">Q2 (October - December)</option>
                    <option value="Q3">Q3 (January - March)</option>
                    <option value="Q4">Q4 (April - June)</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Uganda fiscal year quarter this series falls under</p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('is_current')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">Set as current assessment series</label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('results_released')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">Results released</label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('dont_charge')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">Don't charge candidates</label>
                </div>

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
                  loading={updateMutation.isPending || createMutation.isPending}
                  disabled={!isDirty || updateMutation.isPending || createMutation.isPending}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isNewSeries ? 'Create Series' : 'Save Changes'}
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate(isNewSeries ? '/assessment-series' : `/assessment-series/${id}`)}
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

export default AssessmentSeriesEdit;
