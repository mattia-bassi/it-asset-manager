import { useState, useEffect } from 'react';
import api, { getApiError } from '../../api';
import Button from '../../components/Button';
import { auth } from '../../auth';
import type { AssetType } from '../../types';

// Interfacce per AssetTypesContent
interface AssetTypeHierarchy {
  id: number;
  name: string;
  description: string | null;
  level: number;
  children: AssetTypeHierarchy[];
}

// Componente ParentSelect per AssetTypesContent
function ParentSelect({ value, onChange, excludeId }: { 
  value: number | null; 
  onChange: (value: number | null) => void;
  excludeId?: number;
}) {
  const [types, setTypes] = useState<AssetType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTypes();
  }, []);

  const fetchTypes = async () => {
    try {
      setLoading(true);
      const response = await api.get('/asset-types?limit=1000&is_active=true');
      const allTypes = response.data.items;
      const filtered = excludeId 
        ? allTypes.filter((t: AssetType) => t.id !== excludeId)
        : allTypes;
      setTypes(filtered);
    } catch (error) {
      console.error('Errore caricamento tipologie:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <select disabled className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100">
        <option>Caricamento...</option>
      </select>
    );
  }

  const level1 = types.filter(t => !t.parent_id);
  const level2 = types.filter(t => t.parent_id && !types.find(p => p.id === t.parent_id)?.parent_id);

  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
    >
      <option value="">Nessun padre (Livello 1)</option>
      <optgroup label="Livello 1 - Categorie Principali">
        {level1.map(type => (
          <option key={type.id} value={type.id}>
            📁 {type.name}
          </option>
        ))}
      </optgroup>
      <optgroup label="Livello 2 - Sottocategorie">
        {level2.map(type => (
          <option key={type.id} value={type.id}>
            📂 {type.name} ({type.parent_name})
          </option>
        ))}
      </optgroup>
    </select>
  );
}

