import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import { auth } from '../auth';
import StatsCard from '../components/common/StatsCard';
import { UserGroupIcon } from '@heroicons/react/24/outline';
import type { Person, Site } from '../types';

interface PersonForm {
  first_name: string;
  last_name: string;
  site_id: number | null;
  email: string;
  extension: string;
  mobile_phone: string;
  notes: string;
  is_active: boolean;
}

// Genera colore avatar basato su indice
function getAvatarColor(index: number): string {
  const colors = [
    'bg-gradient-to-br from-yellow-400 to-orange-500',
    'bg-gradient-to-br from-green-400 to-emerald-600',
    'bg-gradient-to-br from-blue-400 to-indigo-600',
    'bg-gradient-to-br from-purple-400 to-pink-500',
    'bg-gradient-to-br from-orange-400 to-red-500',
    'bg-gradient-to-br from-teal-400 to-cyan-600',
  ];
  return colors[index % colors.length];
}

// Estrae iniziali da nome e cognome
function getInitials(firstName: string, lastName: string): string {
  return (firstName.charAt(0) + lastName.charAt(0)).toUpperCase();
}

export default function People() {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';
  
  const [people, setPeople] = useState<Person[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showMergeModal, setShowMergeModal] = useState(false);
  const [editingPerson, setEditingPerson] = useState<Person | null>(null);
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [selectedSiteFilter, setSelectedSiteFilter] = useState<number | null>(null);
  
  // Merge
  const [mergeSourceId, setMergeSourceId] = useState<number | null>(null);
  const [mergeTargetId, setMergeTargetId] = useState<number | null>(null);
  const [mergeNotes, setMergeNotes] = useState(true);

  const [formData, setFormData] = useState<PersonForm>({
    first_name: '',
    last_name: '',
    site_id: null,
    email: '',
    extension: '',
    mobile_phone: '',
    notes: '',
    is_active: true
  });

  useEffect(() => {
    fetchSites();
  }, []);

  useEffect(() => {
    fetchPeople();
  }, [search, showInactive, selectedSiteFilter]);

  const fetchSites = async () => {
    try {
      const response = await api.get('/sites', { params: { is_active: true, limit: 1000 } });
      setSites(response.data.items);
    } catch (error) {
      console.error('Errore caricamento sedi:', error);
    }
  };

  const fetchPeople = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (search) params.search = search;
      if (!showInactive) params.is_active = true;
      if (selectedSiteFilter) params.site_id = selectedSiteFilter;
      
      const response = await api.get('/people', { params });
      setPeople(response.data.items);
    } catch (error) {
      console.error('Errore caricamento persone:', error);
      alert('Errore nel caricamento delle persone');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Convert empty strings to null for optional fields (backend Pydantic expects null, not "")
      const cleanedData = {
        ...formData,
        email: formData.email?.trim() || null,
        extension: formData.extension?.trim() || null,
        mobile_phone: formData.mobile_phone?.trim() || null,
        notes: formData.notes?.trim() || null,
      };

      if (editingPerson) {
        await api.put(`/people/${editingPerson.id}`, cleanedData);
      } else {
        await api.post('/people', cleanedData);
      }
      setShowModal(false);
      resetForm();
      fetchPeople();
    } catch (error: unknown) {
      console.error('Errore salvataggio persona:', error);
      alert(getApiError(error, 'Errore nel salvataggio della persona'));
    }
  };

  const handleEdit = (person: Person) => {
    setEditingPerson(person);
    setFormData({
      first_name: person.first_name,
      last_name: person.last_name,
      site_id: person.site_id,
      email: person.email || '',
      extension: person.extension || '',
      mobile_phone: person.mobile_phone || '',
      notes: person.notes || '',
      is_active: person.is_active
    });
    setShowModal(true);
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Disattivare questa persona?')) return;
    try {
      await api.delete(`/people/${id}`);
      fetchPeople();
    } catch (error) {
      console.error('Errore disattivazione persona:', error);
      alert('Errore nella disattivazione della persona');
    }
  };

  const handleReactivate = async (id: number) => {
    try {
      await api.put(`/people/${id}`, { is_active: true });
      fetchPeople();
    } catch (error) {
      console.error('Errore riattivazione persona:', error);
      alert('Errore nella riattivazione della persona');
    }
  };

  const handleHardDelete = async (id: number) => {
    if (!confirm('⚠️ ATTENZIONE: Questa operazione è IRREVERSIBILE.\n\nEliminare definitivamente questa persona dal database?')) return;
    try {
      await api.delete(`/people/${id}/hard`);
      fetchPeople();
    } catch (error) {
      console.error('Errore eliminazione persona:', error);
      alert('Errore nell\'eliminazione definitiva della persona');
    }
  };

  const handleMerge = async () => {
    if (!mergeSourceId || !mergeTargetId) {
      alert('Seleziona entrambe le persone da unire');
      return;
    }
    if (mergeSourceId === mergeTargetId) {
      alert('Non puoi unire una persona con se stessa');
      return;
    }
    try {
      await api.post('/people/merge', {
        source_id: mergeSourceId,
        target_id: mergeTargetId,
        merge_notes: mergeNotes
      });
      setShowMergeModal(false);
      setMergeSourceId(null);
      setMergeTargetId(null);
      fetchPeople();
      alert('Persone unite con successo');
    } catch (error: unknown) {
      console.error('Errore merge persone:', error);
      alert(getApiError(error, 'Errore nell\'unione delle persone'));
    }
  };

  const resetForm = () => {
    setFormData({
      first_name: '',
      last_name: '',
      site_id: null,
      email: '',
      extension: '',
      mobile_phone: '',
      notes: '',
      is_active: true
    });
    setEditingPerson(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  const totalPeople = people.length;
  const activePeople = people.filter((p) => p.is_active).length;
  const inactivePeople = totalPeople - activePeople;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        {/* HEADER MODERNO */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
              <UserGroupIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Gestione Persone</h1>
              <p className="text-sm text-gray-600 mt-1">Gestisci i dipendenti e le loro informazioni</p>
            </div>
          </div>
          <div className="flex justify-end gap-3">
            {!isUser && (
              <>
                <Button
                  variant="secondary"
                  icon="🔗"
                  onClick={() => setShowMergeModal(true)}
                >
                  Unisci Persone
                </Button>
                <Button
                  variant="primary"
                  icon="➕"
                  onClick={() => setShowModal(true)}
                >
                  Nuova Persona
                </Button>
              </>
            )}
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatsCard
            title="Totale Persone"
            value={totalPeople}
            subtitle="Dipendenti registrati"
            icon={UserGroupIcon}
            gradient="blue"
          />

          <StatsCard
            title="Persone Attive"
            value={activePeople}
            subtitle={`${totalPeople > 0 ? Math.round((activePeople / totalPeople) * 100) : 0}% del totale`}
            icon={UserGroupIcon}
            gradient="green"
          />

          <StatsCard
            title="Persone Inattive"
            value={inactivePeople}
            icon={UserGroupIcon}
            gradient="red"
            badge={
              inactivePeople > 0
                ? {
                    text: 'Attenzione',
                    variant: 'warning',
                  }
                : undefined
            }
          />
        </div>

        {/* Filtri */}
        <div className="mb-4 flex gap-4 items-center">
          <input
            type="text"
            placeholder="Cerca per nome, cognome o email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          />
          <select
            value={selectedSiteFilter || ''}
            onChange={(e) => setSelectedSiteFilter(e.target.value ? Number(e.target.value) : null)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          >
            <option value="">Tutte le sedi</option>
            {sites.map(site => (
              <option key={site.id} value={site.id}>{site.name}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="w-4 h-4 text-asset-manager-gray rounded focus:ring-2 focus:ring-asset-manager-yellow"
            />
            Mostra inattive
          </label>
        </div>

        {/* Tabella */}
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
          </div>
        ) : (
          <div className="bg-white shadow-lg rounded-lg overflow-hidden">
            <div className="overflow-hidden">
              <table className="w-full table-fixed divide-y divide-gray-200">
              <thead className="bg-asset-manager-gray text-white">
                <tr>
                  <th className="px-6 py-3 text-left">Persona</th>
                  <th className="px-6 py-3 text-left">Account</th>
                  <th className="px-6 py-3 text-left">Sede</th>
                  <th className="px-6 py-3 text-left">Email</th>
                  <th className="px-6 py-3 text-left">Interno</th>
                  <th className="px-6 py-3 text-left">Cellulare</th>
                  <th className="px-6 py-3 text-left">Stato</th>
                  <th className="px-6 py-3 text-right">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {people.map((person) => (
                  <tr key={person.id} className="border-t hover:bg-yellow-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full ${getAvatarColor(people.indexOf(person))} flex items-center justify-center text-white font-bold text-sm shadow-md`}>
                          {getInitials(person.first_name, person.last_name)}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">
                            {person.first_name} {person.last_name}
                          </div>
                          {person.email && (
                            <div className="text-sm text-gray-500">{person.email}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {person.linked_username ? (
                        <span className="text-sm text-gray-700 font-mono">{person.linked_username}</span>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">{person.site_name || '-'}</td>
                    <td className="px-6 py-4">{person.email || '-'}</td>
                    <td className="px-6 py-4">{person.extension || '-'}</td>
                    <td className="px-6 py-4">{person.mobile_phone || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                        person.is_active 
                          ? 'bg-green-50 text-green-700 border-green-200' 
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}>
                        {person.is_active ? '✓ Attiva' : '✗ Inattiva'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {!isUser && (
                        <div className="flex justify-end gap-2">
                          {/* 1. Modifica - PRIMARY */}
                          <Button
                            variant="primary"
                            icon="✏️"
                            iconOnly
                            title="Modifica persona"
                            onClick={() => handleEdit(person)}
                          />
                          
                          {person.is_active ? (
                            <>
                              {/* 2. Disattiva - SECONDARY */}
                              <Button
                                variant="secondary"
                                icon="⏸️"
                                iconOnly
                                title="Disattiva persona"
                                onClick={() => handleDeactivate(person.id)}
                              />
                            </>
                          ) : (
                            <>
                              {/* 2. Riattiva - SECONDARY */}
                              <Button
                                variant="secondary"
                                icon="▶️"
                                iconOnly
                                title="Riattiva persona"
                                onClick={() => handleReactivate(person.id)}
                              />
                              {/* 3. Elimina - DESTRUCTIVE (sempre rosso) */}
                              <Button
                                variant="destructive"
                                icon="🗑️"
                                iconOnly
                                title="Elimina definitivamente"
                                onClick={() => handleHardDelete(person.id)}
                              />
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {people.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                      Nessuna persona trovata
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>
          </div>
        )}

        {/* Modal Form Persona */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">
                {editingPerson ? 'Modifica Persona' : 'Nuova Persona'}
              </h2>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Nome *</label>
                      <input
                        type="text"
                        required
                        value={formData.first_name}
                        onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Cognome *</label>
                      <input
                        type="text"
                        required
                        value={formData.last_name}
                        onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Sede</label>
                    <select
                      value={formData.site_id || ''}
                      onChange={(e) => setFormData({...formData, site_id: e.target.value ? Number(e.target.value) : null})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    >
                      <option value="">Nessuna sede</option>
                      {sites.map(site => (
                        <option key={site.id} value={site.id}>{site.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Email</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Interno</label>
                      <input
                        type="text"
                        value={formData.extension}
                        onChange={(e) => setFormData({...formData, extension: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Numero Cellulare</label>
                      <input
                        type="text"
                        value={formData.mobile_phone}
                        onChange={(e) => setFormData({...formData, mobile_phone: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Note</label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({...formData, notes: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      rows={3}
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                      className="mr-2 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-asset-manager-yellow"
                    />
                    <label className="text-sm font-medium text-gray-700">Persona attiva</label>
                  </div>
                </div>
                <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                  <Button
                    variant="secondary"
                    type="button"
                    onClick={handleCloseModal}
                  >
                    Annulla
                  </Button>
                  <Button
                    variant="primary"
                    type="submit"
                  >
                    {editingPerson ? 'Salva Modifiche' : 'Crea Persona'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal Merge */}
        {showMergeModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">🔗 Unisci Persone</h2>
              <p className="text-sm text-gray-600 mb-4">
                Seleziona la persona da unire (verrà disattivata) e la persona destinazione.
              </p>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700">Persona da unire (source)</label>
                  <select
                    value={mergeSourceId || ''}
                    onChange={(e) => setMergeSourceId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Seleziona...</option>
                    {people.filter(p => p.is_active).map(person => (
                      <option key={person.id} value={person.id}>
                        {person.first_name} {person.last_name} {person.email ? `(${person.email})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-700">Persona destinazione (target)</label>
                  <select
                    value={mergeTargetId || ''}
                    onChange={(e) => setMergeTargetId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Seleziona...</option>
                    {people.filter(p => p.is_active).map(person => (
                      <option key={person.id} value={person.id}>
                        {person.first_name} {person.last_name} {person.email ? `(${person.email})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={mergeNotes}
                    onChange={(e) => setMergeNotes(e.target.checked)}
                    className="mr-2 w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                  />
                  <label className="text-sm font-medium text-gray-700">Unisci anche le note</label>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowMergeModal(false);
                    setMergeSourceId(null);
                    setMergeTargetId(null);
                  }}
                >
                  Annulla
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleMerge}
                >
                  Unisci
                </Button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
