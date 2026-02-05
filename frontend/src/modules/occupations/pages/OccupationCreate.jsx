import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import occupationApi from '../services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const OccupationCreate = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: {
      occ_code: '',
      occ_name: '',
      occ_category: '',
      award: '',
      award_modular: '',
      sector: '',
      has_modular: false,
      is_active: true,
    },
  });

  // Watch category and has_modular for conditional fields
  const watchCategory = watch('occ_category');
  const watchHasModular = watch('has_modular');

  // Fetch sectors for dropdown
  const { data: sectorsData } = useQuery({
    queryKey: ['sectors'],
    queryFn: () => occupationApi.sectors.getAll(),
  });

  const sectors = sectorsData?.data?.results || [];

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => occupationApi.create(data),
    onSuccess: (response) => {
      console.log('Create response:', response);
      queryClient.invalidateQueries(['occupations']);
      toast.success('Occupation created successfully!');
      
      // Navigate to the created occupation's view page or list
      const occupationId = response?.data?.id || response?.id;
      if (occupationId) {
        navigate(`/occupations/${occupationId}`);
      } else {
        navigate('/occupations');
      }
    },
    onError: (error) => {
      console.error('Create error:', error);
      toast.error(`Failed to create occupation: ${error.response?.data?.error || error.message}`);
    },
  });

  const onSubmit = (formData) => {
    // Validate required fields
    if (!formData.occ_code || !formData.occ_name || !formData.occ_category) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Clean up data
    const cleanedData = {
      occ_code: formData.occ_code,
      occ_name: formData.occ_name,
      occ_category: formData.occ_category,
      award: formData.occ_category === 'formal' ? (formData.award || null) : null,
      award_modular: formData.has_modular ? (formData.award_modular || null) : null,
      sector: formData.sector ? parseInt(formData.sector) : null,
      has_modular: formData.has_modular || false,
      is_active: formData.is_active !== false,
    };

    console.log('Creating occupation:', cleanedData);
    createMutation.mutate(cleanedData);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/occupations')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to List
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Occupation</h1>
            <p className="text-gray-600 mt-1">Add a new occupation to the system</p>
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
                <h3 className="text-lg font-semibold text-gray-900">Occupation Details</h3>
              </Card.Header>
              <Card.Content className="space-y-6">
                {/* Occupation Code */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Occupation Code <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('occ_code', { required: 'Occupation code is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., OCC001"
                  />
                  {errors.occ_code && (
                    <p className="mt-1 text-sm text-red-600">{errors.occ_code.message}</p>
                  )}
                </div>

                {/* Occupation Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Occupation Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('occ_name', { required: 'Occupation name is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., Carpentry"
                  />
                  {errors.occ_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.occ_name.message}</p>
                  )}
                </div>

                {/* Occupation Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Occupation Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    {...register('occ_category', { required: 'Category is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select category</option>
                    <option value="formal">Formal</option>
                    <option value="workers_pas">Worker's PAS</option>
                  </select>
                  {errors.occ_category && (
                    <p className="mt-1 text-sm text-red-600">{errors.occ_category.message}</p>
                  )}
                </div>

                {/* Award - Only for Formal category */}
                {watchCategory === 'formal' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Award (Full Occupation)
                    </label>
                    <input
                      type="text"
                      {...register('award')}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="e.g., Uganda Vocational Qualification"
                    />
                    <p className="mt-1 text-xs text-gray-500">Award title for full occupation candidates (used on transcripts)</p>
                  </div>
                )}

                {/* Award Modular - Only when has_modular is checked */}
                {watchCategory === 'formal' && watchHasModular && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Award (Modular)
                    </label>
                    <input
                      type="text"
                      {...register('award_modular')}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="e.g., Statement of Attainment"
                    />
                    <p className="mt-1 text-xs text-gray-500">Award title for modular candidates (used on transcripts)</p>
                  </div>
                )}

                {/* Sector */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sector
                  </label>
                  <select
                    {...register('sector')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select sector (optional)</option>
                    {sectors.map((sector) => (
                      <option key={sector.id} value={sector.id}>
                        {sector.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Has Modular */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('has_modular')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    Has modular structure
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
                  Create Occupation
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate('/occupations')}
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

export default OccupationCreate;
