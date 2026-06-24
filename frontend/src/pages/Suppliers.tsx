import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import { auth } from '../auth';
import { TruckIcon } from '@heroicons/react/24/outline';
import type { Supplier } from '../types';

interface SupplierForm {
  name: string;
  contact_person: string;
  phone: string;
  email: string;
  website: string;
  contract_number: string;
  warranty_conditions: string;
  warranty_duration_months: string;
  notes: string;
  is_active: boolean;
}

interface SupplierAsset {
  id: number;
  asset_code: string | null;
  serial_number: string;
  manufacturer: string;
  model: string;
  status: string;
  is_active: boolean;
}

const PAGE_SIZE = 10;

export default function Suppliers() {
  const currentUser = auth.getUser();
  const canCreateEdit = currentUser?.role === 'admin' || currentUser?.role === 'operatore';
  const canDelete = currentUser?.role === 'admin';

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showOnlyActive, setShowOnlyActive] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [detailSupplier, setDetailSupplier] = useState<Supplier | null>(null);
  const [detailAssets, setDetailAssets] = useState<SupplierAsset[]>([]);
  const [detailAssetsLoading, setDetailAssetsLoading] = useState(false);
  const [formData, setFormData] = useState<SupplierForm>({
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    website: '',
    contract_number: '',
    warranty_conditions: '',
    warranty_duration_months: '',
    notes: '',
    is_active: true,
  });

  useEffect(() => {
    fetchSuppliers();
  }, [page, search, showOnlyActive]);

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      const params: Record<string, string | number | boolean | undefined> = {
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      };
      if (search) params.search = search;
      if (showOnlyActive) params.is_active = true;
      const response = await api.get('/suppliers', { params });
      setSuppliers(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Errore caricamento fornitori:', error);
      alert('Errore nel caricamento dei fornitori');
    } finally {
      setLoading(false);
    }
  };

  const fetchSupplierAssets = async (supplierId: number) => {
    try {
      setDetailAssetsLoading(true);
      const response = await api.get(`/suppliers/${supplierId}/assets`, {
        params: { skip: 0, limit: 100 },
      });
      setDetailAssets(response.data.items || []);
    } catch (error) {
      console.error('Errore caricamento asset fornitore:', error);
      setDetailAssets([]);
    } finally {
      setDetailAssetsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        contact_person: formData.contact_person.trim() || null,
        phone: formData.phone.trim() || null,
        email: formData.email.trim() || null,
        website: formData.website.trim() || null,
        contract_number: formData.contract_number.trim() || null,
        warranty_conditions: formData.warranty_conditions.trim() || null,
        warranty_duration_months: formData.warranty_duration_months
          ? parseInt(formData.warranty_duration_months, 10)
          : null,
        notes: formData.notes.trim() || null,
      };
      if (editingSupplier) {
        await api.put(`/suppliers/${editingSupplier.id}`, payload);
      } else {
        await api.post('/suppliers', payload);
      }
      setShowModal(false);
      resetForm();
      fetchSuppliers();
    } catch (error: unknown) {
      console.error('Errore salvataggio fornitore:', error);
      alert(getApiError(error, 'Errore nel salvataggio del fornitore'));
    }
  };

  const handleEdit = (supplier: Supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      name: supplier.name,
      contact_person: supplier.contact_person || '',
      phone: supplier.phone || '',
      email: supplier.email || '',
      website: supplier.website || '',
      contract_number: supplier.contract_number || '',
      warranty_conditions: supplier.warranty_conditions || '',
      warranty_duration_months: supplier.warranty_duration_months?.toString() || '',
      notes: supplier.notes || '',
      is_active: supplier.is_active,
    });
    setShowModal(true);
  };

  const handleViewDetail = (supplier: Supplier) => {
    setDetailSupplier(supplier);
    setDetailAssets([]);
    setShowDetailModal(true);
    fetchSupplierAssets(supplier.id);
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Disattivare questo fornitore?')) return;
    try {
      await api.delete(`/suppliers/${id}`);
      setShowDetailModal(false);
      setDetailSupplier(null);
      fetchSuppliers();
    } catch (error: unknown) {
      console.error('Errore disattivazione fornitore:', error);
      alert(getApiError(error, 'Errore nella disattivazione del fornitore'));
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      contact_person: '',
      phone: '',
      email: '',
      website: '',
      contract_number: '',
      warranty_conditions: '',
      warranty_duration_months: '',
      notes: '',
      is_active: true,
    });
    setEditingSupplier(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  const handleCloseDetailModal = () => {
    setShowDetailModal(false);
    setDetailSupplier(null);
    setDetailAssets([]);
  };

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
      {/* HEADER */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-600 rounded-xl flex items-center justify-center shadow-lg">
            <TruckIcon className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Fornitori</h1>
            <p className="text-sm text-gray-600 mt-1">Gestisci l&apos;anagrafica fornitori e i contratti</p>
          </div>
        </div>
        <div className="flex justify-end">
          {canCreateEdit && (
            <Button variant="primary" icon="➕" onClick={() => setShowModal(true)}>
              Nuovo Fornitore
            </Button>
          )}
        </div>
      </div>

      {/* Barra ricerca e filtri */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <input
          type="text"
          placeholder="Cerca per nome..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
        />
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700 whitespace-nowrap">
          <input
            type="checkbox"
            checked={showOnlyActive}
            onChange={(e) => setShowOnlyActive(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-asset-manager-yellow"
          />
          Mostra solo attivi
        </label>
      </div>

      {/* Tabella fornitori */}
      {loading ? (
        <div className="text-center py-12 text-gray-600">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
          <p className="mt-2">Caricamento...</p>
        </div>
      ) : (
        <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-gray-200">
              <thead className="bg-asset-manager-gray text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Nome</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Referente</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Telefono</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Contratto</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Garanzia (mesi)</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Stato</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold">Azioni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {suppliers.map((s) => (
                  <tr key={s.id} className="hover:bg-yellow-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{s.name}</td>
                    <td className="px-6 py-4 text-gray-600">{s.contact_person || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{s.phone || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{s.email || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{s.contract_number || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{s.warranty_duration_months ?? '-'}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                          s.is_active
                            ? 'bg-green-100 text-green-800 border border-green-200'
                            : 'bg-gray-100 text-gray-600 border border-gray-200'
                        }`}
                      >
                        {s.is_active ? 'Attivo' : 'Inattivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="secondary"
                          icon="👁"
                          iconOnly
                          title="Dettaglio"
                          onClick={() => handleViewDetail(s)}
                        />
                        {canCreateEdit && (
                          <Button
                            variant="primary"
                            icon="✏️"
                            iconOnly
                            title="Modifica"
                            onClick={() => handleEdit(s)}
                          />
                        )}
                        {canDelete && s.is_active && (
                          <Button
                            variant="destructive"
                            icon="🗑"
                            iconOnly
                            title="Disattiva"
                            onClick={() => handleDeactivate(s.id)}
                          />
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {suppliers.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex flex-col items-center">
                        <span className="text-4xl mb-2">📦</span>
                        <p className="text-lg font-medium">Nessun fornitore trovato</p>
                        <p className="text-sm mt-1">
                          {showOnlyActive
                            ? 'Prova a modificare i filtri di ricerca'
                            : 'Disattiva "Mostra solo attivi" per vedere tutti i fornitori'}
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

      {/* Paginazione */}
      {total > PAGE_SIZE && (
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Mostrati {(page - 1) * PAGE_SIZE + 1} - {Math.min(page * PAGE_SIZE, total)} di {total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              Precedente
            </Button>
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Successiva
            </Button>
          </div>
        </div>
      )}

      {/* Modal Crea/Modifica */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">
              {editingSupplier ? 'Modifica Fornitore' : 'Nuovo Fornitore'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Nome *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Referente</label>
                  <input
                    type="text"
                    value={formData.contact_person}
                    onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Telefono</label>
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Email</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Sito web</label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Numero contratto</label>
                  <input
                    type="text"
                    value={formData.contract_number}
                    onChange={(e) => setFormData({ ...formData, contract_number: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Condizioni garanzia</label>
                  <textarea
                    value={formData.warranty_conditions}
                    onChange={(e) => setFormData({ ...formData, warranty_conditions: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Durata garanzia (mesi)</label>
                  <input
                    type="number"
                    min={0}
                    value={formData.warranty_duration_months}
                    onChange={(e) => setFormData({ ...formData, warranty_duration_months: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Note</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    rows={3}
                  />
                </div>
                <div className="flex items-center pt-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-asset-manager-yellow"
                  />
                  <label className="ml-2 text-sm font-medium text-gray-700">Attivo</label>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
                <Button variant="secondary" type="button" onClick={handleCloseModal}>
                  Annulla
                </Button>
                <Button variant="primary" type="submit">
                  {editingSupplier ? 'Salva Modifiche' : 'Crea Fornitore'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Dettaglio */}
      {showDetailModal && detailSupplier && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Dettaglio Fornitore</h2>
            <div className="space-y-4">
              <div>
                <span className="text-sm font-medium text-gray-500">Nome</span>
                <p className="text-lg font-semibold">{detailSupplier.name}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-500">Referente</span>
                  <p>{detailSupplier.contact_person || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Telefono</span>
                  <p>{detailSupplier.phone || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Email</span>
                  <p>{detailSupplier.email || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Sito web</span>
                  <p>{detailSupplier.website || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Contratto</span>
                  <p>{detailSupplier.contract_number || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Garanzia (mesi)</span>
                  <p>{detailSupplier.warranty_duration_months ?? '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Stato</span>
                  <p>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded text-sm ${
                        detailSupplier.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {detailSupplier.is_active ? 'Attivo' : 'Inattivo'}
                    </span>
                  </p>
                </div>
              </div>
              {detailSupplier.warranty_conditions && (
                <div>
                  <span className="text-sm font-medium text-gray-500">Condizioni garanzia</span>
                  <p className="whitespace-pre-wrap">{detailSupplier.warranty_conditions}</p>
                </div>
              )}
              {detailSupplier.notes && (
                <div>
                  <span className="text-sm font-medium text-gray-500">Note</span>
                  <p className="whitespace-pre-wrap">{detailSupplier.notes}</p>
                </div>
              )}
              <div className="pt-4 border-t border-gray-200">
                <h3 className="font-semibold text-gray-800 mb-3">Asset collegati</h3>
                {detailAssetsLoading ? (
                  <div className="flex items-center gap-2 text-gray-700">
                    <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-asset-manager-yellow"></div>
                    Caricamento...
                  </div>
                ) : detailAssets.length === 0 ? (
                  <p className="text-gray-500">Nessun asset collegato</p>
                ) : (
                  <ul className="space-y-2">
                    {detailAssets.map((a) => (
                      <li
                        key={a.id}
                        className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-lg"
                      >
                        <span className="font-medium">
                          {a.manufacturer} {a.model} — SN: {a.serial_number}
                        </span>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            a.is_active ? 'bg-blue-100 text-blue-800' : 'bg-gray-200 text-gray-600'
                          }`}
                        >
                          {a.status}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
              {canCreateEdit && (
                <Button
                  variant="primary"
                  onClick={() => {
                    handleEdit(detailSupplier);
                    handleCloseDetailModal();
                  }}
                >
                  ✏️ Modifica
                </Button>
              )}
              {canDelete && detailSupplier.is_active && (
                <Button variant="destructive" onClick={() => handleDeactivate(detailSupplier.id)}>
                  🗑 Disattiva
                </Button>
              )}
              <Button variant="secondary" onClick={handleCloseDetailModal}>
                Chiudi
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
