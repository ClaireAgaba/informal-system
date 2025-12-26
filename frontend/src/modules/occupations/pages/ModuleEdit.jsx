import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Trash2, Plus, X } from 'lucide-react';
import occupationApi from '../services/occupationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { toast } from 'sonner';
import { useEffect, useState } from 'react';

const ModuleEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { register, handleSubmit, reset, formState: { errors } } = useForm();

  // Fetch module details
  const { data: moduleData, isLoading } = useQuery({
    queryKey: ['occupation-module', id],
    queryFn: () => occupationApi.modules.getById(id),
    enabled: !!id,
  });

  // Fetch levels for the occupation
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', moduleData?.data?.occupation],
    queryFn: () => occupationApi.levels.getByOccupation(moduleData?.data?.occupation),
    enabled: !!moduleData?.data?.occupation,
  });

  const module = moduleData?.data;
  const levels = levelsData?.data?.results || [];

  // LWA state and queries
  const [newLwaName, setNewLwaName] = useState('');
  const [showLwaInput, setShowLwaInput] = useState(false);

  // Fetch LWAs for this module
  const { data: lwasData } = useQuery({
    queryKey: ['module-lwas', id],
    queryFn: () => occupationApi.lwas.getByModule(id),
    enabled: !!id,
  });

  const lwas = lwasData?.data?.results || [];

  // Reset form when module data is loaded
  useEffect(() => {
    if (module) {
      reset({
        module_code: module.module_code,
        module_name: module.module_name,
        level: module.level,
        is_active: module.is_active ? 'true' : 'false',
      });
    }
  }, [module, reset]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data) => occupationApi.modules.update(id, data),
    onSuccess: () => {
      toast.success('Module updated successfully!');
      queryClient.invalidateQueries(['occupation-module', id]);
      queryClient.invalidateQueries(['occupation-modules']);
      navigate(`/occupations/${module.occupation}`);
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to update module';
      toast.error(errorMessage);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => occupationApi.modules.delete(id),
    onSuccess: () => {
      toast.success('Module deleted successfully!');
      queryClient.invalidateQueries(['occupation-modules']);
      navigate(`/occupations/${module.occupation}`);
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to delete module';
      toast.error(errorMessage);
    },
  });

  // LWA mutations
  const createLwaMutation = useMutation({
    mutationFn: (data) => occupationApi.lwas.create(data),
    onSuccess: () => {
      toast.success('LWA added successfully!');
      queryClient.invalidateQueries(['module-lwas', id]);
      setNewLwaName('');
      setShowLwaInput(false);
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to add LWA';
      toast.error(errorMessage);
    },
  });

  const deleteLwaMutation = useMutation({
    mutationFn: (lwaId) => occupationApi.lwas.delete(lwaId),
    onSuccess: () => {
      toast.success('LWA deleted successfully!');
      queryClient.invalidateQueries(['module-lwas', id]);
    },
    onError: (error) => {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to delete LWA';
      toast.error(errorMessage);
    },
  });

  const onSubmit = (data) => {
    const moduleData = {
      ...data,
      occupation: module.occupation,
      is_active: data.is_active === 'true',
    };
    updateMutation.mutate(moduleData);
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this module? This action cannot be undone.')) {
      deleteMutation.mutate();
    }
  };

  const handleAddLwa = () => {
    if (!newLwaName.trim()) {
      toast.error('Please enter an LWA name');
      return;
    }
    createLwaMutation.mutate({
      module: id,
      lwa_name: newLwaName.trim(),
    });
  };

  const handleDeleteLwa = (lwaId) => {
    if (window.confirm('Are you sure you want to delete this LWA?')) {
      deleteLwaMutation.mutate(lwaId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading module details...</div>
      </div>
    );
  }

  if (!module) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Module not found</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(`/occupations/${module.occupation}`)}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Occupation
        </Button>

        <div>
          <h1 className="text-2xl font-bold text-gray-900">Edit Module</h1>
          <p className="text-gray-600 mt-1">
            {module.occupation_name} ({module.occupation_code})
          </p>
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

                {/* Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status *
                  </label>
                  <select
                    {...register('is_active')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                  </select>
                </div>

                {/* Learning Working Assignments (LWAs) */}
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-medium text-gray-700">
                      Learning Working Assignments (LWAs)
                    </label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setShowLwaInput(!showLwaInput)}
                    >
                      <Plus className="w-3 h-3 mr-1" />
                      Add LWA
                    </Button>
                  </div>

                  {showLwaInput && (
                    <div className="mb-3 flex gap-2">
                      <input
                        type="text"
                        value={newLwaName}
                        onChange={(e) => setNewLwaName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddLwa()}
                        placeholder="Enter LWA name"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={handleAddLwa}
                        disabled={createLwaMutation.isPending}
                      >
                        Add
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setShowLwaInput(false);
                          setNewLwaName('');
                        }}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  )}

                  {lwas.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">No LWAs added yet</p>
                  ) : (
                    <div className="space-y-2">
                      {lwas.map((lwa) => (
                        <div
                          key={lwa.id}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-200"
                        >
                          <span className="text-sm text-gray-900">{lwa.lwa_name}</span>
                          <button
                            type="button"
                            onClick={() => handleDeleteLwa(lwa.id)}
                            className="text-red-600 hover:text-red-800"
                            disabled={deleteLwaMutation.isPending}
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
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
                  disabled={updateMutation.isPending}
                  loading={updateMutation.isPending}
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate(`/occupations/${module.occupation}`)}
                >
                  Cancel
                </Button>
                <div className="pt-3 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="danger"
                    size="md"
                    className="w-full"
                    onClick={handleDelete}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Module
                  </Button>
                </div>
              </Card.Content>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ModuleEdit;
