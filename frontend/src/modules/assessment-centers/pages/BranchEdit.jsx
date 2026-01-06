import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save } from 'lucide-react';
import assessmentCenterApi from '../services/assessmentCenterApi';
import configurationApi from '@services/configurationApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const BranchEdit = () => {
  const { centerId, branchId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!branchId;

  const [formData, setFormData] = useState({
    assessment_center: centerId || '',
    branch_name: '',
    branch_code: '',
    district: '',
    village: '',
    is_active: true,
  });
  const [errors, setErrors] = useState({});

  // Fetch branch data if editing
  const { data: branchData, isLoading: branchLoading } = useQuery({
    queryKey: ['branch', branchId],
    queryFn: () => assessmentCenterApi.branches.getById(branchId),
    enabled: isEditing,
  });

  // Fetch center data for display
  const { data: centerData } = useQuery({
    queryKey: ['assessment-center', centerId || branchData?.data?.assessment_center],
    queryFn: () => assessmentCenterApi.getById(centerId || branchData?.data?.assessment_center),
    enabled: !!(centerId || branchData?.data?.assessment_center),
  });

  // Fetch districts
  const { data: districtsData } = useQuery({
    queryKey: ['districts'],
    queryFn: () => configurationApi.districts.getAll({ page_size: 200 }),
  });

  // Fetch villages based on selected district
  const { data: villagesData } = useQuery({
    queryKey: ['villages', formData.district],
    queryFn: () => configurationApi.villages.getAll({ district: formData.district, page_size: 500 }),
    enabled: !!formData.district,
  });

  const districts = districtsData?.data?.results || [];
  const villages = villagesData?.data?.results || [];
  const center = centerData?.data;

  // Populate form when editing
  useEffect(() => {
    if (branchData?.data) {
      const branch = branchData.data;
      setFormData({
        assessment_center: branch.assessment_center,
        branch_name: branch.branch_name || '',
        branch_code: branch.branch_code || '',
        district: branch.district || '',
        village: branch.village || '',
        is_active: branch.is_active ?? true,
      });
    }
  }, [branchData]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data) => assessmentCenterApi.branches.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['center-branches']);
      navigate(`/assessment-centers/${formData.assessment_center}`);
    },
    onError: (error) => {
      if (error.response?.data) {
        setErrors(error.response.data);
      }
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data) => assessmentCenterApi.branches.update(branchId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['center-branches']);
      queryClient.invalidateQueries(['branch', branchId]);
      navigate(`/assessment-centers/${formData.assessment_center}`);
    },
    onError: (error) => {
      if (error.response?.data) {
        setErrors(error.response.data);
      }
    },
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear error when field is changed
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrors({});

    if (isEditing) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  if (branchLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading branch data...</div>
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
          onClick={() => navigate(`/assessment-centers/${formData.assessment_center || centerId}`)}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Center
        </Button>

        <h1 className="text-2xl font-bold text-gray-900">
          {isEditing ? 'Edit Branch' : 'Add New Branch'}
        </h1>
        {center && (
          <p className="text-gray-600 mt-1">
            Center: {center.center_name} ({center.center_number})
          </p>
        )}
      </div>

      <Card>
        <Card.Content className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Branch Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Branch Name *
              </label>
              <input
                type="text"
                name="branch_name"
                value={formData.branch_name}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                  errors.branch_name ? 'border-red-500' : 'border-gray-300'
                }`}
                required
              />
              {errors.branch_name && (
                <p className="mt-1 text-sm text-red-600">{errors.branch_name}</p>
              )}
            </div>

            {/* Branch Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Branch Code *
              </label>
              <input
                type="text"
                name="branch_code"
                value={formData.branch_code}
                onChange={handleChange}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                  errors.branch_code ? 'border-red-500' : 'border-gray-300'
                }`}
                required
              />
              {errors.branch_code && (
                <p className="mt-1 text-sm text-red-600">{errors.branch_code}</p>
              )}
            </div>

            {/* District */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                District
              </label>
              <select
                name="district"
                value={formData.district}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Select District</option>
                {districts.map(district => (
                  <option key={district.id} value={district.id}>
                    {district.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Village */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Village
              </label>
              <select
                name="village"
                value={formData.village}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={!formData.district}
              >
                <option value="">Select Village</option>
                {villages.map(village => (
                  <option key={village.id} value={village.id}>
                    {village.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Active Status */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                Active
              </label>
            </div>

            {/* Error message */}
            {errors.non_field_errors && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{errors.non_field_errors}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(`/assessment-centers/${formData.assessment_center || centerId}`)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                <Save className="w-4 h-4 mr-2" />
                {isSubmitting ? 'Saving...' : (isEditing ? 'Update Branch' : 'Create Branch')}
              </Button>
            </div>
          </form>
        </Card.Content>
      </Card>
    </div>
  );
};

export default BranchEdit;
