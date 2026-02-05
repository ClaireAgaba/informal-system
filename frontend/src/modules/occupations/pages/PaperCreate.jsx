import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save } from 'lucide-react';
import occupationApi from '../services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { toast } from 'sonner';

const PaperCreate = () => {
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

  // Watch selected level for module fetching
  const selectedLevel = watch('level');

  // Fetch modules for selected level
  const { data: modulesData } = useQuery({
    queryKey: ['occupation-modules', occupationId, selectedLevel],
    queryFn: () => occupationApi.modules.getByOccupation(occupationId),
    enabled: !!occupationId && !!selectedLevel,
  });

  const modules = modulesData?.data?.results?.filter(m => m.level === parseInt(selectedLevel)) || [];

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => occupationApi.papers.create(data),
    onSuccess: () => {
      toast.success('Paper created successfully!');
      queryClient.invalidateQueries(['occupation-papers', occupationId]);
      navigate(`/occupations/${occupationId}`);
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to create paper';
      toast.error(errorMessage);
    },
  });

  const onSubmit = (data) => {
    const paperData = {
      ...data,
      occupation: occupationId,
      credit_units: data.credit_units ? parseInt(data.credit_units) : 0,
      is_active: data.is_active === 'true',
    };
    createMutation.mutate(paperData);
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
          <h1 className="text-2xl font-bold text-gray-900">Add Paper</h1>
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
                <h3 className="text-lg font-semibold text-gray-900">Paper Information</h3>
              </Card.Header>
              <Card.Content className="space-y-4">
                {/* Paper Code */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Paper Code *
                  </label>
                  <input
                    type="text"
                    {...register('paper_code', { required: 'Paper code is required' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., HD001"
                  />
                  {errors.paper_code && (
                    <p className="text-red-500 text-xs mt-1">{errors.paper_code.message}</p>
                  )}
                </div>

                {/* Paper Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Paper Name *
                  </label>
                  <input
                    type="text"
                    {...register('paper_name', { required: 'Paper name is required' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., Knotless"
                  />
                  {errors.paper_name && (
                    <p className="text-red-500 text-xs mt-1">{errors.paper_name.message}</p>
                  )}
                </div>

                {/* Paper Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Paper Type *
                  </label>
                  <select
                    {...register('paper_type', { required: 'Paper type is required' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select paper type</option>
                    <option value="theory">Theory</option>
                    <option value="practical">Practical</option>
                  </select>
                  {errors.paper_type && (
                    <p className="text-red-500 text-xs mt-1">{errors.paper_type.message}</p>
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

                {/* Module (optional, for Workers PAS) */}
                {selectedLevel && modules.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Module <span className="text-xs text-gray-500">(Optional - for Worker's PAS)</span>
                    </label>
                    <select
                      {...register('module')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="">No module (for Formal papers)</option>
                      {modules.map((module) => (
                        <option key={module.id} value={module.id}>
                          {module.module_code} - {module.module_name}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Select a module if this paper belongs to a specific module (Worker's PAS only)
                    </p>
                  </div>
                )}

                {/* Credit Units */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Credit Units (CU)
                  </label>
                  <input
                    type="number"
                    {...register('credit_units')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., 2"
                    min="0"
                    defaultValue="0"
                  />
                  <p className="mt-1 text-xs text-gray-500">Number of credit units for this paper</p>
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
                  Create Paper
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

export default PaperCreate;
