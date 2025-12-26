import apiClient from '@services/apiClient';

const CENTERS_BASE = '/assessment-centers/centers';
const BRANCHES_BASE = '/assessment-centers/branches';

export const assessmentCenterApi = {
  // Assessment Centers
  getAll: (params = {}) => apiClient.get(`${CENTERS_BASE}/`, { params }),
  getById: (id) => apiClient.get(`${CENTERS_BASE}/${id}/`),
  create: (data) => apiClient.post(`${CENTERS_BASE}/`, data),
  update: (id, data) => apiClient.put(`${CENTERS_BASE}/${id}/`, data),
  delete: (id) => apiClient.delete(`${CENTERS_BASE}/${id}/`),
  getByDistrict: (districtId) => apiClient.get(`${CENTERS_BASE}/`, { params: { district: districtId } }),
  getCandidatesCount: (id) => apiClient.get(`${CENTERS_BASE}/${id}/candidates-count/`),

  // Center Branches
  branches: {
    getAll: (params = {}) => apiClient.get(`${BRANCHES_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${BRANCHES_BASE}/${id}/`),
    create: (data) => apiClient.post(`${BRANCHES_BASE}/`, data),
    update: (id, data) => apiClient.put(`${BRANCHES_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${BRANCHES_BASE}/${id}/`),
    getByCenter: (centerId) => apiClient.get(`${BRANCHES_BASE}/`, { params: { assessment_center: centerId } }),
  },
};

export default assessmentCenterApi;
