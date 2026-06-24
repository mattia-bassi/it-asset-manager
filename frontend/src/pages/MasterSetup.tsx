import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { getApiError } from '../api';
import type { Site } from '../types';

export default function MasterSetup() {
  const navigate = useNavigate();
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    site_id: '' as string | number,
    username: '',
    password: '',
    confirm_password: '',
  });

  useEffect(() => {
    const fetchSites = async () => {
      try {
        const response = await api.get('/sites', {
          params: { limit: 100, is_active: true },
        });
        setSites(response.data?.items || []);
      } catch {
        setSites([]);
      }
    };
    fetchSites();
  }, []);

  useEffect(() => {
    if (formData.first_name && formData.last_name) {
      const suggested = `${formData.first_name}.${formData.last_name}`
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/\s+/g, '.');
      setFormData((prev) => {
        if (prev.username === '') return { ...prev, username: suggested };
        return prev;
      });
    }
  }, [formData.first_name, formData.last_name]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password.length < 12) {
      setError('La password deve essere di almeno 12 caratteri');
      return;
    }
    if (formData.password !== formData.confirm_password) {
      setError('Le password non coincidono');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/master-setup', {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email.trim() || undefined,
        site_id: formData.site_id ? Number(formData.site_id) : undefined,
        username: formData.username.trim(),
        password: formData.password,
      });
      navigate('/login', {
        replace: true,
        state: {
          message: 'Account amministratore creato. Accedi con le credenziali impostate.',
        },
      });
    } catch (err: unknown) {
      setError(getApiError(err, 'Errore durante il salvataggio'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-800 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-8">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-2">
          🔧 Configurazione Iniziale Sistema
        </h1>
        <p className="text-center text-gray-600 text-sm mb-4">
          Crea il primo account amministratore per iniziare a usare il sistema.
        </p>
        <div className="p-3 mb-6 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
          Dopo il salvataggio, l&apos;account di configurazione verrà disattivato permanentemente.
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cognome *</label>
            <input
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sede</label>
            <select
              name="site_id"
              value={formData.site_id}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            >
              <option value="">— Nessuna —</option>
              {sites.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username Admin *</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password Admin * (min. 12 caratteri)</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={12}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Conferma Password *</label>
            <input
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow outline-none"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors"
          >
            💾 Salva ed Esci
          </button>
        </form>
      </div>
    </div>
  );
}
