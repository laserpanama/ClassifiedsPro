import axios from 'axios';
import api, { setToken, clearToken, getToken } from './api';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';

const login = async (username, password) => {
  const response = await axios.post(`${API_URL}/auth/login`, { username, password });
  setToken(response.data.token);
  return response.data;
};

const logout = () => clearToken();

const isAuthenticated = () => Boolean(getToken());

const authService = {
  login,
  logout,
  isAuthenticated,
  // re-export for convenience
  api,
};

export default authService;
