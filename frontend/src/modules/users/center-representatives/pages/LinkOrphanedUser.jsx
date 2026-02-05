import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, User, Building2 } from 'lucide-react';
import centerRepresentativeApi from '../../services/centerRepresentativeApi';
import apiClient from '@services/apiClient';

const LinkOrphanedUser = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [user, setUser] = useState(null);
  const [centers, setCenters] = useState([]);
  const [branches, setBranches] = useState([]);
  const [formData, setFormData] = useState({
    fullname: '',
    contact: '',
    assessment_center_id: '',
    assessment_center_branch_id: '',
  });

  useEffect(() => {
    fetchData();
  }, [userId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Fetch orphaned users to find this one
      const orphanedRes = await centerRepresentativeApi.getOrphanedUsers();
      const foundUser = orphanedRes.data.results?.find(u => u.id === parseInt(userId));
      
      if (!foundUser) {
        alert('User not found or already has a profile');
        navigate('/users/center-representatives');
        return;
      }
      
      setUser(foundUser);
      setFormData(prev => ({
        ...prev,
        fullname: `${foundUser.first_name || ''} ${foundUser.last_name || ''}`.trim(),
      }));

      // Fetch assessment centers
      const centersRes = await apiClient.get('/assessment-centers/');
      setCenters(centersRes.data.results || centersRes.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      alert('Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const handleCenterChange = async (centerId) => {
    setFormData(prev => ({
      ...prev,
      assessment_center_id: centerId,
      assessment_center_branch_id: '',
    }));
    setBranches([]);

    if (centerId) {
      try {
        const res = await apiClient.get(`/assessment-centers/${centerId}/branches/`);
        setBranches(res.data || []);
      } catch (error) {
        console.error('Error fetching branches:', error);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.fullname || !formData.contact || !formData.assessment_center_id) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      setSubmitting(true);
      await centerRepresentativeApi.linkUser({
        user_id: parseInt(userId),
        fullname: formData.fullname,
        contact: formData.contact,
        assessment_center_id: parseInt(formData.assessment_center_id),
        assessment_center_branch_id: formData.assessment_center_branch_id ? parseInt(formData.assessment_center_branch_id) : null,
      });
      
      alert('Profile created successfully!');
      navigate('/users/center-representatives');
    } catch (error) {
      console.error('Error linking user:', error);
      alert(error.response?.data?.error || 'Failed to create profile');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <button
        onClick={() => navigate('/users/center-representatives')}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="w-5 h-5 mr-2" />
        Back to Center Representatives
      </button>

      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Create Profile for Existing User</h1>
        <p className="text-gray-600 mb-6">
          This user was created without a CenterRepresentative profile. Fill in the details below to create their profile.
        </p>

        {/* User Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <User className="w-5 h-5 text-blue-600 mr-2" />
            <span className="font-medium text-blue-900">Existing User Details</span>
          </div>
          <div className="mt-2 text-sm text-blue-800">
            <p><strong>Username:</strong> {user?.username}</p>
            <p><strong>Email:</strong> {user?.email}</p>
            <p><strong>Status:</strong> {user?.is_active ? 'Active' : 'Inactive'}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.fullname}
              onChange={(e) => setFormData(prev => ({ ...prev, fullname: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Number <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.contact}
              onChange={(e) => setFormData(prev => ({ ...prev, contact: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., 0700123456"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Assessment Center <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.assessment_center_id}
              onChange={(e) => handleCenterChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Select a center...</option>
              {centers.map(center => (
                <option key={center.id} value={center.id}>
                  {center.center_number} - {center.center_name}
                </option>
              ))}
            </select>
          </div>

          {branches.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Branch (Optional)
              </label>
              <select
                value={formData.assessment_center_branch_id}
                onChange={(e) => setFormData(prev => ({ ...prev, assessment_center_branch_id: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Main Center (No Branch)</option>
                {branches.map(branch => (
                  <option key={branch.id} value={branch.id}>
                    {branch.branch_code} - {branch.branch_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="w-5 h-5 mr-2" />
              {submitting ? 'Creating Profile...' : 'Create Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LinkOrphanedUser;
