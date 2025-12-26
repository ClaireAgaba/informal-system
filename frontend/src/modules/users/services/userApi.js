import apiClient from '@services/apiClient';

const STAFF_BASE = '/users/staff';
const SUPPORT_STAFF_BASE = '/users/support-staff';
const DEPARTMENTS_BASE = '/users/departments';

export const userApi = {
  // Staff
  staff: {
    getAll: (params = {}) => apiClient.get(`${STAFF_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${STAFF_BASE}/${id}/`),
    create: (data) => apiClient.post(`${STAFF_BASE}/`, data),
    update: (id, data) => apiClient.put(`${STAFF_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${STAFF_BASE}/${id}/`),
  },

  // Support Staff
  supportStaff: {
    getAll: (params = {}) => apiClient.get(`${SUPPORT_STAFF_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${SUPPORT_STAFF_BASE}/${id}/`),
    create: (data) => apiClient.post(`${SUPPORT_STAFF_BASE}/`, data),
    update: (id, data) => apiClient.put(`${SUPPORT_STAFF_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${SUPPORT_STAFF_BASE}/${id}/`),
  },

  // Departments
  departments: {
    getAll: () => apiClient.get(`${DEPARTMENTS_BASE}/`),
  },
};

export default userApi;
