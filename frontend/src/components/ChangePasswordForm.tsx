import { useState } from 'react';
import api, { getApiError } from '../api';
import Button from './Button';

export default function ChangePasswordForm() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      alert('Le nuove password non coincidono');
      return;
    }
    
    if (newPassword.length < 8) {
      alert('La nuova password deve essere di almeno 8 caratteri');
      return;
    }
    
    try {
      setLoading(true);
      await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      });
      
      alert('✅ Password cambiata con successo!');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: unknown) {
      console.error('Errore cambio password:', error);
      alert(getApiError(error, 'Errore nel cambio password'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Password Corrente
        </label>
        <input
          type="password"
          value={oldPassword}
          onChange={(e) => setOldPassword(e.target.value)}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Nuova Password
        </label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          minLength={8}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">Minimo 8 caratteri</p>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Conferma Nuova Password
        </label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          minLength={8}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      
      <Button
        type="submit"
        variant="primary"
        disabled={loading}
      >
        {loading ? 'Aggiornamento...' : 'Cambia Password'}
      </Button>
    </form>
  );
}
