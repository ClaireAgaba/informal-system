import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Edit, RefreshCw, Mail, Phone, Building, MapPin, Calendar, User, Power, PowerOff } from 'lucide-react';
import centerRepresentativeApi from '../../services/centerRepresentativeApi';

const CenterRepresentativeView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [representative, setRepresentative] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRepresentative();
  }, [id]);

  const fetchRepresentative = async () => {
    try {
      setLoading(true);
      const response = await centerRepresentativeApi.getById(id);
      setRepresentative(response.data);
    } catch (error) {
      console.error('Error fetching center representative:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (window.confirm(`Reset password for ${representative.fullname} to default (uvtab)?`)) {
      try {
        await centerRepresentativeApi.resetPassword(id);
        alert('Password reset successfully to uvtab');
      } catch (error) {
        console.error('Error resetting password:', error);
        alert('Failed to reset password');
      }
    }
  };

  const handleToggleStatus = async () => {
    try {
      if (representative.account_status === 'active') {
        await centerRepresentativeApi.deactivate(id);
      } else {
        await centerRepresentativeApi.activate(id);
      }
      fetchRepresentative();
    } catch (error) {
      console.error('Error toggling status:', error);
      alert('Failed to update status');
    }
  };

  const handleSendEmail = () => {
    window.location.href = `mailto:${representative.email}`;
  };

  const handleCall = () => {
    window.location.href = `tel:${representative.contact}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading center representative...</div>
      </div>
    );
  }

  if (!representative) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Center representative not found</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/users/center-representatives')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Center Representatives
        </button>

        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="h-20 w-20 bg-white rounded-full flex items-center justify-center mr-4">
                <span className="text-3xl font-bold text-blue-600">
                  {representative.fullname?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h1 className="text-3xl font-bold">{representative.fullname}</h1>
                <p className="text-blue-100 mt-1">Center Representative</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => navigate(`/users/center-representatives/${id}/edit`)}
                className="flex items-center px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50"
              >
                <Edit className="w-5 h-5 mr-2" />
                Edit Details
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Personal Information */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <User className="w-5 h-5 text-gray-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Personal Information</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Full Name</label>
                <p className="text-gray-900 mt-1">{representative.fullname}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Email</label>
                <p className="text-gray-900 mt-1">{representative.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Contact</label>
                <p className="text-gray-900 mt-1">{representative.contact}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Account Status</label>
                <div className="mt-1">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    representative.account_status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : representative.account_status === 'suspended'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {representative.account_status_display}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Center Information */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Building className="w-5 h-5 text-gray-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Center Information</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Center</label>
                <p className="text-gray-900 mt-1">{representative.center_name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Center Number</label>
                <p className="text-gray-900 mt-1">{representative.center_number}</p>
              </div>
              {representative.branch_name && (
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-500">Branch</label>
                  <p className="text-gray-900 mt-1">{representative.branch_name}</p>
                </div>
              )}
            </div>
          </div>

          {/* Audit Trail */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Calendar className="w-5 h-5 text-gray-600 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Audit Trail</h2>
            </div>
            <div className="space-y-3">
              <div className="flex items-center text-sm">
                <span className="text-gray-500 w-32">Created:</span>
                <span className="text-gray-900">
                  {new Date(representative.created_at).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center text-sm">
                <span className="text-gray-500 w-32">Last Updated:</span>
                <span className="text-gray-900">
                  {new Date(representative.updated_at).toLocaleString()}
                </span>
              </div>
              {representative.last_login && (
                <div className="flex items-center text-sm">
                  <span className="text-gray-500 w-32">Last Login:</span>
                  <span className="text-gray-900">
                    {new Date(representative.last_login).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate(`/users/center-representatives/${id}/edit`)}
                className="w-full flex items-center justify-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                <Edit className="w-5 h-5 mr-2" />
                Edit Representative
              </button>
              <button
                onClick={handleResetPassword}
                className="w-full flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                Reset Password
              </button>
              <button
                onClick={handleSendEmail}
                className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Mail className="w-5 h-5 mr-2" />
                Send Email
              </button>
              <button
                onClick={handleCall}
                className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Phone className="w-5 h-5 mr-2" />
                Call Representative
              </button>
              <button
                onClick={handleToggleStatus}
                className={`w-full flex items-center justify-center px-4 py-2 rounded-lg ${
                  representative.account_status === 'active'
                    ? 'bg-orange-600 hover:bg-orange-700'
                    : 'bg-green-600 hover:bg-green-700'
                } text-white`}
              >
                {representative.account_status === 'active' ? (
                  <>
                    <PowerOff className="w-5 h-5 mr-2" />
                    Deactivate Account
                  </>
                ) : (
                  <>
                    <Power className="w-5 h-5 mr-2" />
                    Activate Account
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Login Credentials */}
          <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
            <h3 className="text-sm font-semibold text-blue-900 mb-3">Login Credentials</h3>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-blue-700 font-medium">Email:</span>
                <p className="text-blue-900 break-all">{representative.email}</p>
              </div>
              <div>
                <span className="text-blue-700 font-medium">Default Password:</span>
                <p className="text-blue-900 font-mono">uvtab</p>
              </div>
              <p className="text-xs text-blue-600 mt-3">
                * Representative should change password after first login
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CenterRepresentativeView;
