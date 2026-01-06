import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, X } from 'lucide-react';
import centerRepresentativeApi from '../../services/centerRepresentativeApi';
import assessmentCenterApi from '../../../assessment-centers/services/assessmentCenterApi';

const CenterRepresentativeEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);
  
  const [loading, setLoading] = useState(false);
  const [centers, setCenters] = useState([]);
  const [branches, setBranches] = useState([]);
  const [formData, setFormData] = useState({
    fullname: '',
    contact: '',
    assessment_center: '',
    assessment_center_branch: '',
    account_status: 'active'
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    fetchCenters();
    if (isEditMode) {
      fetchRepresentative();
    }
  }, [id]);

  useEffect(() => {
    if (formData.assessment_center) {
      fetchBranches(formData.assessment_center);
    } else {
      setBranches([]);
      setFormData(prev => ({ ...prev, assessment_center_branch: '' }));
    }
  }, [formData.assessment_center]);

  const fetchCenters = async () => {
    try {
      const response = await assessmentCenterApi.getAll();
      setCenters(response.data.results || response.data || []);
    } catch (error) {
      console.error('Error fetching centers:', error);
    }
  };

  const fetchBranches = async (centerId) => {
    try {
      const response = await assessmentCenterApi.branches.getByCenter(centerId);
      setBranches(response.data?.results || response.data || []);
    } catch (error) {
      console.error('Error fetching branches:', error);
      setBranches([]);
    }
  };

  const fetchRepresentative = async () => {
    try {
      setLoading(true);
      const response = await centerRepresentativeApi.getById(id);
      const rep = response.data;
      setFormData({
        fullname: rep.fullname || '',
        contact: rep.contact || '',
        assessment_center: rep.assessment_center || '',
        assessment_center_branch: rep.assessment_center_branch || '',
        account_status: rep.account_status || 'active'
      });
    } catch (error) {
      console.error('Error fetching representative:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.fullname.trim()) {
      newErrors.fullname = 'Full name is required';
    }

    if (!formData.contact.trim()) {
      newErrors.contact = 'Contact number is required';
    }

    if (!formData.assessment_center) {
      newErrors.assessment_center = 'Assessment center is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      
      // Prepare data - remove empty branch
      const submitData = {
        ...formData,
        assessment_center_branch: formData.assessment_center_branch || null
      };

      if (isEditMode) {
        await centerRepresentativeApi.update(id, submitData);
      } else {
        await centerRepresentativeApi.create(submitData);
      }

      navigate('/users/center-representatives');
    } catch (error) {
      console.error('Error saving representative:', error);
      if (error.response?.data) {
        setErrors(error.response.data);
      } else {
        alert('Failed to save center representative');
      }
    } finally {
      setLoading(false);
    }
  };

  const selectedCenter = centers.find(c => c.id === parseInt(formData.assessment_center));
  const selectedBranch = branches.find(b => b.id === parseInt(formData.assessment_center_branch));
  const generatedEmail = selectedCenter 
    ? selectedBranch
      ? `${selectedCenter.center_number.toLowerCase()}-${selectedBranch.branch_code?.split('-').pop() || selectedBranch.branch_code}@uvtab.go.ug`
      : `${selectedCenter.center_number.toLowerCase()}@uvtab.go.ug`
    : '';

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

        <h1 className="text-2xl font-bold text-gray-900">
          {isEditMode ? 'Edit Center Representative' : 'Create Center Representative'}
        </h1>
        <p className="text-gray-600 mt-1">
          {isEditMode 
            ? 'Update center representative information' 
            : 'Add a new center representative to the system'}
        </p>
      </div>

      {/* Form */}
      <div className="max-w-3xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="fullname"
                  value={formData.fullname}
                  onChange={handleChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.fullname ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter full name"
                />
                {errors.fullname && (
                  <p className="text-red-500 text-sm mt-1">{errors.fullname}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contact Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="contact"
                  value={formData.contact}
                  onChange={handleChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.contact ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter contact number"
                />
                {errors.contact && (
                  <p className="text-red-500 text-sm mt-1">{errors.contact}</p>
                )}
              </div>
            </div>
          </div>

          {/* Center Assignment */}
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Center Assignment</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Center <span className="text-red-500">*</span>
                </label>
                <select
                  name="assessment_center"
                  value={formData.assessment_center}
                  onChange={handleChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.assessment_center ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={isEditMode}
                >
                  <option value="">Select Assessment Center</option>
                  {centers.map(center => (
                    <option key={center.id} value={center.id}>
                      {center.center_number} - {center.center_name}
                    </option>
                  ))}
                </select>
                {errors.assessment_center && (
                  <p className="text-red-500 text-sm mt-1">{errors.assessment_center}</p>
                )}
                {isEditMode && (
                  <p className="text-sm text-gray-500 mt-1">
                    Center cannot be changed after creation
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Center Branch
                </label>
                <select
                  name="assessment_center_branch"
                  value={formData.assessment_center_branch}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={!formData.assessment_center}
                >
                  <option value="">Main Center (no specific branch)</option>
                  {branches.map(branch => (
                    <option key={branch.id} value={branch.id}>
                      {branch.branch_name}
                    </option>
                  ))}
                </select>
                <p className="text-sm text-gray-500 mt-1">
                  Optional: select a specific branch to restrict this account to that branch only
                </p>
              </div>

              {generatedEmail && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <label className="block text-sm font-medium text-blue-900 mb-1">
                    Auto-Generated Email
                  </label>
                  <p className="text-blue-700 font-mono">{generatedEmail}</p>
                  <p className="text-xs text-blue-600 mt-2">
                    This email will be automatically generated based on the center number
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Status
                </label>
                <select
                  name="account_status"
                  value={formData.account_status}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>
            </div>
          </div>

          {/* Login Information */}
          {!isEditMode && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-green-900 mb-2">Default Login Credentials</h3>
              <p className="text-sm text-green-700 mb-2">
                The representative will be able to login with:
              </p>
              <ul className="text-sm text-green-700 space-y-1 ml-4 list-disc">
                <li><strong>Email:</strong> {generatedEmail || '(Select a center first)'}</li>
                <li><strong>Password:</strong> <span className="font-mono">uvtab@2025</span></li>
              </ul>
              <p className="text-xs text-green-600 mt-3">
                * Representative should change password after first login
              </p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-4 pt-4">
            <button
              type="button"
              onClick={() => navigate('/users/center-representatives')}
              className="flex items-center px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              <X className="w-5 h-5 mr-2" />
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-5 h-5 mr-2" />
              {loading ? 'Saving...' : isEditMode ? 'Update Representative' : 'Create Representative'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CenterRepresentativeEdit;
