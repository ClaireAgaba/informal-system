import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ArrowLeft, Edit, User, Mail, Phone, Building, Calendar, CheckCircle, XCircle, Ban, Power } from 'lucide-react';
import userApi from '../../services/userApi';
import Button from '@shared/components/Button';
import Card from '@shared/components/Card';
import { formatDate } from '@shared/utils/formatters';

const SupportStaffView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['support-staff', id],
    queryFn: () => userApi.supportStaff.getById(id),
  });

  const supportStaff = data?.data;

  // Change status mutation
  const changeStatusMutation = useMutation({
    mutationFn: ({ newStatus }) => userApi.supportStaff.update(id, { account_status: newStatus }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries(['support-staff', id]);
      queryClient.invalidateQueries(['support-staff']);
      const statusText = variables.newStatus === 'active' ? 'activated' : 
                        variables.newStatus === 'suspended' ? 'suspended' : 'deactivated';
      toast.success(`Support staff account ${statusText} successfully!`);
    },
    onError: (error) => {
      toast.error(`Failed to change status: ${error.message}`);
    },
  });

  const handleStatusChange = (newStatus) => {
    const statusText = newStatus === 'active' ? 'activate' : 
                      newStatus === 'suspended' ? 'suspend' : 'deactivate';
    if (window.confirm(`Are you sure you want to ${statusText} this support staff account?`)) {
      changeStatusMutation.mutate({ newStatus });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading support staff details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error loading support staff: {error.message}</div>
      </div>
    );
  }

  if (!supportStaff) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Support staff member not found</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/users/support-staff')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Support Staff List
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{supportStaff.full_name}</h1>
            <p className="text-gray-600 mt-1">{supportStaff.department_name || 'No Department'}</p>
          </div>
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate(`/users/support-staff/${id}/edit`)}
          >
            <Edit className="w-4 h-4 mr-2" />
            Edit Support Staff
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Support Staff Information</h3>
            </Card.Header>
            <Card.Content className="space-y-4">
              <div className="flex items-center justify-center py-4">
                <span
                  className={`inline-flex items-center px-4 py-2 text-sm font-semibold rounded-full ${
                    supportStaff.account_status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : supportStaff.account_status === 'suspended'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {supportStaff.account_status === 'active' ? (
                    <CheckCircle className="w-4 h-4 mr-2" />
                  ) : (
                    <XCircle className="w-4 h-4 mr-2" />
                  )}
                  {supportStaff.account_status_display}
                </span>
              </div>

              <InfoItem
                icon={<User className="w-5 h-5 text-gray-400" />}
                label="Full Name"
                value={supportStaff.full_name}
              />

              <InfoItem
                icon={<Mail className="w-5 h-5 text-gray-400" />}
                label="Email"
                value={supportStaff.email}
              />

              <InfoItem
                icon={<Phone className="w-5 h-5 text-gray-400" />}
                label="Contact Number"
                value={supportStaff.contact}
              />

              <InfoItem
                icon={<Building className="w-5 h-5 text-gray-400" />}
                label="Department"
                value={supportStaff.department_name || 'Not assigned'}
              />

              <InfoItem
                icon={<Calendar className="w-5 h-5 text-gray-400" />}
                label="Date Joined"
                value={formatDate(supportStaff.date_joined)}
              />

              {supportStaff.last_login && (
                <InfoItem
                  icon={<Calendar className="w-5 h-5 text-gray-400" />}
                  label="Last Login"
                  value={formatDate(supportStaff.last_login)}
                />
              )}

              <div className="pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500 space-y-1">
                  <p>Created: {formatDate(supportStaff.created_at)}</p>
                  <p>Updated: {formatDate(supportStaff.updated_at)}</p>
                </div>
              </div>
            </Card.Content>
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
            </Card.Header>
            <Card.Content className="space-y-3">
              <Button
                variant="primary"
                size="md"
                className="w-full"
                onClick={() => navigate(`/users/support-staff/${id}/edit`)}
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit Details
              </Button>

              {/* Status change buttons */}
              {supportStaff.account_status === 'active' && (
                <>
                  <Button
                    variant="warning"
                    size="md"
                    className="w-full"
                    onClick={() => handleStatusChange('suspended')}
                    loading={changeStatusMutation.isPending}
                  >
                    <Ban className="w-4 h-4 mr-2" />
                    Suspend Account
                  </Button>
                  <Button
                    variant="outline"
                    size="md"
                    className="w-full"
                    onClick={() => handleStatusChange('inactive')}
                    loading={changeStatusMutation.isPending}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Deactivate Account
                  </Button>
                </>
              )}

              {supportStaff.account_status === 'suspended' && (
                <Button
                  variant="success"
                  size="md"
                  className="w-full"
                  onClick={() => handleStatusChange('active')}
                  loading={changeStatusMutation.isPending}
                >
                  <Power className="w-4 h-4 mr-2" />
                  Activate Account
                </Button>
              )}

              {supportStaff.account_status === 'inactive' && (
                <Button
                  variant="success"
                  size="md"
                  className="w-full"
                  onClick={() => handleStatusChange('active')}
                  loading={changeStatusMutation.isPending}
                >
                  <Power className="w-4 h-4 mr-2" />
                  Activate Account
                </Button>
              )}
            </Card.Content>
          </Card>
        </div>
      </div>
    </div>
  );
};

const InfoItem = ({ icon, label, value }) => (
  <div className="flex items-start space-x-3">
    <div className="flex-shrink-0 mt-0.5">{icon}</div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-1 text-sm text-gray-900">{value}</p>
    </div>
  </div>
);

export default SupportStaffView;
