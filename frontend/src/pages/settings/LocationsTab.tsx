import { useState, useEffect } from 'react';
import api, { getApiError } from '../../api';
import Button from '../../components/Button';

interface Location {
  id: number;
  name: string;
  location_type_id: number;
  location_type_name: string | null;
  location_type_icon: string | null;
  site_id: number;
  site_name: string | null;
  floor: string | null;
  room_number: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface Site {
  id: number;
  name: string;
  is_active: boolean;
}

interface LocationType {
  id: number;
  name: string;
  icon: string | null;
  is_active: boolean;
}

interface SiteWithLocations extends Site {
  children: Location[];
}

interface LocationsTabProps {
  currentUserRole: string;
}

export default function LocationsTab({ currentUserRole }: LocationsTabProps) {
  const [locations, setLocations] = useState<Location[]>([]);
  const [locationsBySite, setLocationsBySite] = useState<SiteWithLocations[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [locationTypes, setLocationTypes] = useState<LocationType[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'hierarchy' | 'table'>('hierarchy');
  const [showModal, setShowModal] = useState(false);
  const [editingLocation, setEditingLocation] = useState<Location | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    site_id: 0 as number,
    floor: '',
    room_number: '',
    notes: '',
    is_active: true,
  });

  const canEdit = currentUserRole === 'admin' || currentUserRole === 'operatore';

  useEffect(() => {
    fetchData();
  }, [viewMode]);

  const fetchData = async () => {
    try {
      setLoading(true);
      if (viewMode === 'hierarchy') {
        const [sitesRes, locationsRes, typesRes] = await Promise.all([
          api.get('/sites', { params: { limit: 1000, is_active: true } }),
          api.get('/locations', { params: { limit: 1000 } }),
          api.get('/location-types', { params: { limit: 1000, is_active: true } }),
        ]);
        const sitesData = sitesRes.data.items || [];
        const locationsData = locationsRes.data.items || [];
        const typesData = typesRes.data.items || [];
        setSites(sitesData);
        setLocations(locationsData);
        setLocationTypes(typesData);
        setLocationsBySite(
          sitesData.map((s: Site) => ({
            ...s,
            children: locationsData.filter((l: Location) => l.site_id === s.id),
          }))
        );
      } else {
        const [locationsRes, sitesRes, typesRes] = await Promise.all([
          api.get('/locations', { params: { limit: 1000 } }),
          api.get('/sites', { params: { limit: 1000, is_active: true } }),
          api.get('/location-types', { params: { limit: 1000, is_active: true } }),
        ]);
        setLocations(locationsRes.data.items || []);
        setSites(sitesRes.data.items || []);
        setLocationTypes(typesRes.data.items || []);
      }
    } catch (error) {
      console.error('Errore caricamento locazioni:', error);
      alert('Errore nel caricamento delle locazioni');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (loc?: Location) => {
    if (loc) {
      setEditingLocation(loc);
      setFormData({
        name: loc.name,
        site_id: loc.site_id,
        floor: loc.floor || '',
        room_number: loc.room_number || '',
        notes: loc.notes || '',
        is_active: loc.is_active ?? true,
      });
    } else {
      setEditingLocation(null);
      setFormData({
        name: '',
        site_id: 0,
        floor: '',
        room_number: '',
        notes: '',
        is_active: true,
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingLocation(null);
    setFormData({
      name: '',
      site_id: 0,
      floor: '',
      room_number: '',
      notes: '',
      is_active: true,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!canEdit) {
      alert('Non hai i permessi per questa operazione');
      return;
    }

    if (!formData.site_id) {
      alert('Seleziona sede');
      return;
    }

    try {
      const submitData = {
        name: formData.name,
        site_id: formData.site_id,
        floor: formData.floor || null,
        room_number: formData.room_number || null,
        notes: formData.notes || null,
        is_active: formData.is_active,
      };

      if (editingLocation) {
        await api.put(`/locations/${editingLocation.id}`, submitData);
        alert('✅ Stanza aggiornata con successo!');
      } else {
        await api.post('/locations', submitData);
        alert('✅ Stanza creata con successo!');
      }

      handleCloseModal();
      fetchData();
    } catch (error: unknown) {
      alert(getApiError(error, 'Errore nel salvataggio della stanza'));
    }
  };

  const handleToggleActive = async (loc: Location) => {
    if (!canEdit) {
      alert('Non hai i permessi per questa operazione');
      return;
    }

    const action = loc.is_active ? 'disattivare' : 'attivare';
    if (!confirm(`Confermi di voler ${action} la stanza "${loc.name}"?`)) {
      return;
    }

    try {
      await api.put(`/locations/${loc.id}`, {
        name: loc.name,
        location_type_id: loc.location_type_id,
        site_id: loc.site_id,
        floor: loc.floor,
        room_number: loc.room_number,
        notes: loc.notes,
        is_active: !loc.is_active,
      });
      alert(`✅ Stanza ${loc.is_active ? 'disattivata' : 'attivata'} con successo!`);
      fetchData();
    } catch (error: unknown) {
      alert(getApiError(error, "Errore nell'operazione"));
    }
  };

  const renderHierarchy = (sitesWithLocs: SiteWithLocations[]) => {
    return sitesWithLocs.map((site) => (
      <div key={site.id} style={{ marginLeft: '0px' }}>
        <div className="flex items-center py-2 hover:bg-gray-50 rounded px-2">
          <span className="mr-2">📍</span>
          <span className="font-medium text-gray-900">{site.name}</span>
          <span className="ml-2 text-xs text-gray-400">
            ({site.children?.length || 0} stanze)
          </span>
        </div>
        {site.children &&
          site.children.length > 0 &&
          site.children.map((loc) => (
            <div key={loc.id} style={{ marginLeft: '24px' }}>
              <div className="flex items-center py-2 hover:bg-gray-50 rounded px-2">
                <span className="mr-2">{loc.location_type_icon || '📋'}</span>
                <span className="font-medium text-gray-900">{loc.name}</span>
                {loc.location_type_name && (
                  <span className="ml-2 text-sm text-gray-500">- {loc.location_type_name}</span>
                )}
                {(loc.floor || loc.room_number) && (
                  <span className="ml-2 text-xs text-gray-400">
                    {[
                      loc.floor,
                      loc.room_number ? `Stanza ${loc.room_number}` : null,
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </span>
                )}
                {canEdit && (
                  <div className="ml-auto flex gap-2">
                    <Button
                      variant="secondary"
                      icon="✏️"
                      iconOnly
                      title="Modifica stanza"
                      onClick={() => handleOpenModal(loc)}
                    />
                    <Button
                      variant={loc.is_active ? 'destructive' : 'primary'}
                      icon={loc.is_active ? '🚫' : '✓'}
                      iconOnly
                      title={loc.is_active ? 'Disattiva stanza' : 'Attiva stanza'}
                      onClick={() => handleToggleActive(loc)}
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
      </div>
    ));
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Caricamento...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('hierarchy')}
              className={`px-4 py-2 rounded transition-colors ${
                viewMode === 'hierarchy'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              🌲 Gerarchia
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 rounded transition-colors ${
                viewMode === 'table'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📋 Tabella
            </button>
          </div>
          {canEdit && (
            <Button onClick={() => handleOpenModal()}>➕ Nuova Stanza</Button>
          )}
        </div>
      </div>

      {viewMode === 'hierarchy' && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="space-y-2">
            {locationsBySite.length === 0 ? (
              <p className="text-center text-gray-500 py-8">Nessuna sede presente</p>
            ) : (
              renderHierarchy(locationsBySite)
            )}
          </div>
        </div>
      )}

      {viewMode === 'table' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nome</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sede</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Piano</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stanza</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Creato</th>
                {canEdit && (
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Azioni</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {locations.map((loc) => (
                <tr key={loc.id} className={!loc.is_active ? 'opacity-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{loc.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{loc.site_name || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {loc.location_type_icon || ''} {loc.location_type_name || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{loc.floor || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{loc.room_number || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        loc.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {loc.is_active ? '✓ Attivo' : '✗ Disattivato'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {loc.created_at ? new Date(loc.created_at).toLocaleDateString('it-IT') : '-'}
                  </td>
                  {canEdit && (
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="secondary"
                          icon="✏️"
                          iconOnly
                          title="Modifica stanza"
                          onClick={() => handleOpenModal(loc)}
                        />
                        <Button
                          variant={loc.is_active ? 'destructive' : 'primary'}
                          icon={loc.is_active ? '🚫' : '✓'}
                          iconOnly
                          title={loc.is_active ? 'Disattiva stanza' : 'Attiva stanza'}
                          onClick={() => handleToggleActive(loc)}
                        />
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingLocation ? '✏️ Modifica Stanza' : '➕ Nuova Stanza'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  maxLength={100}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="es. Sala Consiglio, Rack A"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sede *</label>
                <select
                  value={formData.site_id || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      site_id: e.target.value ? Number(e.target.value) : 0,
                    })
                  }
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Seleziona sede</option>
                  {sites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Piano</label>
                <input
                  type="text"
                  value={formData.floor}
                  onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                  maxLength={20}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="es. Piano 1, PT, Piano -1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stanza</label>
                <input
                  type="text"
                  value={formData.room_number}
                  onChange={(e) => setFormData({ ...formData, room_number: e.target.value })}
                  maxLength={20}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="es. 101, Server-01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Note opzionali..."
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">
                  Attivo
                </label>
              </div>

              <div className="flex gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={handleCloseModal} className="flex-1">
                  Annulla
                </Button>
                <Button type="submit" variant="primary" className="flex-1">
                  {editingLocation ? 'Aggiorna' : 'Crea'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
