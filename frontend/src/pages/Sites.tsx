import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import { auth } from '../auth';
import StatsCard from '../components/common/StatsCard';
import { BuildingOfficeIcon } from '@heroicons/react/24/outline';
import type { Site } from '../types';

interface SiteForm {
  name: string;
  address: string;
  city: string;
  postal_code: string;
  country: string;
  centralino: string;
  notes: string;
  is_active: boolean;
}

export default function Sites() {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';
  
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSite, setEditingSite] = useState<Site | null>(null);
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [formData, setFormData] = useState<SiteForm>({
    name: '',
    address: '',
    city: '',
    postal_code: '',
    country: 'Italia',
    centralino: '',
    notes: '',
    is_active: true
  });

  useEffect(() => {
    fetchSites();
  }, [search, showInactive]);

  const fetchSites = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (search) {
        params.search = search;
      }
      if (!showInactive) {
        params.is_active = true;
      }
      const response = await api.get('/sites', { params });
      setSites(response.data.items);
    } catch (error) {
      console.error('Errore caricamento sedi:', error);
      alert('Errore nel caricamento delle sedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSite) {
        await api.put(`/sites/${editingSite.id}`, formData);
      } else {
        await api.post('/sites', formData);
      }
      setShowModal(false);
      resetForm();
      fetchSites();
    } catch (error: unknown) {
      console.error('Errore salvataggio sede:', error);
      alert(getApiError(error, 'Errore nel salvataggio della sede'));
    }
  };

  const handleEdit = (site: Site) => {
    setEditingSite(site);
    setFormData({
      name: site.name,
      address: site.address || '',
      city: site.city || '',
      postal_code: site.postal_code || '',
      country: site.country || 'Italia',
      centralino: site.centralino || '',
      notes: site.notes || '',
      is_active: site.is_active
    });
    setShowModal(true);
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Disattivare questa sede?')) return;
    try {
      await api.delete(`/sites/${id}`);
      fetchSites();
    } catch (error) {
      console.error('Errore disattivazione sede:', error);
      alert('Errore nella disattivazione della sede');
    }
  };

  const handleReactivate = async (id: number) => {
    try {
      await api.put(`/sites/${id}`, { is_active: true });
      fetchSites();
    } catch (error) {
      console.error('Errore riattivazione sede:', error);
      alert('Errore nella riattivazione della sede');
    }
  };

  const handleHardDelete = async (id: number) => {
    if (!confirm('⚠️ ATTENZIONE: Questa operazione è IRREVERSIBILE.\n\nEliminare definitivamente questa sede dal database?')) return;
    try {
      await api.delete(`/sites/${id}/hard`);
      fetchSites();
    } catch (error) {
      console.error('Errore eliminazione sede:', error);
      alert('Errore nell\'eliminazione definitiva della sede');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      address: '',
      city: '',
      postal_code: '',
      country: 'Italia',
      centralino: '',
      notes: '',
      is_active: true
    });
    setEditingSite(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  const totalSites = sites.length;
  const activeSites = sites.filter((s) => s.is_active).length;
  const inactiveSites = totalSites - activeSites;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        {/* HEADER MODERNO */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <BuildingOfficeIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Gestione Sedi</h1>
              <p className="text-sm text-gray-600 mt-1">Gestisci le sedi aziendali e le loro informazioni</p>
            </div>
          </div>
          <div className="flex justify-end">
            {!isUser && (
              <Button
                variant="primary"
                icon="➕"
                onClick={() => setShowModal(true)}
              >
                Nuova Sede
              </Button>
            )}
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatsCard
            title="Totale Sedi"
            value={totalSites}
            subtitle="Sedi registrate"
            icon={BuildingOfficeIcon}
            gradient="blue"
          />

          <StatsCard
            title="Sedi Attive"
            value={activeSites}
            subtitle={`${totalSites > 0 ? Math.round((activeSites / totalSites) * 100) : 0}% del totale`}
            icon={BuildingOfficeIcon}
            gradient="green"
          />

          <StatsCard
            title="Sedi Inattive"
            value={inactiveSites}
            icon={BuildingOfficeIcon}
            gradient="red"
            badge={
              inactiveSites > 0
                ? {
                    text: 'Attenzione',
                    variant: 'warning',
                  }
                : undefined
            }
          />
        </div>

        {/* Barra ricerca e filtri */}
        <div className="mb-6 flex gap-4 items-center">
          <input
            type="text"
            placeholder="Cerca per nome o città..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          />
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 whitespace-nowrap">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-asset-manager-yellow"
            />
            Mostra sedi inattive
          </label>
        </div>

        {/* Tabella sedi */}
        {loading ? (
          <div className="text-center py-12 text-gray-600">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
            <p className="mt-2">Caricamento...</p>
          </div>
        ) : (
          <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
            <div className="overflow-hidden">
              <table className="w-full table-fixed divide-y divide-gray-200">
              <thead className="bg-asset-manager-gray text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Nome</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Indirizzo</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Città</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">CAP</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Paese</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Centralino</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-white">Stato</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-white">Azioni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sites.map((site) => (
                  <tr key={site.id} className="hover:bg-yellow-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{site.name}</td>
                    <td className="px-6 py-4 text-gray-600">{site.address || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{site.city || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{site.postal_code || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{site.country || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{site.centralino || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        site.is_active
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : 'bg-red-100 text-red-800 border border-red-200'
                      }`}>
                        {site.is_active ? '✓ Attiva' : '✗ Inattiva'}
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
                            title="Modifica sede"
                            onClick={() => handleEdit(site)}
                          />
                          
                          {site.is_active ? (
                            <>
                              {/* 2. Disattiva - SECONDARY */}
                              <Button
                                variant="secondary"
                                icon="⏸️"
                                iconOnly
                                title="Disattiva sede"
                                onClick={() => handleDeactivate(site.id)}
                              />
                            </>
                          ) : (
                            <>
                              {/* 2. Riattiva - SECONDARY */}
                              <Button
                                variant="secondary"
                                icon="▶️"
                                iconOnly
                                title="Riattiva sede"
                                onClick={() => handleReactivate(site.id)}
                              />
                              {/* 3. Elimina - DESTRUCTIVE (sempre rosso) */}
                              <Button
                                variant="destructive"
                                icon="🗑️"
                                iconOnly
                                title="Elimina definitivamente"
                                onClick={() => handleHardDelete(site.id)}
                              />
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {sites.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex flex-col items-center">
                        <span className="text-4xl mb-2">📋</span>
                        <p className="text-lg font-medium">Nessuna sede trovata</p>
                        <p className="text-sm mt-1">
                          {showInactive 
                            ? 'Prova a modificare i filtri di ricerca' 
                            : 'Attiva "Mostra sedi inattive" per vedere tutte le sedi'}
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>
          </div>
        )}

        {/* Modal Form */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
              <h2 className="text-2xl font-bold mb-6 text-gray-800">
                {editingSite ? 'Modifica Sede' : 'Nuova Sede'}
              </h2>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Nome *</label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Indirizzo</label>
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) => setFormData({...formData, address: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-700">Città</label>
                      <input
                        type="text"
                        value={formData.city}
                        onChange={(e) => setFormData({...formData, city: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-700">CAP</label>
                      <input
                        type="text"
                        value={formData.postal_code}
                        onChange={(e) => setFormData({...formData, postal_code: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Paese</label>
                    <input
                      type="text"
                      value={formData.country}
                      onChange={(e) => setFormData({...formData, country: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      placeholder="Italia"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Centralino/Prefisso</label>
                    <input
                      type="text"
                      value={formData.centralino}
                      onChange={(e) => setFormData({...formData, centralino: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      placeholder="+39 06 12345"
                    />
                    <p className="text-xs text-gray-500 mt-1">Formato internazionale (es. +39 06 12345)</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Note</label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({...formData, notes: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      rows={3}
                    />
                  </div>
                  <div className="flex items-center pt-2">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-asset-manager-yellow"
                    />
                    <label className="ml-2 text-sm font-medium text-gray-700">Sede attiva</label>
                  </div>
                </div>
                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
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
                    {editingSite ? 'Salva Modifiche' : 'Crea Sede'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
    </div>
  );
}
