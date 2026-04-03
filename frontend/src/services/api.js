import axios from 'axios';

const API_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000,
});

export const scannerAPI = {
  // Get scan results for specific scanner
  getScanResults: async (scanner) => {
    try {
      const response = await api.get(`/api/scan/${scanner}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${scanner} results:`, error);
      throw error;
    }
  },

  // Get all scanner results
  getAllResults: async () => {
    try {
      const response = await api.get('/api/scan/all');
      return response.data;
    } catch (error) {
      console.error('Error fetching all results:', error);
      throw error;
    }
  },

  // Get scanner status
  getStatus: async () => {
    try {
      const response = await api.get('/api/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching status:', error);
      throw error;
    }
  },

  // Trigger manual scan for specific scanner
  triggerManualScan: async (scanner) => {
    try {
      const response = await api.post(`/api/scan/${scanner}/manual`);
      return response.data;
    } catch (error) {
      console.error(`Error triggering ${scanner} scan:`, error);
      throw error;
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/api/health');
      return response.data;
    } catch (error) {
      console.error('API health check failed:', error);
      throw error;
    }
  }
};