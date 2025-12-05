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
  create: async (applicationData) => {
    try {
      const response = await apiClient.post('/applications/', applicationData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
  
  getAll: async () => {
    try {
      const response = await apiClient.get('/applications/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};

export default apiClient;
