import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookImage, Download, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import assessmentCenterApi from '@/modules/assessment-centers/services/assessmentCenterApi';
import assessmentSeriesApi from '@/modules/assessment-series/services/assessmentSeriesApi';
import occupationApi from '@/modules/occupations/services/occupationApi';
import apiClient from '@/services/apiClient';

const Albums = () => {
  const [loading, setLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [filters, setFilters] = useState({
    assessmentCenter: '',
    assessmentCenterBranch: '',
    assessmentSeries: '',
    registrationCategory: '',
    occupation: '',
    level: '',
  });

  // Load user from localStorage
  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setCurrentUser(user);

        // Auto-select center for center representatives
        if (user.user_type === 'center_representative' && user.center_representative?.assessment_center) {
          setFilters(prev => ({
            ...prev,
            assessmentCenter: user.center_representative.assessment_center.id.toString(),
            assessmentCenterBranch: user.center_representative.assessment_center_branch?.id?.toString() || ''
          }));
        }
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  // Fetch assessment centers
  const { data: centersData } = useQuery({
    queryKey: ['assessment-centers'],
    queryFn: () => assessmentCenterApi.getAll({ page_size: 1000 }),
  });

  // Fetch assessment series
  const { data: seriesData } = useQuery({
    queryKey: ['assessment-series'],
    queryFn: () => assessmentSeriesApi.getAll({ page_size: 1000 }),
  });

  // Fetch branches for selected center
  const { data: branchesData } = useQuery({
    queryKey: ['assessment-center-branches', filters.assessmentCenter],
    queryFn: () => assessmentCenterApi.branches.getByCenter(filters.assessmentCenter),
    enabled: !!filters.assessmentCenter,
  });

  // Fetch occupations (filtered by registration category)
  const { data: occupationsData } = useQuery({
    queryKey: ['occupations', filters.registrationCategory],
    queryFn: () => {
      const params = { page_size: 1000 };
      if (filters.registrationCategory) {
        // For modular, filter by has_modular=true
        // For formal and workers_pas, filter by occ_category
        if (filters.registrationCategory === 'modular') {
          params.has_modular = 'true';
        } else {
          params.occ_category = filters.registrationCategory;
        }
      }
      return occupationApi.getAll(params);
    },
    enabled: !!filters.registrationCategory,
  });

  const assessmentCenters = centersData?.data?.results || [];
  const assessmentSeries = seriesData?.data?.results || [];
  const occupations = occupationsData?.data?.results || [];

  // The API returns the array inside `results` for standard viewsets.
  // Alternatively, if it was custom, it might just be the data array. We handle both cases to be safe.
  const branches = Array.isArray(branchesData?.data) ? branchesData.data : (branchesData?.data?.results || []);

  // Check if selected center has branches
  const selectedCenter = assessmentCenters.find(c => c.id.toString() === filters.assessmentCenter);
  const hasBranches = selectedCenter?.has_branches || false;

  // Fetch levels for selected occupation (only for formal/workers_pas)
  const { data: levelsData } = useQuery({
    queryKey: ['occupation-levels', filters.occupation],
    queryFn: () => occupationApi.getLevels(filters.occupation),
    enabled: !!filters.occupation && (filters.registrationCategory === 'formal' || filters.registrationCategory === 'workers_pas'),
  });

  const levels = levelsData?.data?.levels || [];

  // Reset occupation and level when registration category changes
  const handleCategoryChange = (value) => {
    setFilters({
      ...filters,
      registrationCategory: value,
      occupation: '', // Reset occupation when category changes
      level: '' // Reset level when category changes
    });
  };

  // Reset level when occupation changes
  const handleOccupationChange = (value) => {
    setFilters({
      ...filters,
      occupation: value,
      level: '' // Reset level when occupation changes
    });
  };

  const handleGenerate = async () => {
    // Validate filters
    if (!filters.assessmentCenter || !filters.assessmentSeries || !filters.registrationCategory || !filters.occupation) {
      toast.error('Please select all required filters');
      return;
    }
    // Level is required only for formal (workers_pas can have null level)
    if (filters.registrationCategory === 'formal' && !filters.level) {
      toast.error('Please select a level for formal category');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        assessment_center: filters.assessmentCenter,
        assessment_series: filters.assessmentSeries,
        registration_category: filters.registrationCategory,
        occupation: filters.occupation,
      });

      if (filters.assessmentCenterBranch) {
        params.append('branch', filters.assessmentCenterBranch);
      }

      // Add level if selected (for formal/workers_pas)
      if (filters.level) {
        params.append('level', filters.level);
      }

      const response = await apiClient.get(`/reports/candidate-album/?${params.toString()}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'candidate_album.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Album generated successfully!');
    } catch (error) {
      console.error('Error generating album:', error);

      // Handle error - need to parse blob response as JSON for error messages
      let errorMessage = 'Failed to generate album. Please try again.';

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
          <BookImage className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Albums</h1>
            <p className="text-gray-600 mt-1">Generate Registration Lists</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter Options</h2>

        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-6`}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Center
            </label>
            <select
              value={filters.assessmentCenter}
              onChange={(e) => setFilters({ ...filters, assessmentCenter: e.target.value, assessmentCenterBranch: '' })}
              disabled={currentUser?.user_type === 'center_representative'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select Center</option>
              {assessmentCenters.map((center) => (
                <option key={center.id} value={center.id}>
                  {center.center_number} - {center.center_name}
                </option>
              ))}
            </select>
          </div>

          {hasBranches && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assessment Center Branch
              </label>
              <select
                value={filters.assessmentCenterBranch}
                onChange={(e) => setFilters({ ...filters, assessmentCenterBranch: e.target.value })}
                disabled={currentUser?.user_type === 'center_representative' && !!currentUser?.center_representative?.assessment_center_branch}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">All Branches</option>
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.branch_code} - {branch.branch_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Assessment Series
            </label>
            <select
              value={filters.assessmentSeries}
              onChange={(e) => setFilters({ ...filters, assessmentSeries: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
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

          {/* Level dropdown - only show for formal and workers_pas */}
          {(filters.registrationCategory === 'formal' || filters.registrationCategory === 'workers_pas') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Level {filters.registrationCategory === 'workers_pas' && <span className="text-gray-500 text-xs">(Optional)</span>}
              </label>
              <select
                value={filters.level}
                onChange={(e) => setFilters({ ...filters, level: e.target.value })}
                disabled={!filters.occupation}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              >
                <option value="">
                  {!filters.occupation
                    ? 'Select Occupation First'
                    : filters.registrationCategory === 'workers_pas'
                      ? 'All Levels'
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
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center space-x-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              <span>Generate Album</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Albums;
