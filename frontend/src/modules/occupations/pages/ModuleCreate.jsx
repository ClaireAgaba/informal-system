import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save } from 'lucide-react';
import occupationApi from '../services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { toast } from 'sonner';

const ModuleCreate = () => {
  const { occupationId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { register, handleSubmit, watch, formState: { errors } } = useForm();

  // Fetch occupation details
  const { data: occupationData } = useQuery({
    queryKey: ['occupation', occupationId],
    queryFn: () => occupationApi.getById(occupationId),
    enabled: !!occupationId,
  });

  // Fetch levels for this occupation
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', occupationId],
    queryFn: () => occupationApi.levels.getByOccupation(occupationId),
    enabled: !!occupationId,
  });

  const occupation = occupationData?.data;
  const levels = levelsData?.data?.results || [];

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => occupationApi.modules.create(data),
    onSuccess: () => {
      toast.success('Module created successfully!');
      queryClient.invalidateQueries(['occupation-modules', occupationId]);
      navigate(`/occupations/${occupationId}`);
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to create module';
      toast.error(errorMessage);
    },
  });

  const onSubmit = (data) => {
    const moduleData = {
      ...data,
      occupation: occupationId,
      credit_units: data.credit_units ? parseInt(data.credit_units) : 0,
      is_active: data.is_active === 'true',
    };
    createMutation.mutate(moduleData);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/occupations/${occupationId}`)}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Occupation
        </Button>

        <div>
          <h1 className="text-2xl font-bold text-gray-900">Add Module</h1>
          {occupation && (
            <p className="text-gray-600 mt-1">
              {occupation.occ_name} ({occupation.occ_code})
            </p>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form */}
          <div className="lg:col-span-2">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold text-gray-900">Module Information</h3>
              </Card.Header>
              <Card.Content className="space-y-4">
                {/* Module Code */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Module Code *
                  </label>
                  <input
                    type="text"
                    {...register('module_code', { required: 'Module code is required' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., HD01"
                  />
                  {errors.module_code && (
                    <p className="text-red-500 text-xs mt-1">{errors.module_code.message}</p>
                  )}
                </div>

                {/* Module Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Module Name *
                  </label>
                  <input
                    type="text"
                    {...register('module_name', { required: 'Module name is required' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., Hair Styling"
                  />
                  {errors.module_name && (
                    <p className="text-red-500 text-xs mt-1">{errors.module_name.message}</p>
                  )}
                </div>

                {/* Level */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Level *
                  </label>
                  <select
                    {...register('level', { required: 'Level is required' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select level</option>
                    {levels.map((level) => (
                      <option key={level.id} value={level.id}>
                        {level.level_name}
                      </option>
                    ))}
                  </select>
                  {errors.level && (
                    <p className="text-red-500 text-xs mt-1">{errors.level.message}</p>
                  )}
                </div>

                {/* Credit Units */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Credit Units (CU)
                  </label>
                  <input
                    type="number"
                    {...register('credit_units')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., 3"
                    min="0"
                    defaultValue="0"
                  />
                  <p className="mt-1 text-xs text-gray-500">Number of credit units for this module</p>
                </div>

                {/* Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status *
                  </label>
                  <select
                    {...register('is_active')}
                    defaultValue="true"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                  </select>
                </div>

                {/* Worker's PAS Booklet Content */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-3">
                  <div>
                    <h4 className="text-sm font-semibold text-amber-900">Worker's PAS Booklet Content</h4>
                    <p className="text-xs text-amber-700">Optional. Used when this module appears as a Test Area inside a Worker's PAS booklet.</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <textarea
                      rows={3}
                      {...register('wp_description')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="e.g., The Worker has acquired adequate knowledge and skills to construct foundations/substructures e.g.;"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Competence Items (one per line)</label>
                    <textarea
                      rows={5}
                      {...register('wp_competence_items')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-xs"
                      placeholder={'Interpreting drawings\nSetting profiles\nDetermining levels\nStrip foundation'}
                    />
                    <p className="mt-1 text-xs text-gray-500">Each non-empty line becomes a bullet point on the test area page.</p>
                  </div>
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
                  disabled={createMutation.isPending}
                  loading={createMutation.isPending}
                >
                  <Save className="w-4 h-4 mr-2" />
                  Create Module
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate(`/occupations/${occupationId}`)}
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

export default ModuleCreate;
