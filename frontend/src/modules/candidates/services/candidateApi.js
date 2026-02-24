import apiClient from '@services/apiClient';

const CANDIDATES_BASE = '/candidates';

export const candidateApi = {
  // Get all candidates with optional filters
  getAll: (params = {}) => {
    return apiClient.get(CANDIDATES_BASE, { params });
  },

  // Get single candidate by ID
  getById: (id) => {
    return apiClient.get(`${CANDIDATES_BASE}/${id}/`);
  },

  // Create new candidate
  create: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/`, data);
  },

  // Update candidate
  update: (id, data) => {
    return apiClient.put(`${CANDIDATES_BASE}/${id}/`, data);
  },

  // Partial update candidate
  patch: (id, data) => {
    return apiClient.patch(`${CANDIDATES_BASE}/${id}/`, data);
  },

  // Delete candidate
  delete: (id) => {
    return apiClient.delete(`${CANDIDATES_BASE}/${id}/`);
  },


  // Verify candidate
  verify: (id) => {
    return apiClient.post(`${CANDIDATES_BASE}/${id}/verify/`);
  },

  // Decline candidate
  decline: (id, reason) => {
    return apiClient.post(`${CANDIDATES_BASE}/${id}/decline/`, { reason });
  },

  // Mark payment as cleared
  clearPayment: (id, paymentData) => {
    return apiClient.post(`${CANDIDATES_BASE}/${id}/clear-payment/`, paymentData);
  },

  // Get candidates by assessment center
  getByCenter: (centerId) => {
    return apiClient.get(`${CANDIDATES_BASE}`, { params: { assessment_center: centerId } });
  },

  // Get candidates by occupation
  getByOccupation: (occupationId) => {
    return apiClient.get(`${CANDIDATES_BASE}`, { params: { occupation: occupationId } });
  },

  // Get candidates by registration category
  getByCategory: (category) => {
    return apiClient.get(`${CANDIDATES_BASE}`, { params: { registration_category: category } });
  },

  getActivity: (id) => apiClient.get(`${CANDIDATES_BASE}/${id}/activity/`),

  // Search candidates
  search: (query) => {
    return apiClient.get(`${CANDIDATES_BASE}`, { params: { search: query } });
  },

  getNationalities: () => apiClient.get(`${CANDIDATES_BASE}/nationalities/`),

  // Enrollment endpoints
  getEnrollmentOptions: (id) => {
    return apiClient.get(`${CANDIDATES_BASE}/${id}/enrollment-options/`);
  },

  getEnrollments: (id) => {
    return apiClient.get(`${CANDIDATES_BASE}/${id}/enrollments/`);
  },

  enroll: (id, data) => {
    return apiClient.post(`${CANDIDATES_BASE}/${id}/enroll/`, data);
  },

  // De-enroll from an enrollment (candidateId is unused, kept for API compatibility)
  deEnroll: (candidateId, enrollmentId) => apiClient.delete(`${CANDIDATES_BASE}/enrollments/${enrollmentId}/`),

  // Submit a draft candidate
  submit: (id) => apiClient.post(`${CANDIDATES_BASE}/${id}/submit/`),

  // Upload passport photo
  uploadPhoto: (id, photoFile) => {
    const formData = new FormData();
    formData.append('photo', photoFile);
    return apiClient.post(`${CANDIDATES_BASE}/${id}/upload_photo/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Delete passport photo
  deletePhoto: (id) => {
    return apiClient.delete(`${CANDIDATES_BASE}/${id}/delete_photo/`);
  },

  // Upload document (identification or qualification)
  uploadDocument: (id, documentFile, documentType) => {
    const formData = new FormData();
    formData.append('document', documentFile);
    formData.append('document_type', documentType);
    return apiClient.post(`${CANDIDATES_BASE}/${id}/upload_document/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Generate payment code
  generatePaymentCode: (id) => apiClient.post(`${CANDIDATES_BASE}/${id}/generate_payment_code/`),

  // Mark payment as cleared
  markPaymentCleared: (id) => apiClient.post(`${CANDIDATES_BASE}/${id}/mark_payment_cleared/`),

  // Get candidate results
  getResults: (id) => apiClient.get(`${CANDIDATES_BASE}/${id}/results/`),

  // Add modular results (moved to results app)
  addResults: (candidateId, data) => apiClient.post(`/results/modular/add/`, {
    candidate_id: candidateId,
    ...data
  }),

  // Get enrollment modules for a candidate and series (moved to results app)
  getEnrollmentModules: (candidateId, seriesId) => apiClient.get(`/results/modular/enrollment-modules/?candidate_id=${candidateId}&series_id=${seriesId}`),

  // Update modular results (moved to results app)
  updateResults: (candidateId, data) => apiClient.put(`/results/modular/update/`, {
    candidate_id: candidateId,
    ...data
  }),

  // Get verified results PDF (moved to results app)
  getVerifiedResultsPDF: (candidateId, registrationCategory = 'modular') => {
    if (registrationCategory === 'workers_pas') {
      return `/api/results/workers-pas/verified-pdf/?candidate_id=${candidateId}`;
    }
    // Both modular and formal use the same endpoint
    return `/api/results/modular/verified-pdf/?candidate_id=${candidateId}`;
  },

  getTranscriptPDF: (candidateId, registrationCategory = 'modular') => {
    if (registrationCategory === 'workers_pas') {
      return `/api/results/workers-pas/transcript-pdf/?candidate_id=${candidateId}`;
    }
    if (registrationCategory === 'formal') {
      return `/api/results/formal/transcript-pdf/?candidate_id=${candidateId}`;
    }
    return `/api/results/modular/transcript-pdf/?candidate_id=${candidateId}`;
  },

  // Formal results endpoints
  addFormalResults: (candidateId, data) => apiClient.post(`/results/formal/add/`, {
    candidate_id: candidateId,
    ...data
  }),

  updateFormalResults: (candidateId, data) => apiClient.put(`/results/formal/update/`, {
    candidate_id: candidateId,
    ...data
  }),

  listFormalResults: (candidateId, seriesId) => {
    const params = new URLSearchParams({ candidate_id: candidateId });
    if (seriesId) params.append('series_id', seriesId);
    return apiClient.get(`/results/formal/list/?${params.toString()}`);
  },

  // Export candidates to Excel
  export: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/export/`, data, {
      responseType: 'blob',
    });
  },

  // Bulk enroll candidates
  bulkEnroll: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-enroll/`, data);
  },

  // Bulk de-enroll candidates
  bulkDeEnroll: (candidateIds) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-de-enroll/`, { candidate_ids: candidateIds });
  },

  // Clear all results, enrollments, and fees for a candidate
  clearData: (candidateId) => {
    return apiClient.post(`${CANDIDATES_BASE}/${candidateId}/clear-data/`);
  },

  // Bulk clear all results, enrollments, and fees for multiple candidates
  bulkClearData: (candidateIds) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-clear-data/`, { candidate_ids: candidateIds });
  },

  // Change assessment series for a candidate
  changeSeries: (candidateId, newSeriesId) => {
    return apiClient.post(`${CANDIDATES_BASE}/${candidateId}/change-series/`, { new_series_id: newSeriesId });
  },

  // Change assessment center for a candidate
  changeCenter: (candidateId, newCenterId) => {
    return apiClient.post(`${CANDIDATES_BASE}/${candidateId}/change-center/`, { new_center_id: newCenterId });
  },

  // Change occupation for a candidate
  changeOccupation: (candidateId, newOccupationId) => {
    return apiClient.post(`${CANDIDATES_BASE}/${candidateId}/change-occupation/`, { new_occupation_id: newOccupationId });
  },

  // Bulk change occupation for multiple candidates
  bulkChangeOccupation: (candidateIds, newOccupationId) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-change-occupation/`, {
      candidate_ids: candidateIds,
      new_occupation_id: newOccupationId
    });
  },

  // Change registration category for a candidate
  changeRegistrationCategory: (candidateId, newRegCategory) => {
    return apiClient.post(`${CANDIDATES_BASE}/${candidateId}/change-registration-category/`, { new_registration_category: newRegCategory });
  },

  // Bulk change registration category for multiple candidates
  bulkChangeRegistrationCategory: (candidateIds, newRegCategory) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-change-registration-category/`, {
      candidate_ids: candidateIds,
      new_registration_category: newRegCategory
    });
  },

  // Bulk change assessment series for multiple candidates
  bulkChangeSeries: (candidateIds, newSeriesId) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-change-series/`, {
      candidate_ids: candidateIds,
      new_series_id: newSeriesId
    });
  },

  // Bulk change assessment center for multiple candidates
  bulkChangeCenter: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/bulk-change-center/`, data);
  },

  // Get all enrollments with filters
  getAllEnrollments: (params = {}) => {
    return apiClient.get(`${CANDIDATES_BASE}/enrollments/`, { params });
  },

  // Bulk change assessment series for enrollments
  bulkChangeEnrollmentSeries: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/enrollments/bulk-change-series/`, data);
  },

  // Bulk de-enroll by enrollment IDs
  bulkDeEnrollByEnrollment: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/enrollments/bulk-de-enroll/`, data);
  },

  // Bulk clear results, enrollments, and fees by enrollment IDs
  bulkClearEnrollmentData: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/enrollments/bulk-clear-data/`, data);
  },

  // Bulk update enrollments (set level/modules/papers)
  bulkUpdateEnrollment: (data) => {
    return apiClient.post(`${CANDIDATES_BASE}/enrollments/bulk-update/`, data);
  },
};

export default candidateApi;
