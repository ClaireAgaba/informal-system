import apiClient from '../../../services/apiClient';

const feesApi = {
  // Candidate Fees
  getCandidateFees: (params) => apiClient.get('/fees/candidate-fees/', { params }),
  getCandidateFee: (id) => apiClient.get(`/fees/candidate-fees/${id}/`),
  createCandidateFee: (data) => apiClient.post('/fees/candidate-fees/', data),
  updateCandidateFee: (id, data) => apiClient.put(`/fees/candidate-fees/${id}/`, data),
  patchCandidateFee: (id, data) => apiClient.patch(`/fees/candidate-fees/${id}/`, data),
  deleteCandidateFee: (id) => apiClient.delete(`/fees/candidate-fees/${id}/`),
  populateCandidateFees: () => apiClient.post('/fees/candidate-fees/populate_from_candidates/'),
  markAsPaid: (feeIds, paymentReference) => apiClient.post('/fees/candidate-fees/mark_as_paid/', { fee_ids: feeIds, payment_reference: paymentReference }),
  approvePayment: (feeIds) => apiClient.post('/fees/candidate-fees/approve_payment/', { fee_ids: feeIds }),

  // Center Fees
  getCenterFees: (params) => apiClient.get('/fees/center-fees/', { params }),
  getCenterFee: (id) => apiClient.get(`/fees/center-fees/${id}/`),
  createCenterFee: (data) => apiClient.post('/fees/center-fees/', data),
  updateCenterFee: (id, data) => apiClient.put(`/fees/center-fees/${id}/`, data),
  patchCenterFee: (id, data) => apiClient.patch(`/fees/center-fees/${id}/`, data),
  deleteCenterFee: (id) => apiClient.delete(`/fees/center-fees/${id}/`),
  populateCenterFees: () => apiClient.post('/fees/center-fees/populate_from_candidates/'),
  getCenterFeeCandidates: (id) => apiClient.get(`/fees/center-fees/${id}/candidates/`),
  getQuarterlyReport: (params) => apiClient.get('/fees/center-fees/quarterly_report/', { params, responseType: 'blob' }),
};

export default feesApi;