export default function AssetTypesTab() {
  const [assetTypes, setAssetTypes] = useState<AssetType[]>([]);
  const [hierarchy, setHierarchy] = useState<AssetTypeHierarchy[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'hierarchy' | 'table'>('hierarchy');
  const [showModal, setShowModal] = useState(false);
  const [editingType, setEditingType] = useState<AssetType | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    parent_id: null as number | null,
    description: '',
    is_active: true
  });

  const currentUser = auth.getUser();
  const canEdit = currentUser?.role === 'admin' || currentUser?.role === 'operatore';

  useEffect(() => {
    fetchData();
  }, [viewMode]);

  const fetchData = async () => {
    try {
      setLoading(true);
      if (viewMode === 'hierarchy') {
        const response = await api.get('/asset-types/hierarchy');
        setHierarchy(response.data);
      } else {
        const response = await api.get('/asset-types?limit=1000');
        setAssetTypes(response.data.items);
      }
    } catch (error) {
      console.error('Errore caricamento tipologie:', error);
      alert('Errore nel caricamento delle tipologie');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = async (type?: AssetType) => {
    if (type) {
      setEditingType(type);
      setFormData({
        name: type.name,
        parent_id: type.parent_id,
        description: type.description || '',
        is_active: type.is_active ?? true
      });
    } else {
      setEditingType(null);
      setFormData({
        name: '',
        parent_id: null,
        description: '',
        is_active: true
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingType(null);
    setFormData({
      name: '',
      parent_id: null,
      description: '',
      is_active: true
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!canEdit) {
      alert('Non hai i permessi per questa operazione');
      return;
    }

    try {
      const submitData = {
        name: formData.name,
        parent_id: formData.parent_id,
        description: formData.description || null,
        is_active: formData.is_active
      };

      if (editingType) {
        await api.put(`/asset-types/${editingType.id}`, submitData);
        alert('✅ Tipologia aggiornata con successo!');
      } else {
        await api.post('/asset-types', submitData);
        alert('✅ Tipologia creata con successo!');
      }
      
      handleCloseModal();
      fetchData();
    } catch (error: unknown) {
      console.error('Errore salvataggio tipologia:', error);
      alert(getApiError(error, 'Errore nel salvataggio della tipologia'));
    }
  };

  const handleToggleActive = async (type: AssetType) => {
    if (!canEdit) {
      alert('Non hai i permessi per questa operazione');
      return;
    }

    const action = type.is_active ? 'disattivare' : 'attivare';
    if (!confirm(`Confermi di voler ${action} la tipologia "${type.name}"?`)) {
      return;
    }
    
    try {
      await api.put(`/asset-types/${type.id}`, {
        name: type.name,
        parent_id: type.parent_id,
        description: type.description,
        is_active: !type.is_active
      });
      alert(`✅ Tipologia ${type.is_active ? 'disattivata' : 'attivata'} con successo!`);
      fetchData();
    } catch (error: unknown) {
      console.error('Errore toggle attivo:', error);
      alert(getApiError(error, 'Errore nell\'operazione'));
    }
  };

  const renderHierarchy = (nodes: AssetTypeHierarchy[], depth: number = 0) => {
    return nodes.map((node) => (
      <div key={node.id} style={{ marginLeft: `${depth * 24}px` }}>
        <div className="flex items-center py-2 hover:bg-gray-50 rounded px-2">
          <span className="mr-2">
            {depth === 0 ? '📁' : depth === 1 ? '📂' : '📄'}
          </span>
          <span className="font-medium text-gray-900">{node.name}</span>
          {node.description && (
            <span className="ml-2 text-sm text-gray-500">- {node.description}</span>
          )}
          <span className="ml-2 text-xs text-gray-400">
            (Livello {node.level})
          </span>
        </div>
        {node.children && node.children.length > 0 && renderHierarchy(node.children, depth + 1)}
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
            <Button onClick={() => handleOpenModal()}>
              ➕ Nuova Tipologia
            </Button>
          )}
        </div>
      </div>

      {viewMode === 'hierarchy' && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="space-y-2">
            {hierarchy.length === 0 ? (
              <p className="text-center text-gray-500 py-8">Nessuna tipologia presente</p>
            ) : (
              renderHierarchy(hierarchy)
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Padre</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descrizione</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stato</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Creato</th>
                {canEdit && (
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Azioni</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {assetTypes.map((type) => (
                <tr key={type.id} className={!type.is_active ? 'opacity-50' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{type.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{type.parent_name || '-'}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500">{type.description || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      type.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {type.is_active ? '✓ Attivo' : '✗ Disattivato'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {type.created_at ? new Date(type.created_at).toLocaleDateString('it-IT') : '-'}
                  </td>
                  {canEdit && (
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="secondary"
                          icon="✏️"
                          iconOnly
                          title="Modifica tipologia"
                          onClick={() => handleOpenModal(type)}
                        />
                        <Button
                          variant={type.is_active ? "destructive" : "primary"}
                          icon={type.is_active ? "🚫" : "✓"}
                          iconOnly
                          title={type.is_active ? "Disattiva tipologia" : "Attiva tipologia"}
                          onClick={() => handleToggleActive(type)}
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
              {editingType ? '✏️ Modifica Tipologia' : '➕ Nuova Tipologia'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Tipologia *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  maxLength={100}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="es. Laptop, Server, Router..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipologia Padre (opzionale)
                </label>
                <ParentSelect
                  value={formData.parent_id}
                  onChange={(value) => setFormData({...formData, parent_id: value})}
                  excludeId={editingType?.id}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Lascia vuoto per creare una categoria principale (Livello 1)
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrizione
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Descrizione opzionale..."
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="mr-2"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">
                  Tipologia attiva
                </label>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={handleCloseModal} className="flex-1">
                  Annulla
                </Button>
                <Button type="submit" variant="primary" className="flex-1">
                  {editingType ? 'Aggiorna' : 'Crea'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
