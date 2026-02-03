import apiClient from '../../../services/apiClient';

const ditLegacyApi = {
  search: (params) => apiClient.get('/dit-legacy/search/', { params }),
  getPerson: (personId) => apiClient.get(`/dit-legacy/person/${personId}/`),
  getPersonResults: (personId, params) =>
    apiClient.get(`/dit-legacy/person/${personId}/results/`, { params }),
};

export default ditLegacyApi;
