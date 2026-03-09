import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FileSearch, Download, ChevronRight } from 'lucide-react';
import apiClient from '../../../services/apiClient';
import marksheetsApi from '../api/marksheetsApi';

export default function ExtractMarks() {
  const [formData, setFormData] = useState({
    assessment_center: '',
    registration_category: '',
    occupation: '',
  });

  const [centerSearch, setCenterSearch] = useState('');
  const [occupationSearch, setOccupationSearch] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch assessment centers
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: async () => {
      const response = await apiClient.get('/assessment-centers/centers/', { params: { page_size: 1000 } });
      return response.data.results || response.data;
    },
  });

  // Fetch occupations
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations-all'],
    queryFn: async () => {
      const response = await apiClient.get('/occupations/occupations/', { params: { page_size: 1000 } });
      return response.data.results || response.data;
    },
  });

  const centers = Array.isArray(centersData) ? centersData : [];
  const allOccupations = Array.isArray(occupationsData) ? occupationsData : [];

  // Filter centers based on search
  const filteredCenters = centers.filter(center =>
    center.center_name?.toLowerCase().includes(centerSearch.toLowerCase()) ||
    center.center_number?.toLowerCase().includes(centerSearch.toLowerCase())
  );

  // Filter occupations based on search
  const filteredOccupations = allOccupations.filter(occ =>
    occ.occ_name?.toLowerCase().includes(occupationSearch.toLowerCase()) ||
    occ.occ_code?.toLowerCase().includes(occupationSearch.toLowerCase())
  );

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    setError('');
    setSuccess('');
  };

  const handleExtract = async () => {
    setError('');
    setSuccess('');

    if (!formData.assessment_center) {
      setError('Please select an assessment center');
      return;
    }
    if (!formData.registration_category) {
      setError('Please select a registration category');
      return;
    }
    if (!formData.occupation) {
      setError('Please select an occupation');
      return;
    }

    setIsExtracting(true);

    try {
      const response = await marksheetsApi.extractMarks(formData);
      
      // Create blob and download
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from response headers or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'ExtractedMarks.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setSuccess('Marks extracted successfully!');
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to extract marks';
      setError(errorMessage);
    } finally {
      setIsExtracting(false);
    }
  };

  const selectedCenter = centers.find(c => c.id === parseInt(formData.assessment_center));
  const selectedOccupation = allOccupations.find(o => o.id === parseInt(formData.occupation));

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center text-sm text-gray-500 mb-4">
          <Link to="/dashboard" className="hover:text-blue-600 flex items-center">
            Dashboard
          </Link>
          <ChevronRight className="h-4 w-4 mx-2" />
          <Link to="/marksheets" className="hover:text-blue-600">
            Marksheets
          </Link>
          <ChevronRight className="h-4 w-4 mx-2" />
          <span className="text-gray-900 font-medium">Extract Marks</span>
        </div>

        <h1 className="text-2xl font-bold text-gray-900">Extract Marks</h1>
        <p className="text-gray-600 mt-1">
          Extract existing marks for candidates by center, registration category, and occupation.
          Use this to backup marks before re-enrollment.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Assessment Center */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Assessment Center <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search centers..."
                value={centerSearch}
                onChange={(e) => setCenterSearch(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 mb-2"
              />
              <select
                name="assessment_center"
                value={formData.assessment_center}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              >
                <option value="">Select Center</option>
                {filteredCenters.map(center => (
                  <option key={center.id} value={center.id}>
                    {center.center_number} - {center.center_name}
                  </option>
                ))}
              </select>
            </div>
            {selectedCenter && (
              <p className="text-sm text-gray-500 mt-1">
                Selected: {selectedCenter.center_number} - {selectedCenter.center_name}
              </p>
            )}
          </div>

          {/* Registration Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Registration Category <span className="text-red-500">*</span>
            </label>
            <select
              name="registration_category"
              value={formData.registration_category}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">Select Category</option>
              <option value="modular">Modular</option>
              <option value="formal">Formal</option>
              <option value="workers_pas">Worker's PAS</option>
            </select>
          </div>

          {/* Occupation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Occupation <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search occupations..."
                value={occupationSearch}
                onChange={(e) => setOccupationSearch(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 mb-2"
              />
              <select
                name="occupation"
                value={formData.occupation}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              >
                <option value="">Select Occupation</option>
                {filteredOccupations.map(occ => (
                  <option key={occ.id} value={occ.id}>
                    {occ.occ_code} - {occ.occ_name}
                  </option>
                ))}
              </select>
            </div>
            {selectedOccupation && (
              <p className="text-sm text-gray-500 mt-1">
                Selected: {selectedOccupation.occ_code} - {selectedOccupation.occ_name}
              </p>
            )}
          </div>
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h4 className="font-medium text-orange-800 mb-2">What this extracts:</h4>
          <ul className="text-sm text-orange-700 list-disc list-inside space-y-1">
            <li>All existing marks for candidates matching the criteria</li>
            <li>Assessment series where marks were recorded</li>
            <li>Module/Paper codes and names</li>
            <li>Marks, grades, and status</li>
          </ul>
          <p className="text-sm text-orange-700 mt-2">
            <strong>Note:</strong> Assessment series is not required as a filter - all marks regardless of series will be extracted.
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {success}
          </div>
        )}

        {/* Extract Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleExtract}
            disabled={isExtracting}
            className="flex items-center px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExtracting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Extracting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Extract Marks
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
