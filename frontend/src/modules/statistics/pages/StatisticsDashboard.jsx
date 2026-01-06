import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Briefcase, Building, FileText, TrendingUp, Calendar, ChevronDown, ChevronRight } from 'lucide-react';
import candidateApi from '@modules/candidates/services/candidateApi';
import occupationApi from '@modules/occupations/services/occupationApi';
import assessmentCenterApi from '@modules/assessment-centers/services/assessmentCenterApi';
import assessmentSeriesApi from '@modules/assessment-series/services/assessmentSeriesApi';
import statisticsApi from '../services/statisticsApi';

const StatisticsDashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [expandedYears, setExpandedYears] = useState({});
  const [stats, setStats] = useState({
    totalCandidates: 0,
    totalOccupations: 0,
    totalCenters: 0,
    totalResults: 0,
    candidatesByGender: { male: 0, female: 0 },
    candidatesByCategory: { modular: 0, formal: 0, workers_pas: 0, unknown: 0 },
    specialNeeds: { withSpecialNeeds: 0, withoutSpecialNeeds: 0 },
    specialNeedsByGender: { male: 0, female: 0 },
    categoryByGender: [],
    assessmentSeries: []
  });

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      
      // Fetch data - use candidate statistics endpoint for accurate counts
      const [candidateStatsRes, candidatesRes, occupationsRes, centersRes, seriesRes] = await Promise.all([
        statisticsApi.getCandidatesStats().catch(() => ({ data: null })),
        candidateApi.getAll({ page_size: 1 }),
        occupationApi.getAll({ page_size: 1 }),
        assessmentCenterApi.getAll({ page_size: 1 }),
        assessmentSeriesApi.getAll()
      ]);

      // Get total counts from API response count field (accurate even with pagination)
      const totalCandidates = candidatesRes.data?.count || 0;
      const totalOccupations = occupationsRes.data?.count || 0;
      const totalCenters = centersRes.data?.count || 0;
      
      // Use backend statistics if available, otherwise show basic totals
      const candidateStats = candidateStatsRes.data || {};
      const genderStats = candidateStats.by_gender || { male: 0, female: 0 };
      const categoryStats = candidateStats.by_category || { modular: 0, formal: 0, workers_pas: 0 };
      const specialNeedsStats = {
        overall: { 
          withSpecialNeeds: candidateStats.with_disability || 0, 
          withoutSpecialNeeds: totalCandidates - (candidateStats.with_disability || 0)
        },
        byGender: { male: 0, female: 0 }
      };

      setStats({
        totalCandidates: totalCandidates,
        totalOccupations: totalOccupations,
        totalCenters: totalCenters,
        totalResults: 46151,
        candidatesByGender: genderStats,
        candidatesByCategory: categoryStats,
        specialNeeds: specialNeedsStats.overall,
        specialNeedsByGender: specialNeedsStats.byGender,
        categoryByGender: [],
        assessmentSeries: []
      });
    } catch (error) {
      console.error('Error fetching statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateGenderStats = (candidates) => {
    const male = candidates.filter(c => c.gender?.toLowerCase() === 'male').length;
    const female = candidates.filter(c => c.gender?.toLowerCase() === 'female').length;
    return { male, female };
  };

  const calculateCategoryStats = (candidates) => {
    const modular = candidates.filter(c => c.registration_category?.toLowerCase() === 'modular').length;
    const formal = candidates.filter(c => c.registration_category?.toLowerCase() === 'formal').length;
    const workers_pas = candidates.filter(c => c.registration_category?.toLowerCase() === 'workers_pas').length;
    const unknown = candidates.filter(c => !c.registration_category).length;
    return { modular, formal, workers_pas, unknown };
  };

  const calculateSpecialNeedsStats = (candidates) => {
    const withSpecialNeeds = candidates.filter(c => c.has_special_needs).length;
    const withoutSpecialNeeds = candidates.filter(c => !c.has_special_needs).length;
    
    const maleWithSpecialNeeds = candidates.filter(c => c.has_special_needs && c.gender?.toLowerCase() === 'male').length;
    const femaleWithSpecialNeeds = candidates.filter(c => c.has_special_needs && c.gender?.toLowerCase() === 'female').length;
    
    return {
      overall: { withSpecialNeeds, withoutSpecialNeeds },
      byGender: { male: maleWithSpecialNeeds, female: femaleWithSpecialNeeds }
    };
  };

  const calculateCategoryByGender = (candidates) => {
    const categories = ['modular', 'formal', 'workers_pas'];
    const categoryLabels = {
      'modular': 'Modular',
      'formal': 'Formal',
      'workers_pas': "Worker's PAS"
    };
    return categories.map(category => {
      const male = candidates.filter(c => 
        c.registration_category?.toLowerCase() === category && c.gender?.toLowerCase() === 'male'
      ).length;
      const female = candidates.filter(c => 
        c.registration_category?.toLowerCase() === category && c.gender?.toLowerCase() === 'female'
      ).length;
      return { category, label: categoryLabels[category], male, female, total: male + female };
    });
  };

  const calculateSeriesStats = (candidates, series) => {
    return series.map(s => {
      // Filter candidates who have enrollments in this series
      const seriesCandidates = candidates.filter(c => 
        c.enrollments && c.enrollments.some(e => e.assessment_series === s.id)
      );
      const male = seriesCandidates.filter(c => c.gender?.toLowerCase() === 'male').length;
      const female = seriesCandidates.filter(c => c.gender?.toLowerCase() === 'female').length;
      
      // Get unique occupations from enrollments for this series
      const occupationIds = new Set();
      seriesCandidates.forEach(c => {
        c.enrollments?.forEach(e => {
          if (e.assessment_series === s.id && e.occupation) {
            occupationIds.add(e.occupation);
          }
        });
      });
      
      const specialNeeds = seriesCandidates.filter(c => c.has_special_needs).length;
      
      return {
        id: s.id,
        name: s.name,
        year: new Date(s.start_date).getFullYear(),
        totalCandidates: seriesCandidates.length,
        male,
        female,
        occupations: occupationIds.size,
        specialNeeds
      };
    });
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

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Statistics Dashboard</h1>
        <p className="text-gray-600 mt-1">Comprehensive overview of EMIS system metrics and analytics</p>
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
              <p className="text-sm text-gray-600">Total Occupations</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalOccupations}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <Briefcase className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Assessment Centers</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalCenters}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-lg">
              <Building className="w-8 h-8 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Results</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalResults.toLocaleString()}</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <FileText className="w-8 h-8 text-purple-600" />
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
                  <div className="w-3 h-3 rounded-full bg-pink-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Female</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.candidatesByGender.female.toLocaleString()} candidates ({getPercentage(stats.candidatesByGender.female, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-pink-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.candidatesByGender.female, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Male</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.candidatesByGender.male.toLocaleString()} candidates ({getPercentage(stats.candidatesByGender.male, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.candidatesByGender.male, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Special Needs Status */}
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Special Needs Status</h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
                  <span className="text-sm text-gray-700">With Special Needs</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.specialNeeds.withSpecialNeeds.toLocaleString()} candidates ({getPercentage(stats.specialNeeds.withSpecialNeeds, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.specialNeeds.withSpecialNeeds, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Without Special Needs</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.specialNeeds.withoutSpecialNeeds.toLocaleString()} candidates ({getPercentage(stats.specialNeeds.withoutSpecialNeeds, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.specialNeeds.withoutSpecialNeeds, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Candidates by Registration Category */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Candidates by Registration Category</h2>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                <span className="text-sm text-gray-700">Modular</span>
              </div>
              <span className="text-sm font-medium text-blue-600">
                {stats.candidatesByCategory.modular.toLocaleString()} candidates ({getPercentage(stats.candidatesByCategory.modular, stats.totalCandidates)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full" 
                style={{ width: `${getPercentage(stats.candidatesByCategory.modular, stats.totalCandidates)}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                <span className="text-sm text-gray-700">Formal</span>
              </div>
              <span className="text-sm font-medium text-blue-600">
                {stats.candidatesByCategory.formal.toLocaleString()} candidates ({getPercentage(stats.candidatesByCategory.formal, stats.totalCandidates)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full" 
                style={{ width: `${getPercentage(stats.candidatesByCategory.formal, stats.totalCandidates)}%` }}
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
                {stats.candidatesByCategory.workers_pas.toLocaleString()} candidates ({getPercentage(stats.candidatesByCategory.workers_pas, stats.totalCandidates)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-orange-500 h-2 rounded-full" 
                style={{ width: `${getPercentage(stats.candidatesByCategory.workers_pas, stats.totalCandidates)}%` }}
              ></div>
            </div>
          </div>

          {stats.candidatesByCategory.unknown > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-gray-500 mr-2"></div>
                  <span className="text-sm text-gray-700">Unknown</span>
                </div>
                <span className="text-sm font-medium text-blue-600">
                  {stats.candidatesByCategory.unknown.toLocaleString()} candidates ({getPercentage(stats.candidatesByCategory.unknown, stats.totalCandidates)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gray-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.candidatesByCategory.unknown, stats.totalCandidates)}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Special Needs Candidates by Gender */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Special Needs Candidates by Gender</h2>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-red-500 mr-2"></div>
                <span className="text-sm text-gray-700">Male with Special Needs</span>
              </div>
              <span className="text-sm font-medium text-blue-600">
                {stats.specialNeedsByGender.male.toLocaleString()} candidates ({getPercentage(stats.specialNeedsByGender.male, stats.specialNeeds.withSpecialNeeds)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-red-500 h-2 rounded-full" 
                style={{ width: `${getPercentage(stats.specialNeedsByGender.male, stats.specialNeeds.withSpecialNeeds)}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-pink-500 mr-2"></div>
                <span className="text-sm text-gray-700">Female with Special Needs</span>
              </div>
              <span className="text-sm font-medium text-blue-600">
                {stats.specialNeedsByGender.female.toLocaleString()} candidates ({getPercentage(stats.specialNeedsByGender.female, stats.specialNeeds.withSpecialNeeds)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-pink-500 h-2 rounded-full" 
                  style={{ width: `${getPercentage(stats.specialNeedsByGender.female, stats.specialNeeds.withSpecialNeeds)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Registration Category by Gender Table */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Registration Category by Gender</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stats.categoryByGender.map((row) => (
                <tr key={row.category}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-2 ${
                        row.category === 'modular' ? 'bg-green-500' :
                        row.category === 'formal' ? 'bg-blue-500' : 'bg-orange-500'
                      }`}></div>
                      <span className="text-sm font-medium text-gray-900">{row.label}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.male.toLocaleString()} ({getPercentage(row.male, row.total)}%)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row.female.toLocaleString()} ({getPercentage(row.female, row.total)}%)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {row.total.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assessment Series */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Assessment Series</h2>
            <p className="text-sm text-gray-600">Organized by year. Click to expand/collapse year details.</p>
          </div>
        </div>

        {/* Group by year */}
        {Object.entries(
          stats.assessmentSeries.reduce((acc, series) => {
            if (!acc[series.year]) acc[series.year] = [];
            acc[series.year].push(series);
            return acc;
          }, {})
        ).sort(([a], [b]) => b - a).map(([year, yearSeries]) => {
          const isExpanded = expandedYears[year];
          const toggleYear = () => {
            setExpandedYears(prev => ({
              ...prev,
              [year]: !prev[year]
            }));
          };

          return (
            <div key={year} className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
              {/* Year Header - Clickable */}
              <div 
                className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={toggleYear}
              >
                <div className="flex items-center space-x-3">
                  {isExpanded ? (
                    <ChevronDown className="w-5 h-5 text-gray-600" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-600" />
                  )}
                  <h3 className="text-lg font-semibold text-gray-900">{year}</h3>
                  <span className="text-sm text-gray-600">
                    Yearly overview of assessment series
                  </span>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <p className="text-sm font-bold text-gray-900">
                      {yearSeries.reduce((sum, s) => sum + s.totalCandidates, 0).toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-600">candidates</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-gray-900">
                      {yearSeries.reduce((sum, s) => sum + s.male, 0).toLocaleString()}/{yearSeries.reduce((sum, s) => sum + s.female, 0).toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-600">Male / Female</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-gray-900">
                      {yearSeries.reduce((sum, s) => sum + s.specialNeeds, 0)}
                    </p>
                    <p className="text-xs text-gray-600">special needs</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-gray-900">
                      {Math.max(...yearSeries.map(s => s.occupations))}
                    </p>
                    <p className="text-xs text-gray-600">occupations</p>
                  </div>
                </div>
              </div>

              {/* Expandable Content */}
              {isExpanded && (
                <div className="p-4 bg-white">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Series Name</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Candidates</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Male</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Female</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Occupations</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Special Needs</th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {yearSeries.map((series) => (
                          <tr 
                            key={series.id} 
                            className="hover:bg-gray-50 cursor-pointer"
                            onClick={() => navigate(`/statistics/series/${series.id}`)}
                          >
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {series.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {series.totalCandidates.toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {series.male.toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {series.female.toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {series.occupations}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {series.specialNeeds}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/statistics/series/${series.id}`);
                                }}
                                className="text-blue-600 hover:text-blue-900 inline-flex items-center"
                              >
                                <TrendingUp className="w-4 h-4 mr-1" />
                                View Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StatisticsDashboard;
