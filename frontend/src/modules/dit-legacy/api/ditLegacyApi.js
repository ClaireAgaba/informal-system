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

  // Registration History CRUD
  addRegistration: (personId, data) =>
    apiClient.post(`/dit-legacy/person/${personId}/registration/add/`, data),
  updateRegistration: (personId, registrationId, data) =>
    apiClient.patch(`/dit-legacy/person/${personId}/registration/${registrationId}/update/`, data),

  // Exam Results CRUD
  addExamResult: (personId, data) =>
    apiClient.post(`/dit-legacy/person/${personId}/exam-result/add/`, data),
  updateExamResult: (personId, resultId, data) =>
    apiClient.patch(`/dit-legacy/person/${personId}/exam-result/${resultId}/update/`, data),

  // Reference data
  getInstitutions: (params) => apiClient.get('/dit-legacy/institutions/', { params }),
  getCourses: () => apiClient.get('/dit-legacy/courses/'),
  getLevels: () => apiClient.get('/dit-legacy/levels/'),
};

export default ditLegacyApi;
