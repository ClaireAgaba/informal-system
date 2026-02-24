import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import assessmentCenterApi from '../services/assessmentCenterApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const AssessmentCenterEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isNewCenter = id === 'new';
  
  console.log('AssessmentCenterEdit loaded:', { id, isNewCenter });

  const fetchAllPagesFetch = async (baseUrl, params = {}, page = 1, acc = []) => {
    const url = new URL(baseUrl, window.location.origin);
    const search = new URLSearchParams(params);
    search.set('page', String(page));
    search.set('page_size', '1000');
    url.search = search.toString();

    const response = await fetch(url.toString());
    if (!response.ok) throw new Error('Failed to fetch data');
    const data = await response.json();

    if (Array.isArray(data)) {
      return [...acc, ...data];
    }

    const results = data?.results || [];
    const nextAcc = [...acc, ...results];

    if (!data?.next) {
      return nextAcc;
    }

    return fetchAllPagesFetch(baseUrl, params, page + 1, nextAcc);
  };

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isDirty },
  } = useForm();

  // Fetch center details if editing
  const { data, isLoading } = useQuery({
    queryKey: ['assessment-center', id],
    queryFn: () => assessmentCenterApi.getById(id),
    enabled: !isNewCenter && !!id && id !== 'new',
  });

  // Fetch districts for dropdown
  const { data: districtsData } = useQuery({
    queryKey: ['districts'],
    queryFn: async () => {
      return fetchAllPagesFetch('/api/configurations/districts/');
    },
  });

  // Fetch villages for dropdown
  const { data: villagesData } = useQuery({
    queryKey: ['villages'],
    queryFn: async () => {
      return fetchAllPagesFetch('/api/configurations/villages/');
    },
  });

  const center = data?.data;
  const districts = districtsData || [];
  const villages = villagesData || [];

  // Populate form when data is loaded (wait for districts to load first)
  useEffect(() => {
    if (center && !isNewCenter && districts.length > 0) {
      reset({
        center_number: center.center_number,
        center_name: center.center_name,
        assessment_category: center.assessment_category,
        district: center.district ? String(center.district) : '',
        village: center.village ? String(center.village) : '',
        contact_1: center.contact_1 || '',
        contact_2: center.contact_2 || '',
        has_branches: center.has_branches,
        is_active: center.is_active,
      });
    } else if (isNewCenter) {
      // Set default values for new center
      reset({
        center_number: '',
        center_name: '',
        assessment_category: '',
        district: '',
        village: '',
        contact_1: '',
        contact_2: '',
        has_branches: false,
        is_active: true,
      });
    }
  }, [center, reset, isNewCenter, districts.length]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data) => assessmentCenterApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['assessment-center', id]);
      queryClient.invalidateQueries(['assessment-centers']);
      toast.success('Assessment center updated successfully!');
      navigate(`/assessment-centers/${id}`);
    },
    onError: (error) => {
      toast.error(`Failed to update center: ${error.message}`);
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => assessmentCenterApi.create(data),
    onSuccess: (response) => {
      console.log('Create response:', response);
      queryClient.invalidateQueries(['assessment-centers']);
      toast.success('Assessment center created successfully!');
      // Handle different response structures
      const centerId = response?.data?.id || response?.id;
      console.log('Extracted center ID:', centerId);
      if (centerId) {
        navigate(`/assessment-centers/${centerId}`);
      } else {
        console.warn('No center ID found in response, navigating to list');
        // Fallback to list if ID is not available
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
      district: parseInt(formData.district), // Required field
      village: formData.village ? parseInt(formData.village) : null,
      contact_1: formData.contact_1 || '',
      contact_2: formData.contact_2 || '',
      has_branches: formData.has_branches || false,
      is_active: formData.is_active !== false,
    };

    console.log('Submitting form:', { isNewCenter, id, cleanedData });

    if (isNewCenter) {
      createMutation.mutate(cleanedData);
    } else {
      updateMutation.mutate(cleanedData);
    }
  };

  if (isLoading && !isNewCenter) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading center details...</div>
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
          onClick={() => {
            if (isNewCenter) {
              navigate('/assessment-centers');
            } else {
              navigate(`/assessment-centers/${id}`);
            }
          }}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isNewCenter ? 'Create New Assessment Center' : 'Edit Assessment Center'}
            </h1>
            <p className="text-gray-600 mt-1">
              {isNewCenter
                ? 'Add a new assessment center to the system'
                : `Editing: ${center?.center_name}`}
            </p>
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
                  loading={updateMutation.isPending || createMutation.isPending}
                  disabled={!isDirty || updateMutation.isPending || createMutation.isPending}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isNewCenter ? 'Create Center' : 'Save Changes'}
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => {
                    if (isNewCenter) {
                      navigate('/assessment-centers');
                    } else {
                      navigate(`/assessment-centers/${id}`);
                    }
                  }}
                >
                  Cancel
                </Button>

                {!isNewCenter && (
                  <div className="pt-4 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                      Last updated: {new Date(center?.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </Card.Content>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default AssessmentCenterEdit;
