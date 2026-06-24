import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import StatsCard from '../components/common/StatsCard';
import { ArchiveBoxIcon, ExclamationTriangleIcon, CheckCircleIcon, FolderIcon } from '@heroicons/react/24/outline';
import { auth } from '../auth';
import type { Site } from '../types';

interface InventoryItem {
  id: number;
  category: string;
  device: string;
  brand: string | null;
  site_id: number | null;
  quantity: number;
  min_quantity: number;
  notes: string | null;
  is_active: boolean;
  is_low_stock: boolean;
  created_at: string;
  updated_at: string;
}

interface InventoryForm {
  category: string;
  device: string;
  brand: string;
  site_id: number | null;
  quantity: number;
  min_quantity: number;
  notes: string;
  is_active: boolean;
}

export default function Inventory() {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';
  
  const [sites, setSites] = useState<Site[]>([]);
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('');
  const [showLowStockOnly, setShowLowStockOnly] = useState(false);
  const [lowStockCount, setLowStockCount] = useState(0);

  const [formData, setFormData] = useState<InventoryForm>({
    category: '',
    device: '',
    brand: '',
    site_id: null,
    quantity: 0,
    min_quantity: 5,
    notes: '',
    is_active: true
  });

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
    fetchCategories();
    fetchSites();
  }, []);

  useEffect(() => {
    fetchItems();
  }, [search, showInactive, selectedCategoryFilter, showLowStockOnly]);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/inventory/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Errore caricamento categorie:', error);
    }
  };

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (search) params.search = search;
      if (!showInactive) params.is_active = true;
      if (selectedCategoryFilter) params.category = selectedCategoryFilter;
      if (showLowStockOnly) params.low_stock_only = true;

      const response = await api.get('/inventory', { params });
      setItems(response.data.items);
      setLowStockCount(response.data.low_stock_count);
    } catch (error) {
      console.error('Errore caricamento materiali:', error);
      alert('Errore nel caricamento dei materiali');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await api.put(`/inventory/${editingItem.id}`, formData);
      } else {
        await api.post('/inventory', formData);
      }
      setShowModal(false);
      resetForm();
      fetchItems();
      fetchCategories(); // Ricarica categorie se ne è stata creata una nuova
    } catch (error: unknown) {
      console.error('Errore salvataggio materiale:', error);
      alert(getApiError(error, 'Errore nel salvataggio del materiale'));
    }
  };

  const handleEdit = (item: InventoryItem) => {
    setEditingItem(item);
    setFormData({
      category: item.category,
      device: item.device,
      brand: item.brand || '',
      site_id: item.site_id,
      quantity: item.quantity,
      min_quantity: item.min_quantity,
      notes: item.notes || '',
      is_active: item.is_active
    });
    setShowModal(true);
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Disattivare questo materiale?')) return;
    try {
      await api.delete(`/inventory/${id}`);
      fetchItems();
    } catch (error) {
      console.error('Errore disattivazione materiale:', error);
      alert('Errore nella disattivazione del materiale');
    }
  };

  const handleReactivate = async (id: number) => {
    try {
      await api.put(`/inventory/${id}`, { is_active: true });
      fetchItems();
    } catch (error) {
      console.error('Errore riattivazione materiale:', error);
      alert('Errore nella riattivazione del materiale');
    }
  };

  const handleHardDelete = async (id: number) => {
    if (!confirm('⚠️ ATTENZIONE: Questa operazione è IRREVERSIBILE.\n\nEliminare definitivamente questo materiale dal database?')) return;
    try {
      await api.delete(`/inventory/${id}/hard`);
      fetchItems();
    } catch (error) {
      console.error('Errore eliminazione materiale:', error);
      alert('Errore nell\'eliminazione definitiva del materiale');
    }
  };

  const handleQuickAdjust = async (id: number, adjustment: number) => {
    try {
      await api.patch(`/inventory/${id}/adjust?adjustment=${adjustment}`);
      fetchItems();
    } catch (error: unknown) {
      console.error('Errore aggiustamento quantità:', error);
      alert(getApiError(error, 'Errore nell\'aggiustamento della quantità'));
    }
  };

  const resetForm = () => {
    setFormData({
      category: '',
      device: '',
      brand: '',
      site_id: null,
      quantity: 0,
      min_quantity: 5,
      notes: '',
      is_active: true
    });
    setEditingItem(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  // Calcolo statistiche magazzino
  const totalItems = items.length;
  const lowStockItems = items.filter(i => i.is_low_stock).length;
  const okStockItems = totalItems - lowStockItems;
  const uniqueCategories = [...new Set(items.map(i => i.category))].length;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        {/* HEADER MODERNO */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-red-500 rounded-xl flex items-center justify-center shadow-lg">
              <ArchiveBoxIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Gestione Magazzino</h1>
              <p className="text-sm text-gray-600 mt-1">Gestisci i materiali di consumo e le scorte</p>
            </div>
          </div>
          <div className="flex justify-end">
            {!isUser && (
              <Button
                variant="primary"
                icon="➕"
                onClick={() => setShowModal(true)}
              >
                Nuovo Materiale
              </Button>
            )}
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Totale Materiali"
            value={totalItems}
            subtitle="Tipologie gestite"
            icon={ArchiveBoxIcon}
            gradient="blue"
          />

          <StatsCard
            title="Sotto Soglia"
            value={lowStockItems}
            icon={ExclamationTriangleIcon}
            gradient="red"
            badge={lowStockItems > 0 ? {
              text: 'Riordina',
              variant: 'warning'
            } : {
              text: 'Tutto OK',
              variant: 'success'
            }}
          />

          <StatsCard
            title="Scorte OK"
            value={okStockItems}
            subtitle={`${totalItems > 0 ? Math.round((okStockItems/totalItems)*100) : 0}% del totale`}
            icon={CheckCircleIcon}
            gradient="green"
          />

          <StatsCard
            title="Categorie"
            value={uniqueCategories}
            subtitle="Categorie uniche"
            icon={FolderIcon}
            gradient="purple"
          />
        </div>

        {/* Alert sotto soglia */}
        {lowStockCount > 0 && (
          <div className="mb-4 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-lg shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <span className="font-medium">Attenzione!</span> {lowStockCount} {lowStockCount === 1 ? 'materiale è' : 'materiali sono'} sotto la soglia minima.
                  <button
                    onClick={() => setShowLowStockOnly(!showLowStockOnly)}
                    className="ml-2 underline hover:no-underline font-medium"
                  >
                    {showLowStockOnly ? 'Mostra tutti' : 'Visualizza'}
                  </button>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Filtri */}
        <div className="mb-4 flex gap-4 items-center flex-wrap">
          <input
            type="text"
            placeholder="Cerca per dispositivo, marca o categoria..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 min-w-[250px] px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          />
          <select
            value={selectedCategoryFilter}
            onChange={(e) => setSelectedCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          >
            <option value="">Tutte le categorie</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="w-4 h-4 text-asset-manager-gray rounded focus:ring-2 focus:ring-asset-manager-yellow"
            />
            Mostra inattivi
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
                  <th className="px-6 py-3 text-left">Categoria</th>
                  <th className="px-6 py-3 text-left">Dispositivo</th>
                  <th className="px-6 py-3 text-left">Marca</th>
                  <th className="px-6 py-3 text-left">Sede</th>
                  <th className="px-6 py-3 text-center">Quantità</th>
                  <th className="px-6 py-3 text-left">Stato</th>
                  <th className="px-6 py-3 text-right">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className={`border-t hover:bg-yellow-50 transition-colors ${item.is_low_stock ? 'bg-red-50' : ''}`}>
                    <td className="px-6 py-4">{item.category}</td>
                    <td className="px-6 py-4 font-medium">{item.device}</td>
                    <td className="px-6 py-4">{item.brand || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">
                      {item.site_id ? (
                        sites.find(s => s.id === item.site_id)?.name || '-'
                      ) : (
                        <span className="text-gray-400">Non assegnata</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {!isUser ? (
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleQuickAdjust(item.id, -1)}
                            className="w-6 h-6 rounded bg-red-100 hover:bg-red-200 text-red-700 flex items-center justify-center text-sm font-bold"
                            title="Scarica 1"
                          >
                            -
                          </button>
                          <span className={`text-lg font-semibold min-w-[3ch] text-center ${item.is_low_stock ? 'text-yellow-700' : ''}`}>
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => handleQuickAdjust(item.id, 1)}
                            className="w-6 h-6 rounded bg-green-100 hover:bg-green-200 text-green-700 flex items-center justify-center text-sm font-bold"
                            title="Carica 1"
                          >
                            +
                          </button>
                        </div>
                      ) : (
                        <span className={`text-lg font-semibold min-w-[3ch] text-center ${item.is_low_stock ? 'text-yellow-700' : ''}`}>
                          {item.quantity}
                        </span>
                      )}
                      {item.is_low_stock && (
                        <div className="text-xs text-yellow-600 text-center mt-1">
                          ⚠️ Sotto soglia ({item.min_quantity})
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                        item.is_active 
                          ? 'bg-green-50 text-green-700 border-green-200' 
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}>
                        {item.is_active ? '✓ Attivo' : '✗ Inattivo'}
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
                            title="Modifica materiale"
                            onClick={() => handleEdit(item)}
                          />
                          
                          {item.is_active ? (
                            <>
                              {/* 2. Disattiva - SECONDARY */}
                              <Button
                                variant="secondary"
                                icon="⏸️"
                                iconOnly
                                title="Disattiva materiale"
                                onClick={() => handleDeactivate(item.id)}
                              />
                            </>
                          ) : (
                            <>
                              {/* 2. Riattiva - SECONDARY */}
                              <Button
                                variant="secondary"
                                icon="▶️"
                                iconOnly
                                title="Riattiva materiale"
                                onClick={() => handleReactivate(item.id)}
                              />
                              {/* 3. Elimina - DESTRUCTIVE (sempre rosso) */}
                              <Button
                                variant="destructive"
                                icon="🗑️"
                                iconOnly
                                title="Elimina definitivamente"
                                onClick={() => handleHardDelete(item.id)}
                              />
                            </>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                      Nessun materiale trovato
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
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">
                {editingItem ? 'Modifica Materiale' : 'Nuovo Materiale'}
              </h2>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Categoria *</label>
                      <input
                        type="text"
                        required
                        list="categories-list"
                        value={formData.category}
                        onChange={(e) => setFormData({...formData, category: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                      <datalist id="categories-list">
                        {categories.map(cat => (
                          <option key={cat} value={cat} />
                        ))}
                      </datalist>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Marca</label>
                      <input
                        type="text"
                        value={formData.brand}
                        onChange={(e) => setFormData({...formData, brand: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Sede</label>
                      <select
                        value={formData.site_id ?? ''}
                        onChange={(e) => setFormData({...formData, site_id: e.target.value ? parseInt(e.target.value) : null})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      >
                        <option value="">Nessuna sede</option>
                        {sites.map(site => (
                          <option key={site.id} value={site.id}>
                            {site.name} {site.city ? `(${site.city})` : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Dispositivo *</label>
                    <input
                      type="text"
                      required
                      value={formData.device}
                      onChange={(e) => setFormData({...formData, device: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Quantità *</label>
                      <input
                        type="number"
                        required
                        min="0"
                        value={formData.quantity}
                        onChange={(e) => setFormData({...formData, quantity: parseInt(e.target.value) || 0})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Soglia minima alert *</label>
                      <input
                        type="number"
                        required
                        min="0"
                        value={formData.min_quantity}
                        onChange={(e) => setFormData({...formData, min_quantity: parseInt(e.target.value) || 5})}
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
                    <label className="text-sm font-medium text-gray-700">Materiale attivo</label>
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
                    {editingItem ? 'Salva Modifiche' : 'Crea Materiale'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
    </div>
  );
}
