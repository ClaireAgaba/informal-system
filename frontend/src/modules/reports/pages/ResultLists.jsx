import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ClipboardList, Download, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { assessmentSeriesApi } from '../../assessment-series/services/assessmentSeriesApi';
import { assessmentCenterApi } from '../../assessment-centers/services/assessmentCenterApi';
import { occupationApi } from '../../occupations/services/occupationApi';
import apiClient from '@/services/apiClient';

const ResultLists = () => {
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    assessmentSeries: '',
    registrationCategory: '',
    occupation: '',
    level: '',
    assessmentCenter: '', // Optional
  });

  // Fetch assessment series
  const { data: seriesData } = useQuery({
    queryKey: ['assessment-series'],
    queryFn: () => assessmentSeriesApi.getAll({ page_size: 1000 }),
  });

  const assessmentSeries = seriesData?.data?.results || [];

  // Fetch assessment centers
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: () => assessmentCenterApi.getAll({ page_size: 1000 }),
  });

  const assessmentCenters = centersData?.data?.results || [];

  // Fetch occupations based on registration category
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations', filters.registrationCategory],
    queryFn: () => {
      const params = { page_size: 1000 };
      if (filters.registrationCategory === 'modular') {
        params.has_modular = true;
      } else if (filters.registrationCategory) {
        params.occ_category = filters.registrationCategory;
      }
      return occupationApi.getAll(params);
    },
    enabled: !!filters.registrationCategory,
  });

  const occupations = occupationsData?.data?.results || [];

  // Fetch levels based on selected occupation
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', filters.occupation],
    queryFn: () => occupationApi.getLevels(filters.occupation),
    enabled: !!filters.occupation && filters.registrationCategory === 'formal',
  });

  const levels = levelsData?.data?.levels || [];

  // Reset occupation and level when category changes
  const handleCategoryChange = (value) => {
    setFilters({ 
      ...filters, 
      registrationCategory: value,
      occupation: '',
      level: ''
    });
  };

  // Reset level when occupation changes
  const handleOccupationChange = (value) => {
    setFilters({ 
      ...filters, 
      occupation: value,
      level: ''
    });
  };

  const handleGenerate = async () => {
    // Validate filters
    if (!filters.assessmentSeries || !filters.registrationCategory || !filters.occupation) {
      toast.error('Please select Assessment Series, Registration Category, and Occupation');
      return;
    }

    // Level is required for formal
    if (filters.registrationCategory === 'formal' && !filters.level) {
      toast.error('Please select a Level for Formal category');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        assessment_series: filters.assessmentSeries,
        registration_category: filters.registrationCategory,
        occupation: filters.occupation,
      });
      
      // Add level if specified (required for formal)
      if (filters.level) {
        params.append('level', filters.level);
      }
      
      // Add assessment center if specified
      if (filters.assessmentCenter) {
        params.append('assessment_center', filters.assessmentCenter);
      }

      const response = await apiClient.get(`/reports/result-list/?${params.toString()}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'result_list.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Result list generated successfully!');
    } catch (error) {
      console.error('Error generating result list:', error);
      
      // Handle error - need to parse blob response as JSON for error messages
      let errorMessage = 'Failed to generate result list. Please try again.';
      
      if (error.response?.data) {
        try {
          // If response is a blob, convert to text and parse as JSON
          if (error.response.data instanceof Blob) {
            const text = await error.response.data.text();
            const errorData = JSON.parse(text);
            errorMessage = errorData.error || errorMessage;
          } else {
            errorMessage = error.response.data.error || errorMessage;
          }
        } catch (parseError) {
          console.error('Error parsing error response:', parseError);
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex items-center space-x-3">
          <ClipboardList className="w-8 h-8 text-orange-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Result Lists</h1>
            <p className="text-gray-600 mt-1">Generate Result Lists</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter Options</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series
            </label>
            <select
              value={filters.assessmentSeries}
              onChange={(e) => setFilters({ ...filters, assessmentSeries: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">Select Series</option>
              {assessmentSeries.map((series) => (
                <option key={series.id} value={series.id}>
                  {series.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Registration Category
            </label>
            <select
              value={filters.registrationCategory}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">Select Category</option>
              <option value="modular">Modular</option>
              <option value="formal">Formal</option>
              <option value="workers_pas">Workers PAS</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Occupation
            </label>
            <select
              value={filters.occupation}
              onChange={(e) => handleOccupationChange(e.target.value)}
              disabled={!filters.registrationCategory}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">
                {!filters.registrationCategory 
                  ? 'Select Category First' 
                  : 'Select Occupation'}
              </option>
              {occupations.map((occupation) => (
                <option key={occupation.id} value={occupation.id}>
                  {occupation.occ_code} - {occupation.occ_name}
                </option>
              ))}
            </select>
          </div>

          {filters.registrationCategory === 'formal' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Level
              </label>
              <select
                value={filters.level}
                onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                disabled={!filters.occupation}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">
                  {!filters.occupation 
                    ? 'Select Occupation First' 
                    : 'Select Level'}
                </option>
                {levels.map((level) => (
                  <option key={level.id} value={level.id}>
                    {level.level_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Center <span className="text-gray-500 text-xs">(Optional)</span>
            </label>
            <select
              value={filters.assessmentCenter}
              onChange={(e) => setFilters({ ...filters, assessmentCenter: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">All Centers</option>
              {assessmentCenters.map((center) => (
                <option key={center.id} value={center.id}>
                  {center.center_number} - {center.center_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center space-x-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              <span>Generate Result List</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ResultLists;
