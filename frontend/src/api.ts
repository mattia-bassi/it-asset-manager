import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

/**
 * Extracts a human-readable error message from an unknown catch value.
 * Handles Axios errors (FastAPI detail field) and generic Error objects.
 *
 * Usage:
 *   catch (error: unknown) {
 *     alert(getApiError(error, 'Operazione fallita'));
 *   }
 */
export function getApiError(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || fallback;
  }
  if (error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}

