import React, { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import StatsCard from '../components/common/StatsCard';
import { IdentificationIcon, CheckCircleIcon, UserGroupIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { auth } from '../auth';
import type { Badge, Person, Site } from '../types';

const Badges: React.FC = () => {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';

  // State
  const [badges, setBadges] = useState<Badge[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBadge, setEditingBadge] = useState<Badge | null>(null);

  // Filtri
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [tipoFilter, setTipoFilter] = useState<string>('');
  const [siteFilter, setSiteFilter] = useState<string>('');
  const [scadutiFilter, setScadutiFilter] = useState<string>('');

  // Form
  const [formData, setFormData] = useState({
    numero_badge: '',
    tipo: 'dipendente' as 'dipendente' | 'visitatore' | 'temporaneo',
    status: 'attivo' as 'attivo' | 'disattivo' | 'smarrito',
    data_emissione: new Date().toISOString().split('T')[0],
    data_scadenza: '',
    site_id: null as number | null,
    person_id: null as number | null,
    notes: '',
    is_active: true
  });

  // Fetch Badges
  const fetchBadges = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);
      if (tipoFilter) params.append('tipo', tipoFilter);
      if (siteFilter) params.append('site_id', siteFilter);
      if (scadutiFilter) {
        params.append('scaduti', scadutiFilter === 'true' ? 'true' : 'false');
      }

      const response = await api.get(`/badges?${params.toString()}`);
      setBadges(response.data.items);
    } catch (error) {
      console.error('Errore caricamento badge:', error);
      alert('Errore nel caricamento dei badge');
    } finally {
      setLoading(false);
    }
  };

  // Fetch People
  const fetchPeople = async () => {
    try {
      const response = await api.get('/people?limit=1000');
      setPeople(response.data.items);
    } catch (error) {
      console.error('Errore caricamento persone:', error);
    }
  };

  // Fetch Sites
  const fetchSites = async () => {
    try {
      const response = await api.get('/sites?limit=500&is_active=true');
      setSites(response.data.items || []);
    } catch (error) {
      console.error('Errore caricamento sedi:', error);
    }
  };

  useEffect(() => {
    fetchBadges();
    fetchPeople();
    fetchSites();
  }, [search, statusFilter, tipoFilter, siteFilter, scadutiFilter]);

  // Reset form
  const resetForm = () => {
    setFormData({
      numero_badge: '',
      tipo: 'dipendente',
      status: 'attivo',
      data_emissione: new Date().toISOString().split('T')[0],
      data_scadenza: '',
      site_id: null,
      person_id: null,
      notes: '',
      is_active: true
    });
    setEditingBadge(null);
  };

  // Apri modal creazione
  const handleCreate = () => {
    resetForm();
    setShowModal(true);
  };

  // Apri modal modifica
  const handleEdit = (badge: Badge) => {
    setEditingBadge(badge);
    setFormData({
      numero_badge: badge.numero_badge,
      tipo: badge.tipo,
      status: badge.status,
      data_emissione: badge.data_emissione,
      data_scadenza: badge.data_scadenza || '',
      site_id: badge.site_id,
      person_id: badge.person_id,
      notes: badge.notes || '',
      is_active: badge.is_active
    });
    setShowModal(true);
  };

  // Salva badge (create/update)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validazione
    if (!formData.numero_badge || !formData.data_emissione) {
      alert('Numero badge e data emissione sono obbligatori');
      return;
    }

    try {
      const payload = {
        ...formData,
        data_scadenza: formData.data_scadenza || null
      };

      if (editingBadge) {
        await api.put(`/badges/${editingBadge.id}`, payload);
        alert('Badge aggiornato con successo');
      } else {
        await api.post('/badges', payload);
        alert('Badge creato con successo');
      }

      setShowModal(false);
      resetForm();
      fetchBadges();
    } catch (error: unknown) {
      console.error('Errore salvataggio badge:', error);
      alert(getApiError(error, 'Errore nel salvataggio del badge'));
    }
  };

  // Elimina badge
  const handleDelete = async (id: number) => {
    if (!confirm('Sei sicuro di voler eliminare questo badge?')) return;

    try {
      await api.delete(`/badges/${id}`);
      alert('Badge eliminato con successo');
      fetchBadges();
    } catch (error: unknown) {
      console.error('Errore eliminazione badge:', error);
      alert(getApiError(error, 'Errore nell\'eliminazione del badge'));
    }
  };

  // Calcola statistiche
  const stats = {
    totale: badges.length,
    attivi: badges.filter(b => b.status === 'attivo').length,
    assegnati: badges.filter(b => b.person_id !== null).length,
    scaduti: badges.filter(b => {
      if (!b.data_scadenza) return false;
      return new Date(b.data_scadenza) < new Date();
    }).length
  };

  // Verifica se badge è scaduto
  const isBadgeScaduto = (badge: Badge): boolean => {
    if (!badge.data_scadenza) return false;
    return new Date(badge.data_scadenza) < new Date();
  };

  // Badge status badge CSS
  const getStatusBadge = (status: string) => {
    const styles = {
      attivo: 'bg-green-100 text-green-800 border-green-200',
      disattivo: 'bg-gray-100 text-gray-800 border-gray-200',
      smarrito: 'bg-red-100 text-red-800 border-red-200'
    };
    return styles[status as keyof typeof styles] || styles.disattivo;
  };

  // Tipo badge CSS
  const getTipoBadge = (tipo: string) => {
    const styles = {
      dipendente: 'bg-blue-100 text-blue-800 border-blue-200',
      visitatore: 'bg-purple-100 text-purple-800 border-purple-200',
      temporaneo: 'bg-orange-100 text-orange-800 border-orange-200'
    };
    return styles[tipo as keyof typeof styles] || styles.dipendente;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Caricamento badge...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
            <IdentificationIcon className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Badge Aziendali</h1>
            <p className="text-sm text-gray-600 mt-1">Gestione badge dipendenti, visitatori e temporanei</p>
          </div>
        </div>
        <div className="flex justify-end">
          {!isUser && (
            <Button
              variant="primary"
              icon="➕"
              onClick={handleCreate}
            >
              Nuovo Badge
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatsCard
          title="Totale Badge"
          value={stats.totale}
          icon={IdentificationIcon}
          gradient="blue"
        />
        <StatsCard
          title="Attivi"
          value={stats.attivi}
          icon={CheckCircleIcon}
          gradient="green"
        />
        <StatsCard
          title="Assegnati"
          value={stats.assegnati}
          icon={UserGroupIcon}
          gradient="purple"
        />
        <StatsCard
          title="Scaduti"
          value={stats.scaduti}
          icon={XCircleIcon}
          gradient="red"
          badge={stats.scaduti > 0 ? { text: 'Attenzione', variant: 'warning' } : undefined}
        />
      </div>

      {/* Filtri */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Search */}
          <input
            type="text"
            placeholder="🔍 Cerca badge, note..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
          />

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
          >
            <option value="">Tutti gli stati</option>
            <option value="attivo">Attivo</option>
            <option value="disattivo">Disattivo</option>
            <option value="smarrito">Smarrito</option>
          </select>

          {/* Tipo Filter */}
          <select
            value={tipoFilter}
            onChange={(e) => setTipoFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
          >
            <option value="">Tutti i tipi</option>
            <option value="dipendente">Dipendente</option>
            <option value="visitatore">Visitatore</option>
            <option value="temporaneo">Temporaneo</option>
          </select>

          {/* Site Filter */}
          <select
            value={siteFilter}
            onChange={(e) => setSiteFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
          >
            <option value="">Tutte le sedi</option>
            {sites.map(site => (
              <option key={site.id} value={site.id}>{site.name}</option>
            ))}
          </select>

          {/* Scaduti Filter */}
          <select
            value={scadutiFilter}
            onChange={(e) => setScadutiFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
          >
            <option value="">Tutti</option>
            <option value="false">Solo validi</option>
            <option value="true">Solo scaduti</option>
          </select>
        </div>
      </div>

      {/* Tabella Badge */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-asset-manager-gray text-white">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Numero Badge</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Tipo</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Assegnato a</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Sede</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Data Emissione</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Data Scadenza</th>
                {!isUser && (
                  <th className="px-4 py-3 text-right text-sm font-semibold">Azioni</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {badges.map((badge) => (
                <tr key={badge.id} className="border-t hover:bg-yellow-50 transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{badge.numero_badge}</span>
                      {isBadgeScaduto(badge) && (
                        <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">SCADUTO</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getTipoBadge(badge.tipo)}`}>
                      {badge.tipo}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadge(badge.status)}`}>
                      {badge.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {badge.person_first_name && badge.person_last_name
                      ? `${badge.person_first_name} ${badge.person_last_name}`
                      : '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {badge.site_name || '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(badge.data_emissione).toLocaleDateString('it-IT')}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {badge.data_scadenza
                      ? new Date(badge.data_scadenza).toLocaleDateString('it-IT')
                      : 'Nessuna'}
                  </td>
                  {!isUser && (
                    <td className="px-4 py-3 text-right space-x-2">
                      <button
                        onClick={() => handleEdit(badge)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        ✏️ Modifica
                      </button>
                      <button
                        onClick={() => handleDelete(badge.id)}
                        className="text-red-600 hover:text-red-800 font-medium"
                      >
                        🗑️ Elimina
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>

          {badges.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              Nessun badge trovato
            </div>
          )}
        </div>
      </div>

      {/* Modal Create/Edit */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">
                {editingBadge ? '✏️ Modifica Badge' : '➕ Nuovo Badge'}
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Numero Badge */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Numero Badge *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.numero_badge}
                    onChange={(e) => setFormData({ ...formData, numero_badge: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                    placeholder="es. B001, BADGE-2024-001"
                  />
                </div>

                {/* Tipo e Status */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo *
                    </label>
                    <select
                      required
                      value={formData.tipo}
                      onChange={(e) => setFormData({ ...formData, tipo: e.target.value as 'dipendente' | 'visitatore' | 'temporaneo' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                    >
                      <option value="dipendente">Dipendente</option>
                      <option value="visitatore">Visitatore</option>
                      <option value="temporaneo">Temporaneo</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status *
                    </label>
                    <select
                      required
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value as 'attivo' | 'disattivo' | 'smarrito' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                    >
                      <option value="attivo">Attivo</option>
                      <option value="disattivo">Disattivo</option>
                      <option value="smarrito">Smarrito</option>
                    </select>
                  </div>
                </div>

                {/* Date Emissione e Scadenza */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Emissione *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.data_emissione}
                      onChange={(e) => setFormData({ ...formData, data_emissione: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Scadenza
                    </label>
                    <input
                      type="date"
                      value={formData.data_scadenza}
                      onChange={(e) => setFormData({ ...formData, data_scadenza: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">Lascia vuoto se non scade</p>
                  </div>
                </div>

                {/* Sede */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sede
                  </label>
                  <select
                    value={formData.site_id ?? ''}
                    onChange={(e) => setFormData({ ...formData, site_id: e.target.value ? Number(e.target.value) : null })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                  >
                    <option value="">Nessuna sede</option>
                    {sites.map(site => (
                      <option key={site.id} value={site.id}>{site.name}</option>
                    ))}
                  </select>
                </div>

                {/* Note */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Note
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
                    placeholder="Note aggiuntive sul badge..."
                  />
                </div>

                {/* Buttons */}
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Annulla
                  </button>
                  <Button type="submit">
                    {editingBadge ? '💾 Salva Modifiche' : '➕ Crea Badge'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Badges;
