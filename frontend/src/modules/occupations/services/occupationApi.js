import apiClient from '@services/apiClient';

const OCCUPATIONS_BASE = 'occupations';
const SECTORS_BASE = 'occupations/sectors';
const LEVELS_BASE = 'occupations/levels';
const MODULES_BASE = 'occupations/modules';
const PAPERS_BASE = 'occupations/papers';
const LWAS_BASE = 'occupations/module-lwas';

export const occupationApi = {
  // Occupations
  getAll: (params = {}) => apiClient.get(`${OCCUPATIONS_BASE}/occupations/`, { params }),
  getById: (id) => apiClient.get(`${OCCUPATIONS_BASE}/occupations/${id}/`),
  create: (data) => apiClient.post(`${OCCUPATIONS_BASE}/occupations/`, data),
  update: (id, data) => apiClient.put(`${OCCUPATIONS_BASE}/occupations/${id}/`, data),
  delete: (id) => apiClient.delete(`${OCCUPATIONS_BASE}/occupations/${id}/`),
  getBySector: (sectorId) => apiClient.get(`${OCCUPATIONS_BASE}/occupations/`, { params: { sector: sectorId } }),

  // Sectors
  sectors: {
    getAll: (params = {}) => apiClient.get(`${SECTORS_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${SECTORS_BASE}/${id}/`),
    create: (data) => apiClient.post(`${SECTORS_BASE}/`, data),
    update: (id, data) => apiClient.put(`${SECTORS_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${SECTORS_BASE}/${id}/`),
    getOccupations: (id) => apiClient.get(`${SECTORS_BASE}/${id}/occupations/`),
  },

  // Occupation Levels
  levels: {
    getAll: (params = {}) => apiClient.get(`${LEVELS_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${LEVELS_BASE}/${id}/`),
    create: (data) => apiClient.post(`${LEVELS_BASE}/`, data),
    update: (id, data) => apiClient.put(`${LEVELS_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${LEVELS_BASE}/${id}/`),
    getByOccupation: (occupationId) => apiClient.get(`${LEVELS_BASE}/`, { params: { occupation: occupationId } }),
  },

  // Occupation Modules
  modules: {
    getAll: (params = {}) => apiClient.get(`${MODULES_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${MODULES_BASE}/${id}/`),
    create: (data) => apiClient.post(`${MODULES_BASE}/`, data),
    update: (id, data) => apiClient.put(`${MODULES_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${MODULES_BASE}/${id}/`),
    getByOccupation: (occupationId) => apiClient.get(`${MODULES_BASE}/by-occupation/`, { params: { occupation: occupationId } }),
    getLevelsByOccupation: (occupationId) => apiClient.get(`${MODULES_BASE}/levels-by-occupation/`, { params: { occupation: occupationId } }),
  },

  // Occupation Papers
  papers: {
    getAll: (params = {}) => apiClient.get(`${PAPERS_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${PAPERS_BASE}/${id}/`),
    create: (data) => apiClient.post(`${PAPERS_BASE}/`, data),
    update: (id, data) => apiClient.put(`${PAPERS_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${PAPERS_BASE}/${id}/`),
    getByOccupation: (occupationId) => apiClient.get(`${PAPERS_BASE}/by-occupation/`, { params: { occupation: occupationId } }),
    getByLevel: (levelId) => apiClient.get(`${PAPERS_BASE}/by-level/`, { params: { level: levelId } }),
  },

  // Module LWAs
  lwas: {
    getAll: (params = {}) => apiClient.get(`${LWAS_BASE}/`, { params }),
    getById: (id) => apiClient.get(`${LWAS_BASE}/${id}/`),
    create: (data) => apiClient.post(`${LWAS_BASE}/`, data),
    update: (id, data) => apiClient.put(`${LWAS_BASE}/${id}/`, data),
    delete: (id) => apiClient.delete(`${LWAS_BASE}/${id}/`),
    getByModule: (moduleId) => apiClient.get(`${LWAS_BASE}/by-module/`, { params: { module: moduleId } }),
  },
};

export default occupationApi;
