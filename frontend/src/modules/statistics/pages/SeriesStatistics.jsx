import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Users, Briefcase, Download, FileText, TrendingUp } from 'lucide-react';
import candidateApi from '@modules/candidates/services/candidateApi';
import assessmentSeriesApi from '@modules/assessment-series/services/assessmentSeriesApi';

const SeriesStatistics = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [series, setSeries] = useState(null);
  const [stats, setStats] = useState({
    totalCandidates: 0,
    male: 0,
    female: 0,
    occupations: 0,
    specialNeeds: 0,
    byGender: { male: 0, female: 0 },
    byCategory: { formal: 0, workers_pas: 0, modular: 0 },
    candidates: []
  });

  useEffect(() => {
    fetchSeriesStatistics();
  }, [id]);

  const fetchSeriesStatistics = async () => {
    try {
      setLoading(true);
      
      // Fetch series details and all candidates
      const [seriesRes, candidatesRes] = await Promise.all([
        assessmentSeriesApi.getById(id),
        candidateApi.getAll({ page_size: 10000 })
      ]);

      const seriesData = seriesRes.data;
      const allCandidates = candidatesRes.data.results || candidatesRes.data || [];
      
      // Filter candidates who are enrolled in this specific series
      const candidates = allCandidates.filter(c => 
        c.enrollments && c.enrollments.some(e => e.assessment_series === parseInt(id))
      );

      // Calculate statistics
      const male = candidates.filter(c => c.gender?.toLowerCase() === 'male').length;
      const female = candidates.filter(c => c.gender?.toLowerCase() === 'female').length;
      const specialNeeds = candidates.filter(c => c.has_special_needs).length;
      
      // Get unique occupations from enrollments for this series
      const occupationIds = new Set();
      candidates.forEach(c => {
        c.enrollments?.forEach(e => {
          if (e.assessment_series === parseInt(id) && e.occupation) {
            occupationIds.add(e.occupation);
          }
        });
      });

      const formal = candidates.filter(c => c.registration_category?.toLowerCase() === 'formal').length;
      const workers_pas = candidates.filter(c => c.registration_category?.toLowerCase() === 'workers_pas').length;
      const modular = candidates.filter(c => c.registration_category?.toLowerCase() === 'modular').length;

      setSeries(seriesData);
      setStats({
        totalCandidates: candidates.length,
        male,
        female,
        occupations: occupationIds.size,
        specialNeeds,
        byGender: { male, female },
        byCategory: { formal, workers_pas, modular },
        candidates
      });
    } catch (error) {
      console.error('Error fetching series statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = () => {
    // Navigate to report generation page
    navigate(`/statistics/series/${id}/report`);
  };

  const getPercentage = (value, total) => {
    if (total === 0) return '0.0';
    return ((value / total) * 100).toFixed(1);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!series) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Series not found</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/statistics')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Statistics
        </button>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessment Series: {series.name}</h1>
            <p className="text-gray-600 mt-1">Detailed breakdown of candidates assessed in {series.name}</p>
          </div>
          <button
            onClick={handleGenerateReport}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="w-5 h-5 mr-2" />
            Generate Performance Report
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Candidates</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalCandidates.toLocaleString()}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Occupations</p>
              <p className="text-3xl font-bold text-gray-900">{stats.occupations}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <Briefcase className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Male Candidates</p>
              <p className="text-3xl font-bold text-gray-900">{stats.male.toLocaleString()}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Female Candidates</p>
              <p className="text-3xl font-bold text-gray-900">{stats.female.toLocaleString()}</p>
            </div>
            <div className="bg-pink-100 p-3 rounded-lg">
              <Users className="w-8 h-8 text-pink-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Candidates by Gender */}
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Candidates by Gender</h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Male</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.male.toLocaleString()} candidates ({getPercentage(stats.male, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.male, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-pink-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Female</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.female.toLocaleString()} candidates ({getPercentage(stats.female, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-pink-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.female, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Registration Categories */}
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Registration Categories</h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Formal</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.byCategory.formal.toLocaleString()} candidates ({getPercentage(stats.byCategory.formal, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.byCategory.formal, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-orange-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Worker's PAS</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.byCategory.workers_pas.toLocaleString()} candidates ({getPercentage(stats.byCategory.workers_pas, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-orange-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.byCategory.workers_pas, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Modular</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.byCategory.modular.toLocaleString()} candidates ({getPercentage(stats.byCategory.modular, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.byCategory.modular, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Series Information */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Series Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Series Name</label>
            <p className="text-gray-900 font-medium">{series.name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">Start Date</label>
            <p className="text-gray-900">{new Date(series.start_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">End Date</label>
            <p className="text-gray-900">{new Date(series.end_date).toLocaleDateString()}</p>
          </div>
          {series.description && (
            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-500 mb-1">Description</label>
              <p className="text-gray-900">{series.description}</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={handleGenerateReport}
            className="flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="w-5 h-5 mr-2" />
            Generate Performance Report
          </button>
          <button
            onClick={() => navigate(`/candidates?assessment_series=${id}`)}
            className="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Users className="w-5 h-5 mr-2" />
            View All Candidates
          </button>
          <button
            onClick={() => navigate(`/assessment-series/${id}`)}
            className="flex items-center justify-center px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <TrendingUp className="w-5 h-5 mr-2" />
            View Series Details
          </button>
        </div>
      </div>
    </div>
  );
};

export default SeriesStatistics;
