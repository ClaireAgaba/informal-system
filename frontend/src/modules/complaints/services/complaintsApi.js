import apiClient from '../../../services/apiClient';

const BASE_URL = '/complaints';

export const complaintsApi = {
  // Get all complaints with filters
  getComplaints: (params = {}) => {
    return apiClient.get(`${BASE_URL}/complaints/`, { params });
  },

  // Get single complaint by ID
  getComplaint: (id) => {
    return apiClient.get(`${BASE_URL}/complaints/${id}/`);
  },

  // Create new complaint
  createComplaint: (data) => {
    return apiClient.post(`${BASE_URL}/complaints/`, data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Update complaint
  updateComplaint: (id, data) => {
    return apiClient.patch(`${BASE_URL}/complaints/${id}/`, data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Delete complaint
  deleteComplaint: (id) => {
    return apiClient.delete(`${BASE_URL}/complaints/${id}/`);
  },

  // Assign complaint to helpdesk team
  assignComplaint: (id, helpdeskTeamId) => {
    return apiClient.post(`${BASE_URL}/complaints/${id}/assign/`, {
      helpdesk_team: helpdeskTeamId,
    });
  },

  // Update complaint status
  updateStatus: (id, status) => {
    return apiClient.post(`${BASE_URL}/complaints/${id}/update_status/`, {
      status,
    });
  },

  // Add team response
  addResponse: (id, response) => {
    return apiClient.post(`${BASE_URL}/complaints/${id}/add_response/`, {
      team_response: response,
    });
  },

  // Get complaint statistics
  getStatistics: () => {
    return apiClient.get(`${BASE_URL}/complaints/statistics/`);
  },

  // Get complaint categories
  getCategories: () => {
    return apiClient.get(`${BASE_URL}/categories/`);
  },

  // Upload attachment
  uploadAttachment: (complaintId, file) => {
    const formData = new FormData();
    formData.append('complaint', complaintId);
    formData.append('file', file);
    return apiClient.post(`${BASE_URL}/attachments/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export default complaintsApi;
