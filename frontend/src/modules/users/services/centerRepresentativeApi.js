import apiClient from '@services/apiClient';

const BASE_URL = '/users/center-representatives';

export const centerRepresentativeApi = {
  getAll: (params = {}) => {
    return apiClient.get(BASE_URL + '/', { params });
  },

  getById: (id) => {
    return apiClient.get(`${BASE_URL}/${id}/`);
  },

  create: (data) => {
    return apiClient.post(BASE_URL + '/', data);
  },

  update: (id, data) => {
    return apiClient.put(`${BASE_URL}/${id}/`, data);
  },

  partialUpdate: (id, data) => {
    return apiClient.patch(`${BASE_URL}/${id}/`, data);
  },

  delete: (id) => {
    return apiClient.delete(`${BASE_URL}/${id}/`);
  },

  resetPassword: (id) => {
    return apiClient.post(`${BASE_URL}/${id}/reset_password/`);
  },

  activate: (id) => {
    return apiClient.post(`${BASE_URL}/${id}/activate/`);
  },

  deactivate: (id) => {
    return apiClient.post(`${BASE_URL}/${id}/deactivate/`);
  },

  getActive: () => {
    return apiClient.get(`${BASE_URL}/active/`);
  }
};

export default centerRepresentativeApi;
