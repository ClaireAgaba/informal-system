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

  printModularMarksheet: (data) => {
    return apiClient.post('/results/marksheets/print-modular/', data, {
      responseType: 'blob'
    });
  },

  printFormalMarksheet: (data) => {
    return apiClient.post('/results/marksheets/print-formal/', data, {
      responseType: 'blob'
    });
  },

  printWorkersPasMarksheet: (data) => {
    return apiClient.post('/results/marksheets/print-workers-pas/', data, {
      responseType: 'blob'
    });
  },

  exportModularResults: (data) => {
    return apiClient.post('/results/marksheets/export-modular/', data, {
      responseType: 'blob'
    });
  },

  exportFormalResults: (data) => {
    return apiClient.post('/results/marksheets/export-formal/', data, {
      responseType: 'blob'
    });
  },

  exportWorkersPasResults: (data) => {
    return apiClient.post('/results/marksheets/export-workers-pas/', data, {
      responseType: 'blob'
    });
  },
};

export default marksheetsApi;
