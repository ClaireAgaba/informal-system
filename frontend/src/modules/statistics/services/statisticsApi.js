import apiClient from '@services/apiClient';

const statisticsApi = {
  // Overall statistics
  getOverallStats: () => apiClient.get('/statistics/overall/'),

  // Candidates statistics
  getCandidatesStats: (params = {}) => apiClient.get('/candidates/candidates/statistics/', { params }),
  getCandidatesByGender: () => apiClient.get('/statistics/candidates/by-gender/'),
  getCandidatesByCategory: () => apiClient.get('/statistics/candidates/by-category/'),
  getCandidatesBySpecialNeeds: () => apiClient.get('/statistics/candidates/by-special-needs/'),

  // Assessment Series statistics
  getAssessmentSeriesStats: () => apiClient.get('/statistics/assessment-series/'),
  getSeriesDetail: (seriesId) => apiClient.get(`/statistics/assessment-series/${seriesId}/`),

  // Occupations statistics
  getOccupationsStats: () => apiClient.get('/statistics/occupations/'),

  // Assessment Centers statistics
  getCentersStats: () => apiClient.get('/statistics/centers/'),

  // Results statistics
  getResultsStats: (params = {}) => apiClient.get('/statistics/results/', { params }),

  // Assessment Series statistics
  getAssessmentSeriesList: () => apiClient.get('/statistics/series/'),
  getSeriesResults: (seriesId) => apiClient.get(`/statistics/series/${seriesId}/results/`),

  // Special needs and refugee analytics  
  getSpecialNeedsAnalytics: (params = {}) => apiClient.get('/statistics/special-needs/', { params }),
};

export default statisticsApi;
