import apiClient from '../../../services/apiClient';

const ditLegacyApi = {
  search: (params) => apiClient.get('/dit-legacy/search/', { params }),
  getPerson: (personId) => apiClient.get(`/dit-legacy/person/${personId}/`),
  getPersonResults: (personId, params) =>
    apiClient.get(`/dit-legacy/person/${personId}/results/`, { params }),
  updatePerson: (personId, data) =>
    apiClient.patch(`/dit-legacy/person/${personId}/update/`, data),
  uploadPhoto: (personId, file) => {
    const formData = new FormData();
    formData.append('passport_photo', file);
    return apiClient.patch(`/dit-legacy/person/${personId}/update/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getAuditLogs: (personId) =>
    apiClient.get(`/dit-legacy/person/${personId}/audit-logs/`),
};

export default ditLegacyApi;
