import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import assessmentCenterApi from '../services/assessmentCenterApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const AssessmentCenterCreate = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      center_number: '',
      center_name: '',
      assessment_category: '',
      district: '',
      village: '',
      contact_1: '',
      contact_2: '',
      has_branches: false,
      is_active: true,
    },
  });

  // Fetch districts for dropdown
  const { data: districtsData } = useQuery({
    queryKey: ['districts'],
    queryFn: async () => {
      const response = await fetch('/api/configurations/districts/');
      if (!response.ok) throw new Error('Failed to fetch districts');
      return response.json();
    },
  });

  // Fetch villages for dropdown
  const { data: villagesData } = useQuery({
    queryKey: ['villages'],
    queryFn: async () => {
      const response = await fetch('/api/configurations/villages/');
      if (!response.ok) throw new Error('Failed to fetch villages');
      return response.json();
    },
  });

  const districts = districtsData?.results || [];
  const villages = villagesData?.results || [];

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => assessmentCenterApi.create(data),
    onSuccess: (response) => {
      console.log('Create response:', response);
      queryClient.invalidateQueries(['assessment-centers']);
      toast.success('Assessment center created successfully!');
      
      // Navigate to the created center's view page or list
      const centerId = response?.data?.id || response?.id;
      if (centerId) {
        navigate(`/assessment-centers/${centerId}`);
      } else {
        navigate('/assessment-centers');
      }
    },
    onError: (error) => {
      console.error('Create error:', error);
      toast.error(`Failed to create center: ${error.response?.data?.error || error.message}`);
    },
  });

  const onSubmit = (formData) => {
    // Validate required fields
    if (!formData.center_number || !formData.center_name || !formData.assessment_category || !formData.district) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Clean up data
    const cleanedData = {
      center_number: formData.center_number,
      center_name: formData.center_name,
      assessment_category: formData.assessment_category,
      district: parseInt(formData.district),
      village: formData.village ? parseInt(formData.village) : null,
      contact_1: formData.contact_1 || '',
      contact_2: formData.contact_2 || '',
      has_branches: formData.has_branches || false,
      is_active: formData.is_active !== false,
    };

    console.log('Creating center:', cleanedData);
    createMutation.mutate(cleanedData);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/assessment-centers')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to List
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create New Assessment Center</h1>
            <p className="text-gray-600 mt-1">Add a new assessment center to the system</p>
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
                <h3 className="text-lg font-semibold text-gray-900">Center Details</h3>
              </Card.Header>
              <Card.Content className="space-y-6">
                {/* Center Number */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Center Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('center_number', { required: 'Center number is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., UVT001"
                  />
                  {errors.center_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.center_number.message}</p>
                  )}
                </div>

                {/* Center Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Center Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('center_name', { required: 'Center name is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., Kampala Vocational Training Center"
                  />
                  {errors.center_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.center_name.message}</p>
                  )}
                </div>

                {/* Assessment Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Assessment Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    {...register('assessment_category', { required: 'Category is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select category</option>
                    <option value="VTI">Vocational Training Institute</option>
                    <option value="TTI">Technical Training Institute</option>
                    <option value="workplace">Workplace</option>
                  </select>
                  {errors.assessment_category && (
                    <p className="mt-1 text-sm text-red-600">{errors.assessment_category.message}</p>
                  )}
                </div>

                {/* District */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    District <span className="text-red-500">*</span>
                  </label>
                  <select
                    {...register('district', { required: 'District is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select district</option>
                    {districts.map((district) => (
                      <option key={district.id} value={district.id}>
                        {district.name}
                      </option>
                    ))}
                  </select>
                  {errors.district && (
                    <p className="mt-1 text-sm text-red-600">{errors.district.message}</p>
                  )}
                </div>

                {/* Village */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Village
                  </label>
                  <select
                    {...register('village')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select village (optional)</option>
                    {villages.map((village) => (
                      <option key={village.id} value={village.id}>
                        {village.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Contact 1 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact 1
                  </label>
                  <input
                    type="text"
                    {...register('contact_1')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., 0700123456"
                  />
                </div>

                {/* Contact 2 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact 2
                  </label>
                  <input
                    type="text"
                    {...register('contact_2')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="e.g., 0700654321"
                  />
                </div>

                {/* Has Branches */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('has_branches')}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label className="ml-2 text-sm text-gray-700">
                    This center has branches
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
                  Create Center
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate('/assessment-centers')}
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

export default AssessmentCenterCreate;
