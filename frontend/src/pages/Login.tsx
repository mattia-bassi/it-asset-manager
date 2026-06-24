import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api, { getApiError } from '../api';
import { auth } from '../auth';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const successMessage = (location.state as { message?: string })?.message;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      if (response.data.require_master_setup) {
        navigate('/master-setup');
        return;
      }
      auth.setToken(response.data.access_token);
      auth.setUser(response.data.user);
      navigate('/');
    } catch (err: unknown) {
      setError(getApiError(err, 'Login failed'));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-6">IT Asset Manager</h1>
        {successMessage && (
          <div className="p-3 mb-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {successMessage}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none transition-colors"
            />
          </div>
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          <button
            type="submit"
            className="w-full py-2 px-4 bg-asset-manager-yellow text-asset-manager-gray font-semibold rounded-lg hover:bg-asset-manager-yellow-hover transition-colors"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
