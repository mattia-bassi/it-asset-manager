import { useState, useEffect } from 'react';
import api, { getApiError } from '../../api';
import Button from '../../components/Button';
import { auth } from '../../auth';

// Interfacce per UsersContent
interface User {
  id: number;
  username: string;
  role: 'admin' | 'operatore' | 'user';
  is_active: boolean;
  person_id: number | null;
  person_first_name: string | null;
  person_last_name: string | null;
  person_email: string | null;
  created_at: string;
}

export default function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [people, setPeople] = useState<any[]>([]);
  const [loadingPeople, setLoadingPeople] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    role: 'user' as 'admin' | 'operatore' | 'user',
    is_active: true,
    person_id: null as number | null
  });

  const [showLinkModal, setShowLinkModal] = useState(false);
  const [linkingUser, setLinkingUser] = useState<User | null>(null);
  const [linkPersonId, setLinkPersonId] = useState<number | null>(null);

  const currentUser = auth.getUser();

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    const fetchPeople = async () => {
      try {
        setLoadingPeople(true);
        const response = await api.get('/people');
        setPeople(response.data.items || []);
      } catch (error) {
        console.error('Errore caricamento persone:', error);
      } finally {
        setLoadingPeople(false);
      }
    };
    fetchPeople();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/users');
      setUsers(response.data.items || response.data);
    } catch (error) {
      console.error('Errore caricamento utenti:', error);
      alert('Errore nel caricamento degli utenti');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        password: '',
        role: user.role,
        is_active: user.is_active,
        person_id: user.person_id || null
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        password: '',
        role: 'user',
        is_active: true,
        person_id: null
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      role: 'user',
      is_active: true,
      person_id: null
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingUser) {
        const updateData: any = {
          username: formData.username,
          role: formData.role,
          is_active: formData.is_active
        };
        if (formData.password) {
          updateData.password = formData.password;
        }
        updateData.person_id = formData.person_id;
        
        await api.put(`/users/${editingUser.id}`, updateData);
        alert('✅ Utente aggiornato con successo!');
      } else {
        if (!formData.password) {
          alert('La password è obbligatoria per nuovi utenti');
          return;
        }
        await api.post('/users', formData);
        alert('✅ Utente creato con successo!');
      }
      
      handleCloseModal();
      fetchUsers();
    } catch (error: unknown) {
      console.error('Errore salvataggio utente:', error);
      alert(getApiError(error, 'Errore nel salvataggio dell\'utente'));
    }
  };

  const handleChangeRole = async (userId: number, newRole: string) => {
    if (!confirm(`Confermi di voler cambiare il ruolo di questo utente in "${newRole}"?`)) {
      return;
    }
    
    try {
      await api.patch(`/users/${userId}/role`, { role: newRole });
      alert('✅ Ruolo modificato con successo!');
      fetchUsers();
    } catch (error: unknown) {
      console.error('Errore cambio ruolo:', error);
      alert(getApiError(error, 'Errore nel cambio ruolo'));
    }
  };

  const handleToggleActive = async (user: User) => {
    const action = user.is_active ? 'disattivare' : 'attivare';
    if (!confirm(`Confermi di voler ${action} l'utente "${user.username}"?`)) {
      return;
    }
    
    try {
      await api.put(`/users/${user.id}`, {
        username: user.username,
        role: user.role,
        is_active: !user.is_active
      });
      alert(`✅ Utente ${user.is_active ? 'disattivato' : 'attivato'} con successo!`);
      fetchUsers();
    } catch (error: unknown) {
      console.error('Errore toggle attivo:', error);
      alert(getApiError(error, 'Errore nell\'operazione'));
    }
  };

  const handleOpenLinkModal = (user: User) => {
    setLinkingUser(user);
    setLinkPersonId(null);
    setShowLinkModal(true);
  };

  const handleLinkPerson = async () => {
    if (!linkingUser || !linkPersonId) return;

    try {
      await api.patch(`/users/${linkingUser.id}/link-person`, { person_id: linkPersonId });
      alert(`✅ Utente "${linkingUser.username}" collegato alla persona con successo!`);
      setShowLinkModal(false);
      setLinkingUser(null);
      setLinkPersonId(null);
      fetchUsers();
    } catch (error: unknown) {
      console.error('Errore collegamento persona:', error);
      alert(getApiError(error, 'Errore nel collegamento'));
    }
  };

  const handleHardDelete = async (user: User) => {
    if (user.id === currentUser?.id) {
      alert('Non puoi eliminare il tuo stesso account');
      return;
    }

    const confirmMsg = `⚠️ ATTENZIONE: Stai per eliminare PERMANENTEMENTE l'utente "${user.username}".\n\nQuesta azione è irreversibile.\n\nConfermi?`;
    if (!confirm(confirmMsg)) return;

    // Doppia conferma per sicurezza
    if (!confirm(`Sei davvero sicuro? L'utente "${user.username}" verrà rimosso dal database.`)) return;

    try {
      await api.delete(`/users/${user.id}/hard`);
      alert(`✅ Utente "${user.username}" eliminato permanentemente.`);
      fetchUsers();
    } catch (error: unknown) {
      console.error('Errore eliminazione utente:', error);
      alert(getApiError(error, 'Errore nell\'eliminazione'));
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'operatore': return 'bg-blue-100 text-blue-800';
      case 'user': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Caricamento...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-500">
          Gli account vengono creati automaticamente dalla pagina Persone.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Persona</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ruolo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Creato</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Azioni</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className={!user.is_active ? 'opacity-50' : ''}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{user.username}</div>
                  {user.id === currentUser?.id && (
                    <span className="text-xs text-gray-500">(Tu)</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {user.person_id ? (
                    <div>
                      <div className="text-sm text-gray-900">
                        {user.person_first_name} {user.person_last_name}
                      </div>
                      {user.person_email && (
                        <div className="text-xs text-gray-500">{user.person_email}</div>
                      )}
                    </div>
                  ) : (
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      ⚠️ Orfano
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <select
                    value={user.role}
                    onChange={(e) => handleChangeRole(user.id, e.target.value)}
                    disabled={user.id === currentUser?.id}
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(user.role)} ${
                      user.id === currentUser?.id ? 'cursor-not-allowed' : 'cursor-pointer'
                    }`}
                  >
                    <option value="admin">Admin</option>
                    <option value="operatore">Operatore</option>
                    <option value="user">User</option>
                  </select>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? '✓ Attivo' : '✗ Disattivato'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(user.created_at).toLocaleDateString('it-IT')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end gap-2">
                    {!user.person_id && (
                      <Button
                        variant="primary"
                        icon="🔗"
                        iconOnly
                        title="Collega a persona"
                        onClick={() => handleOpenLinkModal(user)}
                      />
                    )}
                    <Button
                      variant="secondary"
                      icon="✏️"
                      iconOnly
                      title="Modifica utente"
                      onClick={() => handleOpenModal(user)}
                    />
                    {user.id !== currentUser?.id && (
                      <Button
                        variant={user.is_active ? "destructive" : "primary"}
                        icon={user.is_active ? "🚫" : "✓"}
                        iconOnly
                        title={user.is_active ? "Disattiva utente" : "Attiva utente"}
                        onClick={() => handleToggleActive(user)}
                      />
                    )}
                    {user.id !== currentUser?.id && user.id !== 1 && (
                      <Button
                        variant="destructive"
                        icon="🗑️"
                        iconOnly
                        title="Elimina permanentemente"
                        onClick={() => handleHardDelete(user)}
                      />
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingUser ? '✏️ Modifica Utente' : '➕ Nuovo Utente'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                  minLength={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password {editingUser && '(lascia vuoto per non modificare)'}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required={!editingUser}
                  minLength={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Minimo 8 caratteri</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ruolo</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value as any})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="user">User (solo visualizzazione propria)</option>
                  <option value="operatore">Operatore (gestione completa)</option>
                  <option value="admin">Admin (completo + utenti)</option>
                </select>
              </div>
              
              {/* Campo Persona - visibile per tutti i ruoli */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Persona Collegata
                </label>
                <select
                  value={formData.person_id || ''}
                  onChange={(e) => setFormData({...formData, person_id: e.target.value ? parseInt(e.target.value) : null})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  required={false}
                >
                  <option value="">Seleziona persona...</option>
                  {people.map(person => (
                    <option key={person.id} value={person.id}>
                      {person.first_name} {person.last_name} {person.email ? `(${person.email})` : ''}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Collegare una persona per associare l'utente ai relativi dati
                </p>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active_user"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="is_active_user" className="text-sm text-gray-700">Utente attivo</label>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={handleCloseModal} className="flex-1">
                  Annulla
                </Button>
                <Button type="submit" variant="primary" className="flex-1">
                  {editingUser ? 'Aggiorna' : 'Crea'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showLinkModal && linkingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">🔗 Collega Persona</h2>
            <p className="text-sm text-gray-600 mb-4">
              Collega l'utente <strong>{linkingUser.username}</strong> a una persona esistente.
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Persona</label>
              <select
                value={linkPersonId || ''}
                onChange={(e) => setLinkPersonId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
              >
                <option value="">Seleziona persona...</option>
                {people.map((person: any) => (
                  <option key={person.id} value={person.id}>
                    {person.first_name} {person.last_name} {person.email ? `(${person.email})` : ''}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => { setShowLinkModal(false); setLinkingUser(null); }}
                className="flex-1"
              >
                Annulla
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={handleLinkPerson}
                disabled={!linkPersonId}
                className="flex-1"
              >
                Collega
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
