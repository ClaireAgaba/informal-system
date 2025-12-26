import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import userApi from '../../services/userApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';

const StaffEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isNew = id === 'new';

  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['staff', id],
    queryFn: () => userApi.staff.getById(id),
    enabled: !isNew,
  });

  const { data: departmentsData } = useQuery({
    queryKey: ['departments'],
    queryFn: () => userApi.departments.getAll(),
  });

  const staff = data?.data;
  const departments = departmentsData?.data?.results || [];

  useEffect(() => {
    if (staff) {
      reset({
        full_name: staff.full_name,
        email: staff.email,
        contact: staff.contact,
        department: staff.department || '',
        account_status: staff.account_status,
      });
    }
  }, [staff, reset]);

  const updateMutation = useMutation({
    mutationFn: (data) => userApi.staff.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['staff']);
      toast.success('Staff member updated successfully!');
      navigate(`/users/staff/${id}`);
    },
    onError: (error) => {
      toast.error(`Failed to update: ${error.message}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: (data) => userApi.staff.create(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries(['staff']);
      toast.success('Staff member created successfully!');
      navigate(`/users/staff/${response.data.id}`);
    },
    onError: (error) => {
      toast.error(`Failed to create: ${error.message}`);
    },
  });

  const onSubmit = (formData) => {
    const cleanedData = {
      full_name: formData.full_name,
      email: formData.email,
      contact: formData.contact,
      department: formData.department ? parseInt(formData.department) : null,
      account_status: formData.account_status,
    };

    if (isNew) {
      createMutation.mutate(cleanedData);
    } else {
      updateMutation.mutate(cleanedData);
    }
  };

  if (isLoading && !isNew) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate(isNew ? '/users/staff' : `/users/staff/${id}`)}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <h1 className="text-2xl font-bold text-gray-900">
          {isNew ? 'Add New Staff Member' : 'Edit Staff Member'}
        </h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold text-gray-900">Staff Details</h3>
              </Card.Header>
              <Card.Content className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('full_name', { required: 'Full name is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.full_name && <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    {...register('email', { required: 'Email is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contact Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    {...register('contact', { required: 'Contact number is required' })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  {errors.contact && <p className="mt-1 text-sm text-red-600">{errors.contact.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Department</label>
                  <select
                    {...register('department')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="">Select department</option>
                    {departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Account Status</label>
                  <select
                    {...register('account_status')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="suspended">Suspended</option>
                  </select>
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
                  {isNew ? 'Create Staff' : 'Save Changes'}
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  className="w-full"
                  onClick={() => navigate(isNew ? '/users/staff' : `/users/staff/${id}`)}
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

export default StaffEdit;
