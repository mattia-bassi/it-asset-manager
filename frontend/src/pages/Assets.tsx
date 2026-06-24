import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import StatsCard from '../components/common/StatsCard';
import { CubeIcon, CheckCircleIcon, WrenchScrewdriverIcon, ArchiveBoxXMarkIcon } from '@heroicons/react/24/outline';
import { auth } from '../auth';
import type { Asset, AssetType, Site, Person, Supplier } from '../types';

interface AssetForm {
  asset_code: string;
  serial_number: string;
  mac_address: string;
  asset_type_id: number | null;
  manufacturer: string;
  model: string;
  site_id: number | null;
  person_id: number | null;
  supplier_id: number | null;
  status: string;
  purchase_date: string;
  warranty_expiry: string;
  specifications: Record<string, any>;
  notes: string;
  is_active: boolean;
}

const STATUS_OPTIONS = [
  'disponibile',
  'assegnato',
  'manutenzione',
  'dismissione',
  'dismesso'
];

export default function Assets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [assetTypes, setAssetTypes] = useState<AssetType[]>([]);
  const [flatAssetTypes, setFlatAssetTypes] = useState<AssetType[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<Asset | null>(null);
  const [search, setSearch] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [filterAssetTypeId, setFilterAssetTypeId] = useState<number | null>(null);
  const [filterSiteId, setFilterSiteId] = useState<number | null>(null);
  const [filterPersonId, setFilterPersonId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');

  // NUOVI STATE PER RITIRO MANUTENZIONE
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [maintenanceAsset, setMaintenanceAsset] = useState<Asset | null>(null);
  const [maintenanceReason, setMaintenanceReason] = useState('');
  const [maintenanceNotes, setMaintenanceNotes] = useState('');
  const [isSubmittingMaintenance, setIsSubmittingMaintenance] = useState(false);

  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';

  const [formData, setFormData] = useState<AssetForm>({
    asset_code: '',
    serial_number: '',
    mac_address: '',
    asset_type_id: null,
    manufacturer: '',
    model: '',
    site_id: null,
    person_id: null,
    supplier_id: null,
    status: 'disponibile',
    purchase_date: '',
    warranty_expiry: '',
    specifications: {},
    notes: '',
    is_active: true
  });

  useEffect(() => {
    fetchAssetTypes();
    fetchSites();
    fetchPeople();
    fetchSuppliers();
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [search, showInactive, filterAssetTypeId, filterSiteId, filterPersonId, filterStatus]);

  const flattenAssetTypes = (types: AssetType[], level = 0): AssetType[] => {
    let result: AssetType[] = [];
    for (const type of types) {
      result.push({ ...type, name: '  '.repeat(level) + type.name });
      if (type.children && type.children.length > 0) {
        result = result.concat(flattenAssetTypes(type.children, level + 1));
      }
    }
    return result;
  };

  const fetchAssetTypes = async () => {
    try {
      const response = await api.get('/asset-types/hierarchy');
      setAssetTypes(response.data);
      setFlatAssetTypes(flattenAssetTypes(response.data));
    } catch (error) {
      console.error('Errore caricamento tipi asset:', error);
    }
  };

  const fetchSites = async () => {
    try {
      const response = await api.get('/sites', { params: { limit: 1000, is_active: true } });
      setSites(response.data.items);
    } catch (error) {
      console.error('Errore caricamento sedi:', error);
    }
  };

  const fetchPeople = async () => {
    try {
      const response = await api.get('/people', { params: { limit: 1000, is_active: true } });
      setPeople(response.data.items);
    } catch (error) {
      console.error('Errore caricamento persone:', error);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const res = await api.get('/suppliers', { params: { limit: 500, is_active: true } });
      setSuppliers(res.data.items || []);
    } catch (err: unknown) {
      console.error('Failed to fetch suppliers:', err);
    }
  };

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (search) params.search = search;
      if (!showInactive) params.is_active = true;
      if (filterAssetTypeId) params.asset_type_id = filterAssetTypeId;
      if (filterSiteId) params.site_id = filterSiteId;
      if (filterPersonId) params.person_id = filterPersonId;
      if (filterStatus) params.asset_status = filterStatus;

      params.limit = 1000;
      const response = await api.get('/assets', { params });
      setAssets(response.data.items);
    } catch (error) {
      console.error('Errore caricamento asset:', error);
      alert('Errore nel caricamento degli asset');
    } finally {
      setLoading(false);
    }
  };

  const getSelectedAssetType = (): AssetType | null => {
    if (!formData.asset_type_id) return null;
    const findType = (types: AssetType[]): AssetType | null => {
      for (const type of types) {
        if (type.id === formData.asset_type_id) return type;
        if (type.children) {
          const found = findType(type.children);
          if (found) return found;
        }
      }
      return null;
    };
    return findType(assetTypes);
  };

  const renderDynamicFields = () => {
    const selectedType = getSelectedAssetType();
    if (!selectedType || !selectedType.fields_schema) return null;

    return Object.entries(selectedType.fields_schema).map(([fieldName, fieldType]) => (
      <div key={fieldName}>
        <label className="block text-sm font-medium mb-1 text-gray-700 capitalize">
          {fieldName.replace(/_/g, ' ')}
        </label>
        <input
          type="text"
          value={formData.specifications[fieldName] || ''}
          onChange={(e) => setFormData({
            ...formData,
            specifications: {
              ...formData.specifications,
              [fieldName]: e.target.value
            }
          })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
        />
      </div>
    ));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        asset_type_id: formData.asset_type_id || undefined,
        site_id: formData.site_id || undefined,
        person_id: formData.person_id || undefined,
        purchase_date: formData.purchase_date || undefined,
        warranty_expiry: formData.warranty_expiry || undefined,
        supplier_id: formData.supplier_id || undefined
      };

      if (editingAsset) {
        await api.put(`/assets/${editingAsset.id}`, submitData);
      } else {
        await api.post('/assets', submitData);
      }
      setShowModal(false);
      resetForm();
      fetchAssets();
    } catch (error: unknown) {
      console.error('Errore salvataggio asset:', error);
      alert(getApiError(error, 'Errore nel salvataggio dell\'asset'));
    }
  };

  const handleEdit = (asset: Asset) => {
    setEditingAsset(asset);
    setFormData({
      asset_code: asset.asset_code || '',
      serial_number: asset.serial_number,
      mac_address: asset.mac_address || '',
      asset_type_id: asset.asset_type_id,
      manufacturer: asset.manufacturer,
      model: asset.model,
      site_id: asset.site_id,
      person_id: asset.person_id,
      supplier_id: (asset as Asset & { supplier_id?: number | null }).supplier_id ?? null,
      status: asset.status,
      purchase_date: asset.purchase_date || '',
      warranty_expiry: asset.warranty_expiry || '',
      specifications: asset.specifications || {},
      notes: asset.notes || '',
      is_active: asset.is_active
    });
    setShowModal(true);
  };

  const handleDeactivate = async (id: number) => {
    if (!confirm('Disattivare questo asset?')) return;
    try {
      await api.delete(`/assets/${id}`);
      fetchAssets();
    } catch (error) {
      console.error('Errore disattivazione asset:', error);
      alert('Errore nella disattivazione dell\'asset');
    }
  };

  const handleReactivate = async (id: number) => {
    try {
      await api.put(`/assets/${id}`, { is_active: true });
      fetchAssets();
    } catch (error) {
      console.error('Errore riattivazione asset:', error);
      alert('Errore nella riattivazione dell\'asset');
    }
  };

  const handleHardDelete = async (id: number) => {
    if (!confirm('⚠️ ATTENZIONE: Questa operazione è IRREVERSIBILE.\n\nEliminare definitivamente questo asset dal database?')) return;
    try {
      await api.delete(`/assets/${id}/hard`);
      fetchAssets();
    } catch (error) {
      console.error('Errore eliminazione asset:', error);
      alert('Errore nell\'eliminazione definitiva dell\'asset');
    }
  };

  // NUOVE FUNZIONI PER RITIRO MANUTENZIONE
  const handleWithdrawForMaintenance = (asset: Asset) => {
    if (!asset.person_id) {
      alert('Asset non assegnato');
      return;
    }
    setMaintenanceAsset(asset);
    setMaintenanceReason('');
    setMaintenanceNotes('');
    setShowMaintenanceModal(true);
  };

  const executeWithdrawForMaintenance = async () => {
    if (!maintenanceAsset) return;
    
    setIsSubmittingMaintenance(true);
    try {
      const params = new URLSearchParams();
      if (maintenanceReason) params.append('reason', maintenanceReason);
      if (maintenanceNotes) params.append('notes', maintenanceNotes);
      
      const response = await api.post(
        `/assets/${maintenanceAsset.id}/withdraw-for-maintenance?${params}`
      );
      
      alert(response.data.message || 'Asset ritirato per manutenzione con successo');
      setShowMaintenanceModal(false);
      setMaintenanceAsset(null);
      fetchAssets();
    } catch (error: unknown) {
      console.error('Errore ritiro asset:', error);
      alert(getApiError(error, 'Errore durante il ritiro dell\'asset'));
    } finally {
      setIsSubmittingMaintenance(false);
    }
  };

  const resetForm = () => {
    setFormData({
      asset_code: '',
      serial_number: '',
      mac_address: '',
      asset_type_id: null,
      manufacturer: '',
      model: '',
      site_id: null,
      person_id: null,
      supplier_id: null,
      status: 'disponibile',
      purchase_date: '',
      warranty_expiry: '',
      specifications: {},
      notes: '',
      is_active: true
    });
    setEditingAsset(null);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  // Calcolo statistiche per status
  const totalAssets = assets.length;
  const available = assets.filter(a => a.status === 'disponibile').length;
  const assigned = assets.filter(a => a.status === 'assegnato').length;
  const maintenance = assets.filter(a => a.status === 'manutenzione').length;
  const dismissed = assets.filter(a => a.status === 'dismesso' || a.status === 'dismissione').length;
  const availablePercent = totalAssets > 0 ? Math.round((available/totalAssets)*100) : 0;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        {/* HEADER MODERNO */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
              <CubeIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Gestione Asset</h1>
              <p className="text-sm text-gray-600 mt-1">Gestisci i dispositivi IT aziendali e le loro assegnazioni</p>
            </div>
          </div>
          <div className="flex justify-end">
            {!isUser && (
              <Button
                variant="primary"
                icon="➕"
                onClick={() => setShowModal(true)}
              >
                Nuovo Asset
              </Button>
            )}
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatsCard
            title="Totale Asset"
            value={totalAssets}
            subtitle="Dispositivi tracciati"
            icon={CubeIcon}
            gradient="blue"
          />

          <StatsCard
            title="Disponibili"
            value={available}
            subtitle={`${availablePercent}% del totale`}
            icon={CheckCircleIcon}
            gradient="green"
          />

          <StatsCard
            title="Assegnati"
            value={assigned}
            subtitle="In uso"
            icon={CubeIcon}
            gradient="purple"
          />

          <StatsCard
            title="Manutenzione"
            value={maintenance}
            icon={WrenchScrewdriverIcon}
            gradient="orange"
            badge={maintenance > 0 ? {
              text: 'In lavorazione',
              variant: 'warning'
            } : undefined}
          />

          <StatsCard
            title="Dismessi"
            value={dismissed}
            icon={ArchiveBoxXMarkIcon}
            gradient="red"
          />
        </div>

        {/* Filtri */}
        <div className="mb-4 space-y-3">
          <input
            type="text"
            placeholder="Cerca per codice, seriale, marca, modello o MAC..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
          />
          <div className="flex gap-4 items-center flex-wrap">
            <select
              value={filterAssetTypeId || ''}
              onChange={(e) => setFilterAssetTypeId(e.target.value ? parseInt(e.target.value) : null)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
            >
              <option value="">Tutti i tipi</option>
              {flatAssetTypes.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
            <select
              value={filterSiteId || ''}
              onChange={(e) => setFilterSiteId(e.target.value ? parseInt(e.target.value) : null)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
            >
              <option value="">Tutte le sedi</option>
              {sites.map(site => (
                <option key={site.id} value={site.id}>{site.name}</option>
              ))}
            </select>
            <select
              value={filterPersonId || ''}
              onChange={(e) => setFilterPersonId(e.target.value ? parseInt(e.target.value) : null)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
            >
              <option value="">Tutte le persone</option>
              {people.map(person => (
                <option key={person.id} value={person.id}>
                  {person.first_name} {person.last_name}
                </option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
            >
              <option value="">Tutti gli stati</option>
              {STATUS_OPTIONS.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="w-4 h-4 text-asset-manager-yellow rounded focus:ring-2 focus:ring-asset-manager-yellow"
              />
              Mostra inattivi
            </label>
          </div>
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
                    <th className="px-6 py-3 text-left">Codice</th>
                    <th className="px-6 py-3 text-left">Tipo</th>
                    <th className="px-6 py-3 text-left">Marca/Modello</th>
                    <th className="px-6 py-3 text-left">Seriale</th>
                    <th className="px-6 py-3 text-left">Sede</th>
                    <th className="px-6 py-3 text-left">Persona</th>
                    <th className="px-6 py-3 text-left">Stato</th>
                    <th className="px-6 py-3 text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((asset) => (
                    <tr key={asset.id} className="border-t hover:bg-yellow-50 transition-colors">
                      <td className="px-6 py-4 font-mono text-sm">{asset.asset_code || '-'}</td>
                      <td className="px-6 py-4">{asset.asset_type_name}</td>
                      <td className="px-6 py-4">
                        <div className="font-medium">{asset.manufacturer}</div>
                        <div className="text-sm text-gray-600">{asset.model}</div>
                      </td>
                      <td className="px-6 py-4 font-mono text-sm">{asset.serial_number}</td>
                      <td className="px-6 py-4">{asset.site_name || '-'}</td>
                      <td className="px-6 py-4">
                        {asset.person_name
                          ? asset.person_name
                          : asset.location_name
                            ? `📍 ${asset.location_name}`
                            : '—'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                          asset.status === 'disponibile' ? 'bg-green-50 text-green-700 border-green-200' :
                          asset.status === 'assegnato' ? 'bg-asset-manager-yellow bg-opacity-20 text-asset-manager-gray border-asset-manager-yellow' :
                          asset.status === 'manutenzione' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                          'bg-gray-50 text-gray-700 border-gray-200'
                        }`}>
                          {asset.status}
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
                              title="Modifica asset"
                              onClick={() => handleEdit(asset)}
                            />
                            
                            {asset.is_active ? (
                              <>
                                {/* 2. Disattiva - SECONDARY */}
                                <Button
                                  variant="secondary"
                                  icon="⏸️"
                                  iconOnly
                                  title="Disattiva asset"
                                  onClick={() => handleDeactivate(asset.id)}
                                />
                              </>
                            ) : (
                              <>
                                {/* 2. Riattiva - SECONDARY */}
                                <Button
                                  variant="secondary"
                                  icon="▶️"
                                  iconOnly
                                  title="Riattiva asset"
                                  onClick={() => handleReactivate(asset.id)}
                                />
                                {/* 3. Elimina - DESTRUCTIVE (sempre rosso) */}
                                <Button
                                  variant="destructive"
                                  icon="🗑️"
                                  iconOnly
                                  title="Elimina definitivamente"
                                  onClick={() => handleHardDelete(asset.id)}
                                />
                              </>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {assets.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                        Nessun asset trovato
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
            <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">
                {editingAsset ? 'Modifica Asset' : 'Nuovo Asset'}
              </h2>
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  {/* Tipo Asset */}
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Tipo Asset *</label>
                    <select
                      required
                      value={formData.asset_type_id || ''}
                      onChange={(e) => setFormData({...formData, asset_type_id: parseInt(e.target.value), specifications: {}})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    >
                      <option value="">Seleziona tipo...</option>
                      {flatAssetTypes.map(type => (
                        <option key={type.id} value={type.id}>{type.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Campi base */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Marca *</label>
                      <input
                        type="text"
                        required
                        value={formData.manufacturer}
                        onChange={(e) => setFormData({...formData, manufacturer: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Modello *</label>
                      <input
                        type="text"
                        required
                        value={formData.model}
                        onChange={(e) => setFormData({...formData, model: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Numero Seriale *</label>
                      <input
                        type="text"
                        required
                        value={formData.serial_number}
                        onChange={(e) => setFormData({...formData, serial_number: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Codice Asset</label>
                      <input
                        type="text"
                        value={formData.asset_code}
                        onChange={(e) => setFormData({...formData, asset_code: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">MAC Address</label>
                    <input
                      type="text"
                      value={formData.mac_address}
                      onChange={(e) => setFormData({...formData, mac_address: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    />
                  </div>

                  {/* Sede */}
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Sede</label>
                    <select
                      value={formData.site_id || ''}
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

                  {/* Fornitore */}
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Fornitore</label>
                    <select
                      value={formData.supplier_id || ''}
                      onChange={(e) => setFormData({...formData, supplier_id: e.target.value ? parseInt(e.target.value) : null})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    >
                      <option value="">Nessun fornitore</option>
                      {suppliers.map(supplier => (
                        <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Stato e Date */}
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Stato *</label>
                      <select
                        required
                        value={formData.status}
                        onChange={(e) => setFormData({...formData, status: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      >
                        {STATUS_OPTIONS.map(status => (
                          <option key={status} value={status}>{status}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Data Acquisto</label>
                      <input
                        type="date"
                        value={formData.purchase_date}
                        onChange={(e) => setFormData({...formData, purchase_date: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Scadenza Garanzia</label>
                      <input
                        type="date"
                        value={formData.warranty_expiry}
                        onChange={(e) => setFormData({...formData, warranty_expiry: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Campi dinamici */}
                  {formData.asset_type_id && (
                    <div className="border-t pt-4">
                      <h3 className="text-lg font-semibold mb-3 text-gray-800">Specifiche Tecniche</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {renderDynamicFields()}
                      </div>
                    </div>
                  )}

                  {/* Note */}
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
                      className="mr-2 w-4 h-4 text-asset-manager-gray rounded focus:ring-2 focus:ring-asset-manager-yellow"
                    />
                    <label className="text-sm font-medium text-gray-700">Asset attivo</label>
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
                    {editingAsset ? 'Salva Modifiche' : 'Crea Asset'}
                  </Button>
                  {editingAsset?.person_id && (
                    <Button
                      variant="primary"
                      type="button"
                      icon="🔧"
                      onClick={() => {
                        setShowModal(false);
                        handleWithdrawForMaintenance(editingAsset);
                      }}
                      className="bg-orange-500 hover:bg-orange-600 text-white"
                    >
                      Ritira per Manutenzione
                    </Button>
                  )}
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL CONFERMA RITIRO PER MANUTENZIONE */}
        {showMaintenanceModal && maintenanceAsset && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4 text-gray-800">
                🔧 Ritira Asset per Manutenzione
              </h2>
              
              <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-sm font-semibold text-gray-700 mb-2">Asset:</p>
                <p className="text-gray-800">
                  {maintenanceAsset.asset_code || 'N/A'} - {maintenanceAsset.manufacturer} {maintenanceAsset.model}
                </p>
                <p className="text-sm text-gray-600 mt-1">S/N: {maintenanceAsset.serial_number}</p>
                
                {maintenanceAsset.person_name && (
                  <div className="mt-3">
                    <p className="text-sm font-semibold text-gray-700">Assegnato a:</p>
                    <p className="text-gray-800">{maintenanceAsset.person_name}</p>
                  </div>
                )}
              </div>
              
              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm font-semibold text-blue-800 mb-1">Operazioni che verranno eseguite:</p>
                <ul className="text-sm text-blue-700 list-disc list-inside space-y-1">
                  <li>Registrazione restituzione asset (data odierna)</li>
                  <li>Cambio stato asset → "Manutenzione"</li>
                  <li>Rimozione assegnazione corrente</li>
                  <li>Creazione log audit</li>
                </ul>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Motivo manutenzione (opzionale)
                </label>
                <input
                  type="text"
                  value={maintenanceReason}
                  onChange={(e) => setMaintenanceReason(e.target.value)}
                  placeholder="es: Schermo rotto, Batteria da sostituire..."
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Note aggiuntive (opzionale)
                </label>
                <textarea
                  value={maintenanceNotes}
                  onChange={(e) => setMaintenanceNotes(e.target.value)}
                  placeholder="Eventuali dettagli aggiuntivi..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
              
              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowMaintenanceModal(false);
                    setMaintenanceAsset(null);
                  }}
                  disabled={isSubmittingMaintenance}
                >
                  Annulla
                </Button>
                <Button
                  variant="primary"
                  onClick={executeWithdrawForMaintenance}
                  disabled={isSubmittingMaintenance}
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {isSubmittingMaintenance ? '⏳ Elaborazione...' : '✅ Conferma Ritiro'}
                </Button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
