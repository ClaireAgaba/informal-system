import apiClient from '../../../services/apiClient';

const marksheetsApi = {
  generateModularMarksheet: (data) => {
    return apiClient.post('/results/marksheets/generate-modular/', data, {
      responseType: 'blob'
    });
  },
  
  generateFormalMarksheet: (data) => {
    return apiClient.post('/results/marksheets/generate-formal/', data, {
      responseType: 'blob'
    });
  },
  
  generateWorkersPasMarksheet: (data) => {
    return apiClient.post('/results/marksheets/generate-workers-pas/', data, {
      responseType: 'blob'
    });
  },
};

export default marksheetsApi;
