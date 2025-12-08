// In frontend/app/services/api.js

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authAPI = {
  // ... (keep existing register and login) ...
  register: async (userData) => {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
  
  login: async (username, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password');
      
      const response = await axios.post(
        `${API_BASE_URL}/auth/token`,
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      
      if (response.data.access_token) {
        await AsyncStorage.setItem('access_token', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};

export const applicationAPI = {
  // 1. NEW: Initial Application (sends JSON to /apply)
  apply: async (applicationData) => {
    try {
      const response = await apiClient.post('/applications/apply', applicationData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
  
  // 2. MODIFIED: Verification Submission (sends multipart/form-data to /submit)
  submitVerification: async (formDataWithFiles) => { 
    try {
      const response = await apiClient.post('/applications/submit', formDataWithFiles, {
        headers: {
          'Content-Type': 'multipart/form-data', // IMPORTANT for file uploads
        },
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
  
  // 3. Keep existing getAll method (assumes backend's /applications/ endpoint works)
  getAll: async () => {
    try {
      // NOTE: Update the backend's GET /applications/ endpoint logic to handle filtering by user ID if necessary.
      const response = await apiClient.get('/applications/'); 
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};

export default apiClient;