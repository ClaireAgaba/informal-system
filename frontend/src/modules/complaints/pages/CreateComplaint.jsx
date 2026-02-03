import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, X } from 'lucide-react';
import complaintsApi from '../services/complaintsApi';
import assessmentCenterApi from '../../assessment-centers/services/assessmentCenterApi';
import assessmentSeriesApi from '../../assessment-series/services/assessmentSeriesApi';
import occupationApi from '../../occupations/services/occupationApi';

const CreateComplaint = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [centers, setCenters] = useState([]);
  const [series, setSeries] = useState([]);
  const [occupations, setOccupations] = useState([]);
  const [formData, setFormData] = useState({
    category: '',
    exam_center: '',
    exam_series: '',
    program: '',
    phone: '',
    issue_description: '',
    proof_of_complaint: null,
    status: 'new',
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    fetchDropdownData();
  }, []);

  const fetchAllPagesApi = async (fetchPage, params = {}, page = 1, acc = []) => {
    const response = await fetchPage({ ...params, page, page_size: 1000 });
    const data = response?.data;

    if (Array.isArray(data)) {
      return [...acc, ...data];
    }

    const results = data?.results || [];
    const nextAcc = [...acc, ...results];

    if (!data?.next) {
      return nextAcc;
    }

    return fetchAllPagesApi(fetchPage, params, page + 1, nextAcc);
  };

  const fetchDropdownData = async () => {
    try {
      const categoriesRes = await complaintsApi.getCategories();
      const [centersData, seriesData, occupationsData] = await Promise.all([
        fetchAllPagesApi(assessmentCenterApi.getAll),
        fetchAllPagesApi(assessmentSeriesApi.getAll),
        fetchAllPagesApi(occupationApi.getAll),
      ]);

      console.log('Categories response:', categoriesRes);
      console.log('Centers response:', centersData);
      console.log('Series response:', seriesData);
      console.log('Occupations response:', occupationsData);

      const categoriesData = Array.isArray(categoriesRes.data) ? categoriesRes.data : (categoriesRes.data.results || []);

      console.log('Parsed categories:', categoriesData);
      console.log('Parsed centers:', centersData);
      console.log('Parsed series:', seriesData);
      console.log('Parsed occupations:', occupationsData);

      setCategories(categoriesData);
      setCenters(centersData);
      setSeries(seriesData);
      setOccupations(occupationsData);
    } catch (error) {
      console.error('Error fetching dropdown data:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const maxSize = 20 * 1024 * 1024; // 20MB
      if (file.size > maxSize) {
        setErrors((prev) => ({
          ...prev,
          proof_of_complaint: 'File size must be less than 20MB',
        }));
        return;
      }
      setFormData((prev) => ({
        ...prev,
        proof_of_complaint: file,
      }));
      setErrors((prev) => ({ ...prev, proof_of_complaint: '' }));
    }
  };

  const removeFile = () => {
    setFormData((prev) => ({
      ...prev,
      proof_of_complaint: null,
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.category) newErrors.category = 'Category is required';
    if (!formData.exam_center) newErrors.exam_center = 'Exam center is required';
    if (!formData.exam_series) newErrors.exam_series = 'Exam series is required';
    if (!formData.program) newErrors.program = 'Program is required';
    if (!formData.issue_description) newErrors.issue_description = 'Issue description is required';

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

      const submitData = new FormData();
      Object.keys(formData).forEach((key) => {
        if (formData[key] !== null && formData[key] !== '') {
          submitData.append(key, formData[key]);
        }
      });

      const response = await complaintsApi.createComplaint(submitData);
      navigate(`/complaints/${response.data.id}`);
    } catch (error) {
      console.error('Error creating complaint:', error);
      if (error.response?.data) {
        setErrors(error.response.data);
      } else {
        alert('Failed to create complaint. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/complaints')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Complaints
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Create New Complaint</h1>
        <p className="text-gray-600 mt-1">Submit a support ticket for assistance</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="max-w-4xl">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6 space-y-6">
          {/* Complaint Category */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                Complaint Category <span className="text-red-500">*</span>
              </label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                  errors.category ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="" className="text-gray-500">Select category</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id} className="text-gray-900">
                    {category.name}
                  </option>
                ))}
              </select>
              {errors.category && <p className="mt-1 text-sm text-red-500">{errors.category}</p>}
            </div>

            <div>
              <label htmlFor="exam_center" className="block text-sm font-medium text-gray-700 mb-2">
                Assessment Center <span className="text-red-500">*</span>
              </label>
              <select
                id="exam_center"
                name="exam_center"
                value={formData.exam_center}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                  errors.exam_center ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="" className="text-gray-500">Select center</option>
                {centers.map((center) => (
                  <option key={center.id} value={center.id} className="text-gray-900">
                    {center.name}
                  </option>
                ))}
              </select>
              {errors.exam_center && <p className="mt-1 text-sm text-red-500">{errors.exam_center}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="exam_series" className="block text-sm font-medium text-gray-700 mb-2">
                Assessment Series <span className="text-red-500">*</span>
              </label>
              <select
                id="exam_series"
                name="exam_series"
                value={formData.exam_series}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                  errors.exam_series ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="" className="text-gray-500">Select series</option>
                {series.map((s) => (
                  <option key={s.id} value={s.id} className="text-gray-900">
                    {s.name}
                  </option>
                ))}
              </select>
              {errors.exam_series && <p className="mt-1 text-sm text-red-500">{errors.exam_series}</p>}
            </div>

            <div>
              <label htmlFor="program" className="block text-sm font-medium text-gray-700 mb-2">
                Occupation <span className="text-red-500">*</span>
              </label>
              <select
                id="program"
                name="program"
                value={formData.program}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 ${
                  errors.program ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="" className="text-gray-500">Select occupation</option>
                {occupations.map((occ) => (
                  <option key={occ.id} value={occ.id} className="text-gray-900">
                    {occ.name}
                  </option>
                ))}
              </select>
              {errors.program && <p className="mt-1 text-sm text-red-500">{errors.program}</p>}
            </div>
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="e.g. +256 7XX XXX XXX"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="issue_description" className="block text-sm font-medium text-gray-700 mb-2">
              Issue Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="issue_description"
              name="issue_description"
              value={formData.issue_description}
              onChange={handleChange}
              rows={6}
              placeholder="Provide the issue in detail"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.issue_description ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.issue_description && (
              <p className="mt-1 text-sm text-red-500">{errors.issue_description}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attachments
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Supported formats: PNG, JPG, JPEG, PDF, DOC, DOCX. Max size: 20MB per file.
            </p>
            
            {!formData.proof_of_complaint ? (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  id="proof_of_complaint"
                  accept=".png,.jpg,.jpeg,.pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="proof_of_complaint"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <Upload className="w-12 h-12 text-gray-400 mb-2" />
                  <span className="text-sm text-gray-600">Click to upload or drag and drop</span>
                </label>
              </div>
            ) : (
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Upload className="w-5 h-5 text-gray-400 mr-3" />
                  <span className="text-sm text-gray-900">{formData.proof_of_complaint.name}</span>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  className="text-red-600 hover:text-red-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
            {errors.proof_of_complaint && (
              <p className="mt-1 text-sm text-red-500">{errors.proof_of_complaint}</p>
            )}
          </div>

          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
            >
              <option value="new" className="text-gray-900">New</option>
              <option value="in_progress" className="text-gray-900">In Progress</option>
              <option value="done" className="text-gray-900">Done</option>
              <option value="cancelled" className="text-gray-900">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/complaints')}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Complaint'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateComplaint;
