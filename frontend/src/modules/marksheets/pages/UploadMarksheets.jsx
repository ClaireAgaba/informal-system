import { useState } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle, Search } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../../services/apiClient';
import marksheetsApi from '../api/marksheetsApi';

export default function UploadMarksheets() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    assessment_series: '',
    registration_category: '',
    occupation: '',
    module: '',
    level: '',
    assessment_center: '',
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [moduleSearch, setModuleSearch] = useState('');

  // Fetch assessment series
  const { data: seriesData } = useQuery({
    queryKey: ['assessment-series'],
    queryFn: async () => {
      const response = await apiClient.get('/assessment-series/series/');
      return response.data.results || response.data;
    },
  });

  // Fetch occupations (all - no pagination)
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations-all'],
    queryFn: async () => {
      const response = await apiClient.get('/occupations/occupations/', { params: { page_size: 500 } });
      return response.data.results || response.data;
    },
    staleTime: 0,
  });

  // Fetch modules for selected occupation (modular only)
  const { data: modulesData } = useQuery({
    queryKey: ['occupation-modules', formData.occupation],
    queryFn: async () => {
      const response = await apiClient.get(`/occupations/modules/by-occupation/?occupation=${formData.occupation}`);
      return response.data.results || response.data;
    },
    enabled: !!formData.occupation && formData.registration_category === 'modular',
  });

  // Fetch levels for selected occupation (formal and workers_pas)
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', formData.occupation],
    queryFn: async () => {
      const response = await apiClient.get(`/occupations/levels/by_occupation/?occupation_id=${formData.occupation}`);
      return response.data.results || response.data;
    },
    enabled: !!formData.occupation && (formData.registration_category === 'formal' || formData.registration_category === 'workers_pas'),
  });

  // Fetch assessment centers (all - no pagination)
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: async () => {
      const response = await apiClient.get('/assessment-centers/centers/', { params: { page_size: 1000 } });
      return response.data.results || response.data;
    },
  });

  const series = Array.isArray(seriesData) ? seriesData : [];
  const allOccupations = Array.isArray(occupationsData) ? occupationsData : [];
  const modules = Array.isArray(modulesData) ? modulesData : [];
  const levels = Array.isArray(levelsData) ? levelsData : [];
  const centers = Array.isArray(centersData) ? centersData : [];

  // Filter occupations based on registration category
  const occupations = formData.registration_category
    ? allOccupations.filter(occ => {
        if (formData.registration_category === 'modular') {
          return occ.has_modular === true;
        }
        return occ.occ_category === formData.registration_category;
      })
    : [];

  // Filter modules based on search
  const filteredModules = modules.filter(module =>
    module.module_name.toLowerCase().includes(moduleSearch.toLowerCase()) ||
    module.module_code.toLowerCase().includes(moduleSearch.toLowerCase())
  );

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
    setUploadResult(null);
    
    if (name === 'registration_category') {
      setFormData(prev => ({ ...prev, occupation: '', module: '', level: '' }));
    }
    if (name === 'occupation') {
      setFormData(prev => ({ ...prev, module: '', level: '' }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        setError('Please select an Excel file (.xlsx or .xls)');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError('');
      setUploadResult(null);
    }
  };

  const uploadMutation = useMutation({
    mutationFn: async (data) => {
      const formDataToSend = new FormData();
      formDataToSend.append('assessment_series', data.assessment_series);
      formDataToSend.append('occupation', data.occupation);
      
      if (data.registration_category === 'modular') {
        formDataToSend.append('module', data.module);
      } else if (data.registration_category === 'formal' || data.registration_category === 'workers_pas') {
        formDataToSend.append('level', data.level);
      }
      
      if (data.assessment_center) {
        formDataToSend.append('assessment_center', data.assessment_center);
      }
      formDataToSend.append('file', data.file);

      let endpoint;
      if (data.registration_category === 'modular') {
        endpoint = '/results/marksheets/upload-modular/';
      } else if (data.registration_category === 'formal') {
        endpoint = '/results/marksheets/upload-formal/';
      } else if (data.registration_category === 'workers_pas') {
        endpoint = '/results/marksheets/upload-workers-pas/';
      }

      return apiClient.post(endpoint, formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    },
    onSuccess: (response) => {
      setUploadResult(response.data);
      queryClient.invalidateQueries(['modular-results']);
      queryClient.invalidateQueries(['formal-results']);
      // Reset form
      setFormData({
        assessment_series: '',
        registration_category: '',
        occupation: '',
        module: '',
        level: '',
        assessment_center: '',
      });
      setSelectedFile(null);
    },
    onError: (err) => {
      // Check if the error response has detailed error information
      if (err.response?.data) {
        const responseData = err.response.data;
        
        // If there's a message and errors array, show them as upload result
        if (responseData.message && responseData.errors) {
          setUploadResult(responseData);
          setError('');
        } else {
          // Otherwise show generic error
          const errorMsg = responseData.error || responseData.detail || err.message;
          setError(errorMsg);
        }
      } else {
        setError(err.message || 'Upload failed');
      }
    },
  });

  const handleUpload = () => {
    if (!formData.assessment_series || !formData.registration_category || !formData.occupation) {
      setError('Please fill in all required fields');
      return;
    }
    
    if (formData.registration_category === 'modular' && !formData.module) {
      setError('Please select a module');
      return;
    }
    
    if ((formData.registration_category === 'formal' || formData.registration_category === 'workers_pas') && !formData.level) {
      setError('Please select a level');
      return;
    }
    
    if (!selectedFile) {
      setError('Please select an Excel file to upload');
      return;
    }

    uploadMutation.mutate({
      ...formData,
      file: selectedFile,
    });
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Upload className="h-7 w-7 text-green-600" />
          Upload Marksheets
        </h1>
        <p className="text-gray-600 mt-1">Upload completed marksheets with results</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series <span className="text-red-500">*</span>
            </label>
            <select
              name="assessment_series"
              value={formData.assessment_series}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Assessment Series</option>
              {series.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Registration Category <span className="text-red-500">*</span>
            </label>
            <select
              name="registration_category"
              value={formData.registration_category}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Category</option>
              <option value="modular">Modular</option>
              <option value="formal">Formal</option>
              <option value="workers_pas">Worker's PAS</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Occupation <span className="text-red-500">*</span>
            </label>
            <select
              name="occupation"
              value={formData.occupation}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={!formData.registration_category}
            >
              <option value="">
                {formData.registration_category ? 'Select Occupation' : 'Select Category First'}
              </option>
              {occupations.map(occ => (
                <option key={occ.id} value={occ.id}>
                  {occ.occ_name} ({occ.occ_code})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Module Selection - Only for Modular */}
        {formData.registration_category === 'modular' && formData.occupation && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Module <span className="text-red-500">*</span>
            </label>
            <div className="border border-gray-300 rounded-lg p-4">
              <div className="mb-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search modules..."
                    value={moduleSearch}
                    onChange={(e) => setModuleSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2">
                {filteredModules.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No modules found</p>
                ) : (
                  filteredModules.map(module => (
                    <label
                      key={module.id}
                      className="flex items-center p-3 hover:bg-gray-50 rounded-lg cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="module"
                        value={module.id}
                        checked={formData.module === String(module.id)}
                        onChange={(e) => setFormData(prev => ({ ...prev, module: e.target.value }))}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <span className="ml-3 text-sm text-gray-900">
                        {module.module_name} ({module.module_code})
                      </span>
                    </label>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Level Selection - For Formal and Worker's PAS */}
        {(formData.registration_category === 'formal' || formData.registration_category === 'workers_pas') && formData.occupation && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Level <span className="text-red-500">*</span>
            </label>
            <select
              name="level"
              value={formData.level}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Level</option>
              {levels.map(level => (
                <option key={level.id} value={level.id}>
                  {level.level_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Assessment Center */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Assessment Center (optional)
          </label>
          <select
            name="assessment_center"
            value={formData.assessment_center}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">-- All Centers --</option>
            {centers.map(center => (
              <option key={center.id} value={center.id}>
                {center.center_name} ({center.center_number})
              </option>
            ))}
          </select>
        </div>

        {/* File Upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Excel File <span className="text-red-500">*</span>
          </label>
          <div className="flex items-center gap-3">
            <label className="flex-1 flex items-center justify-center px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors">
              <FileSpreadsheet className="h-5 w-5 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">
                {selectedFile ? selectedFile.name : 'Choose Excel file...'}
              </span>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-1">Upload the generated marksheet with filled marks</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Success/Warning/Error Message */}
        {uploadResult && (
          <div className={`mb-4 p-4 rounded-lg border ${
            uploadResult.updated_count > 0 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-start gap-2 mb-2">
              {uploadResult.updated_count > 0 ? (
                <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p className={`text-sm font-medium ${
                  uploadResult.updated_count > 0 ? 'text-green-800' : 'text-red-800'
                }`}>
                  {uploadResult.message}
                </p>
                <p className={`text-sm mt-1 ${
                  uploadResult.updated_count > 0 ? 'text-green-700' : 'text-red-700'
                }`}>
                  Updated: {uploadResult.updated_count} | Skipped: {uploadResult.skipped_count}
                </p>
              </div>
            </div>
            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <div className={`mt-3 pt-3 border-t ${
                uploadResult.updated_count > 0 ? 'border-green-200' : 'border-red-200'
              }`}>
                <p className={`text-sm font-medium mb-2 ${
                  uploadResult.updated_count > 0 ? 'text-green-800' : 'text-red-800'
                }`}>
                  {uploadResult.updated_count > 0 ? 'Issues encountered:' : 'Errors:'}
                </p>
                <ul className={`list-disc list-inside space-y-1 text-sm max-h-40 overflow-y-auto ${
                  uploadResult.updated_count > 0 ? 'text-green-700' : 'text-red-700'
                }`}>
                  {uploadResult.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Upload Button */}
        <div className="flex justify-end">
          <button
            onClick={handleUpload}
            disabled={
              uploadMutation.isPending || 
              !selectedFile || 
              (formData.registration_category === 'modular' && !formData.module) ||
              ((formData.registration_category === 'formal' || formData.registration_category === 'workers_pas') && !formData.level)
            }
            className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Upload className="h-4 w-4" />
            {uploadMutation.isPending ? 'Uploading...' : 'Upload Marks'}
          </button>
        </div>
      </div>
    </div>
  );
}
