import apiClient from '@services/apiClient';

const SERIES_BASE = '/assessment-series/series';

export const assessmentSeriesApi = {
  // Assessment Series
  getAll: (params = {}) => apiClient.get(`${SERIES_BASE}/`, { params }),
  getById: (id) => apiClient.get(`${SERIES_BASE}/${id}/`),
  create: (data) => apiClient.post(`${SERIES_BASE}/`, data),
  update: (id, data) => apiClient.put(`${SERIES_BASE}/${id}/`, data),
  delete: (id) => apiClient.delete(`${SERIES_BASE}/${id}/`),
  setCurrent: (id) => apiClient.post(`${SERIES_BASE}/${id}/set-current/`),
  releaseResults: (id) => apiClient.post(`${SERIES_BASE}/${id}/release-results/`),
  getByYear: (year) => apiClient.get(`${SERIES_BASE}/`, { params: { year } }),
};

export default assessmentSeriesApi;
