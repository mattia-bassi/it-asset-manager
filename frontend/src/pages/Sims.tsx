import React, { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import StatsCard from '../components/common/StatsCard';
import { DevicePhoneMobileIcon, CheckCircleIcon, UserGroupIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { auth } from '../auth';
import type { Sim, Person, Site } from '../types';

interface SimWithCredentials extends Sim {
  pin: string;
  puk: string;
}

const Sims: React.FC = () => {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';

  // State
  const [sites, setSites] = useState<Site[]>([]);
  const [sims, setSims] = useState<Sim[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [editingSim, setEditingSim] = useState<Sim | null>(null);
  const [selectedSim, setSelectedSim] = useState<Sim | null>(null);
  const [credentials, setCredentials] = useState<{ pin: string; puk: string } | null>(null);
  
  // Filtri
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [operatoreFilter, setOperatoreFilter] = useState('');
  
  // Form
  const [formData, setFormData] = useState({
    seriale: '',
    operatore: '',
    site_id: null as number | null,
    numero_telefono: '',
    pin: '',
    puk: '',
    status: 'disponibile' as 'disponibile' | 'assegnata' | 'disattivata'
  });
  
  // Assegnazione
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null);
  
  // PIN/PUK visibility
  const [showPin, setShowPin] = useState(false);
  const [showPuk, setShowPuk] = useState(false);

  // Fetch SIM
  const fetchSims = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);
      if (operatoreFilter) params.append('operatore', operatoreFilter);
      
      const response = await api.get(`/sims?${params.toString()}`);
      setSims(response.data.items);
    } catch (error) {
      console.error('Errore caricamento SIM:', error);
      alert('Errore nel caricamento delle SIM');
    } finally {
      setLoading(false);
    }
  };

  // Fetch People (per assegnazioni)
  const fetchPeople = async () => {
    try {
      const response = await api.get('/people?limit=1000');
      setPeople(response.data.items);
    } catch (error) {
      console.error('Errore caricamento persone:', error);
    }
  };

  const fetchSites = async () => {
    try {
      const response = await api.get('/sites', {
        params: { limit: 500, is_active: true }
      });
      setSites(response.data.items || []);
    } catch (error) {
      console.error('Errore caricamento sedi:', error);
    }
  };

  useEffect(() => {
    fetchSims();
    fetchPeople();
    fetchSites();
  }, [search, statusFilter, operatoreFilter]);

  // Reset form
  const resetForm = () => {
    setFormData({
      seriale: '',
      operatore: '',
      site_id: null,
      numero_telefono: '',
      pin: '',
      puk: '',
      status: 'disponibile'
    });
    setEditingSim(null);
    setShowPin(false);
    setShowPuk(false);
  };

  // Apri modal creazione
  const handleCreate = () => {
    resetForm();
    setShowModal(true);
  };

  // Apri modal modifica
  const handleEdit = (sim: Sim) => {
    setEditingSim(sim);
    setFormData({
      seriale: sim.seriale,
      operatore: sim.operatore,
      site_id: sim.site_id,
      numero_telefono: sim.numero_telefono,
      pin: '',
      puk: '',
      status: sim.status
    });
    setShowModal(true);
  };

  // Submit form (crea/modifica)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingSim) {
        // Modifica
        const updateData: any = {
          seriale: formData.seriale,
          operatore: formData.operatore,
          site_id: formData.site_id,
          numero_telefono: formData.numero_telefono,
          status: formData.status
        };
        
        // Includi PIN/PUK solo se forniti
        if (formData.pin) updateData.pin = formData.pin;
        if (formData.puk) updateData.puk = formData.puk;
        
        await api.put(`/sims/${editingSim.id}`, updateData);
        alert('SIM aggiornata con successo!');
      } else {
        // Creazione
        if (!formData.pin || !formData.puk) {
          alert('PIN e PUK sono obbligatori per la creazione');
          return;
        }
        
        await api.post('/sims', formData);
        alert('SIM creata con successo!');
      }
      
      setShowModal(false);
      resetForm();
      fetchSims();
    } catch (error: unknown) {
      console.error('Errore salvataggio SIM:', error);
      alert(getApiError(error, 'Errore nel salvataggio della SIM'));
    }
  };

  // Elimina SIM
  const handleDelete = async (id: number) => {
    if (!confirm('Sei sicuro di voler eliminare questa SIM?')) return;
    
    try {
      await api.delete(`/sims/${id}`);
      alert('SIM eliminata con successo!');
      fetchSims();
    } catch (error: unknown) {
      console.error('Errore eliminazione SIM:', error);
      alert(getApiError(error, 'Errore nell\'eliminazione della SIM'));
    }
  };

  // Visualizza credenziali
  const handleShowCredentials = async (sim: Sim) => {
    try {
      const response = await api.get<SimWithCredentials>(`/sims/${sim.id}/credentials`);
      setCredentials({ pin: response.data.pin, puk: response.data.puk });
      setSelectedSim(sim);
      setShowCredentialsModal(true);
    } catch (error) {
      console.error('Errore caricamento credenziali:', error);
      alert('Errore nel caricamento delle credenziali');
    }
  };

  // Apri modal assegnazione
  const handleOpenAssignModal = (sim: Sim) => {
    setSelectedSim(sim);
    setSelectedPersonId(null);
    setShowAssignModal(true);
  };

  // Assegna SIM
  const handleAssignSim = async () => {
    if (!selectedSim || !selectedPersonId) {
      alert('Seleziona una persona');
      return;
    }
    
    try {
      await api.post(`/sims/${selectedSim.id}/assign/${selectedPersonId}`);
      alert('SIM assegnata con successo!');
      setShowAssignModal(false);
      fetchSims();
    } catch (error: unknown) {
      console.error('Errore assegnazione SIM:', error);
      alert(getApiError(error, 'Errore nell\'assegnazione della SIM'));
    }
  };

  // Rimuovi assegnazione
  const handleUnassignSim = async (sim: Sim) => {
    // Trova persona con questo numero
    const person = people.find(p => p.mobile_phone === sim.numero_telefono);
    if (!person) {
      alert('Persona con questa SIM non trovata');
      return;
    }
    
    if (!confirm(`Rimuovere SIM da ${person.first_name} ${person.last_name}?`)) return;
    
    try {
      await api.post(`/sims/${sim.id}/unassign/${person.id}`);
      alert('Assegnazione SIM rimossa con successo!');
      fetchSims();
    } catch (error: unknown) {
      console.error('Errore rimozione assegnazione:', error);
      alert(getApiError(error, 'Errore nella rimozione dell\'assegnazione'));
    }
  };

  // Badge status con colori
  const getStatusBadge = (status: string) => {
    const styles = {
      disponibile: 'bg-green-100 text-green-800',
      assegnata: 'bg-blue-100 text-blue-800',
      disattivata: 'bg-gray-100 text-gray-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[status as keyof typeof styles]}`}>
        {status}
      </span>
    );
  };

  // Calcolo statistiche SIM (dopo state, prima del return)
  const totalSims = sims.length;
  const available = sims.filter(s => s.status === 'disponibile').length;
  const assigned = sims.filter(s => s.status === 'assegnata').length;
  const deactivated = sims.filter(s => s.status === 'disattivata').length;
  const availablePercent = totalSims > 0 ? Math.round((available/totalSims)*100) : 0;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
      {/* HEADER MODERNO */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
            <DevicePhoneMobileIcon className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Gestione SIM</h1>
            <p className="text-sm text-gray-600 mt-1">Gestisci le SIM aziendali con PIN/PUK criptati</p>
          </div>
        </div>
        <div className="flex justify-end">
          {!isUser && (
            <Button
              variant="primary"
              icon="➕"
              onClick={handleCreate}
            >
              Nuova SIM
            </Button>
          )}
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Totale SIM"
          value={totalSims}
          icon={DevicePhoneMobileIcon}
          gradient="blue"
        />
        <StatsCard
          title="Disponibili"
          value={available}
          icon={CheckCircleIcon}
          gradient="green"
          subtitle={`${availablePercent}% del totale`}
        />
        <StatsCard
          title="Assegnate"
          value={assigned}
          icon={UserGroupIcon}
          gradient="purple"
        />
        <StatsCard
          title="Disattivate"
          value={deactivated}
          icon={XCircleIcon}
          gradient="red"
        />
      </div>

      {/* Filtri e Azioni */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Ricerca */}
          <div>
            <input
              type="text"
              placeholder="🔍 Cerca seriale, numero..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
            />
          </div>

          {/* Filtro Status */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
            >
              <option value="">Tutti gli status</option>
              <option value="disponibile">Disponibile</option>
              <option value="assegnata">Assegnata</option>
              <option value="disattivata">Disattivata</option>
            </select>
          </div>

          {/* Filtro Operatore */}
          <div>
            <input
              type="text"
              placeholder="Filtra per operatore..."
              value={operatoreFilter}
              onChange={(e) => setOperatoreFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
            />
          </div>
        </div>
      </div>

      {/* Tabella SIM */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-600">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
            <p className="mt-4">Caricamento...</p>
          </div>
        ) : sims.length === 0 ? (
          <div className="p-8 text-center text-gray-600">Nessuna SIM trovata</div>
        ) : (
          <div className="overflow-hidden">
            <table className="w-full table-fixed divide-y divide-gray-200">
              <thead className="bg-asset-manager-gray text-white">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Seriale</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Operatore</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Sede</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Numero Telefono</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Assegnata a</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Data Creazione</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {sims.map((sim) => (
                  <tr
                    key={sim.id}
                    className="border-t hover:bg-yellow-50 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-sm">{sim.seriale}</td>
                    <td className="px-4 py-3">{sim.operatore}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {sim.site_id ? (
                        sites.find(s => s.id === sim.site_id)?.name || '-'
                      ) : (
                        <span className="text-gray-400">Non assegnata</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">{sim.numero_telefono}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-700">
                      {sim.person_first_name && sim.person_last_name ? (
                        <span className="text-blue-600">
                          {sim.person_first_name} {sim.person_last_name}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(sim.status)}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(sim.created_at).toLocaleDateString('it-IT')}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        {/* 1. Credenziali - PRIMARY (visibile per tutti) */}
                        <Button
                          variant="primary"
                          icon="🔐"
                          iconOnly
                          title="Visualizza PIN/PUK"
                          onClick={() => handleShowCredentials(sim)}
                        />

                        {/* Bottoni azioni - Nascosti per user */}
                        {!isUser && (
                          <>
                            {/* 2. Assegna/Rimuovi - SECONDARY (o destructive per Rimuovi) */}
                            {sim.status === 'disponibile' ? (
                              <Button
                                variant="secondary"
                                icon="👤"
                                iconOnly
                                title="Assegna a persona"
                                onClick={() => handleOpenAssignModal(sim)}
                              />
                            ) : sim.status === 'assegnata' ? (
                              <Button
                                variant="destructive"
                                icon="❌"
                                iconOnly
                                title="Rimuovi assegnazione"
                                onClick={() => handleUnassignSim(sim)}
                              />
                            ) : null}

                            {/* 3. Modifica - PRIMARY */}
                            <Button
                              variant="primary"
                              icon="✏️"
                              iconOnly
                              title="Modifica SIM"
                              onClick={() => handleEdit(sim)}
                            />

                            {/* 4. Elimina - DESTRUCTIVE (sempre rosso) */}
                            {sim.status !== 'assegnata' && (
                              <Button
                                variant="destructive"
                                icon="🗑️"
                                iconOnly
                                title="Elimina SIM"
                                onClick={() => handleDelete(sim.id)}
                              />
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Crea/Modifica SIM */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-2xl font-bold mb-4 text-asset-manager-gray">
              {editingSim ? 'Modifica SIM' : 'Nuova SIM'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Seriale */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Seriale *
                </label>
                <input
                  type="text"
                  value={formData.seriale}
                  onChange={(e) => setFormData({ ...formData, seriale: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                  placeholder="es: SIM-001-2026"
                  required
                />
              </div>

              {/* Operatore */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Operatore *
                </label>
                <select
                  value={formData.operatore}
                  onChange={(e) => setFormData({ ...formData, operatore: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                  required
                >
                  <option value="">Seleziona operatore</option>
                  <option value="TIM">TIM</option>
                  <option value="Vodafone">Vodafone</option>
                  <option value="Wind">Wind</option>
                  <option value="Tre">Tre</option>
                  <option value="Iliad">Iliad</option>
                  <option value="Fastweb">Fastweb</option>
                  <option value="Altro">Altro</option>
                </select>
              </div>

              {/* Campo Sede */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sede
                </label>
                <select
                  value={formData.site_id ?? ''}
                  onChange={(e) => setFormData({ ...formData, site_id: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                >
                  <option value="">Nessuna sede</option>
                  {sites.map(site => (
                    <option key={site.id} value={site.id}>
                      {site.name} {site.city ? `(${site.city})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Numero Telefono */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Numero Telefono *
                </label>
                <input
                  type="tel"
                  value={formData.numero_telefono}
                  onChange={(e) => setFormData({ ...formData, numero_telefono: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                  placeholder="es: +39 333 1234567"
                  required
                />
              </div>

              {/* PIN */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PIN {!editingSim && '*'}
                  {editingSim && <span className="text-xs text-gray-500"> (lascia vuoto per non modificare)</span>}
                </label>
                <div className="relative">
                  <input
                    type={showPin ? 'text' : 'password'}
                    value={formData.pin}
                    onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                    placeholder="4-8 cifre"
                    pattern="[0-9]{4,8}"
                    required={!editingSim}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPin(!showPin)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPin ? '👁️' : '🙈'}
                  </button>
                </div>
              </div>

              {/* PUK */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PUK {!editingSim && '*'}
                  {editingSim && <span className="text-xs text-gray-500"> (lascia vuoto per non modificare)</span>}
                </label>
                <div className="relative">
                  <input
                    type={showPuk ? 'text' : 'password'}
                    value={formData.puk}
                    onChange={(e) => setFormData({ ...formData, puk: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                    placeholder="8 cifre"
                    pattern="[0-9]{8}"
                    required={!editingSim}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPuk(!showPuk)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPuk ? '👁️' : '🙈'}
                  </button>
                </div>
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status *
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                  required
                >
                  <option value="disponibile">Disponibile</option>
                  <option value="assegnata">Assegnata</option>
                  <option value="disattivata">Disattivata</option>
                </select>
              </div>

              {/* Bottoni */}
              <div className="flex gap-3 mt-6">
                <Button
                  variant="secondary"
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    resetForm();
                  }}
                  fullWidth
                >
                  Annulla
                </Button>
                <Button
                  variant="primary"
                  type="submit"
                  fullWidth
                >
                  {editingSim ? 'Aggiorna' : 'Crea'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Visualizza Credenziali */}
      {showCredentialsModal && selectedSim && credentials && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-2xl font-bold mb-4 text-asset-manager-gray">
              🔐 Credenziali SIM
            </h2>

            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Seriale</p>
                <p className="font-mono font-bold text-lg">{selectedSim.seriale}</p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Numero Telefono</p>
                <p className="font-mono font-bold text-lg">{selectedSim.numero_telefono}</p>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg border-2 border-asset-manager-yellow">
                <p className="text-sm text-gray-600 mb-1">PIN</p>
                <p className="font-mono font-bold text-2xl text-asset-manager-gray">{credentials.pin}</p>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg border-2 border-asset-manager-yellow">
                <p className="text-sm text-gray-600 mb-1">PUK</p>
                <p className="font-mono font-bold text-2xl text-asset-manager-gray">{credentials.puk}</p>
              </div>

              <div className="bg-red-50 border border-red-300 rounded-lg p-3">
                <p className="text-xs text-red-700">
                  ⚠️ <strong>Attenzione:</strong> Queste credenziali sono sensibili. 
                  Non condividerle via email o chat. Annotale in modo sicuro.
                </p>
              </div>
            </div>

            <Button
              variant="secondary"
              onClick={() => {
                setShowCredentialsModal(false);
                setCredentials(null);
                setSelectedSim(null);
              }}
              fullWidth
              className="mt-6"
            >
              Chiudi
            </Button>
          </div>
        </div>
      )}

      {/* Modal Assegnazione */}
      {showAssignModal && selectedSim && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-2xl font-bold mb-4 text-asset-manager-gray">
              👤 Assegna SIM
            </h2>

            <div className="mb-4 bg-gray-50 p-3 rounded-lg">
              <p className="text-sm text-gray-600">SIM da assegnare:</p>
              <p className="font-mono font-bold">{selectedSim.seriale}</p>
              <p className="text-sm">{selectedSim.numero_telefono}</p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Seleziona Persona *
              </label>
              <select
                value={selectedPersonId || ''}
                onChange={(e) => setSelectedPersonId(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
              >
                <option value="">-- Seleziona --</option>
                {people.map((person) => (
                  <option key={person.id} value={person.id}>
                    {person.first_name} {person.last_name}
                    {person.mobile_phone && ` (${person.mobile_phone})`}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowAssignModal(false);
                  setSelectedSim(null);
                  setSelectedPersonId(null);
                }}
                fullWidth
              >
                Annulla
              </Button>
              <Button
                variant="primary"
                onClick={handleAssignSim}
                fullWidth
              >
                Assegna
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sims;
