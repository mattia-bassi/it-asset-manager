import { useState, useEffect, useRef, useMemo } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import StatsCard from '../components/common/StatsCard';
import { ClipboardDocumentListIcon, PlusCircleIcon, ArrowPathIcon, ArrowUturnLeftIcon } from '@heroicons/react/24/outline';
import { auth } from '../auth';
import type { Person, Asset, InventorySku, Sim, Badge, AssignmentItem, Assignment } from '../types';

interface AssignmentItemCreate {
  item_type: 'asset' | 'inventory' | 'sim' | 'badge';
  asset_id?: number;
  inventory_sku_id?: number;
  sim_id?: number;
  badge_id?: number;
  quantity: number;
  notes?: string;
}

// Componente per selezionare materiali da ritirare
function MaterialReturnSelector({ 
  personId, 
  returnedItems, 
  setReturnedItems 
}: {
  personId: number | null;
  returnedItems: any[];
  setReturnedItems: (items: any[]) => void;
}) {
  const [assignedAssets, setAssignedAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [returnTab, setReturnTab] = useState('asset');

  useEffect(() => {
    if (personId) {
      fetchAssignedMaterials();
    } else {
      setAssignedAssets([]);
    }
  }, [personId]);

  const fetchAssignedMaterials = async () => {
    if (!personId) return;
    
    try {
      setLoading(true);
      // Recupera assegnazioni attive per questa persona
      const response = await api.get(`/assignments?person_id=${personId}&active_only=true&limit=1000`);
      
      // Estrai tutti i materiali dalle assegnazioni attive
      // IMPORTANTE: Filtra solo items con is_returned=false (attualmente assegnati)
      const materials: any[] = [];
      response.data.items.forEach((assignment: any) => {
        assignment.items?.forEach((item: any) => {
          // Includi solo items NON restituiti
          if (!item.is_returned) {
          materials.push({
            ...item,
            assignment_id: assignment.id,
            assignment_number: assignment.assignment_number
          });
          }
        });
      });
      
      // Per ogni asset, recupera i dettagli completi
      const materialsWithDetails = await Promise.all(
        materials.map(async (material) => {
          if (material.item_type === 'asset' && material.asset_id) {
            try {
              const assetResponse = await api.get(`/assets/${material.asset_id}`);
              return {
                ...material,
                asset_details: assetResponse.data
              };
            } catch (error) {
              console.error(`Errore recupero dettagli asset ${material.asset_id}:`, error);
              return material;
            }
          }
          return material;
        })
      );
      
      setAssignedAssets(materialsWithDetails);
    } catch (error) {
      console.error('Errore caricamento materiali assegnati:', error);
      alert('Errore nel caricamento dei materiali assegnati');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleMaterial = (material: any) => {
    const exists = returnedItems.find(
      item => 
        item.item_type === material.item_type &&
        (material.asset_id ? item.asset_id === material.asset_id : 
         material.inventory_sku_id ? item.inventory_sku_id === material.inventory_sku_id :
         material.badge_id ? item.badge_id === material.badge_id :
         item.sim_id === material.sim_id)
    );

    if (exists) {
      setReturnedItems(returnedItems.filter(item => item !== exists));
    } else {
      setReturnedItems([...returnedItems, {
        item_type: material.item_type,
        asset_id: material.asset_id,
        inventory_sku_id: material.inventory_sku_id,
        sim_id: material.sim_id,
        badge_id: material.badge_id,
        quantity: material.quantity,
        notes: `Ritirato da assegnazione ${material.assignment_number}`
      }]);
    }
  };

  if (loading) {
    return <div className="text-center py-4">Caricamento materiali assegnati...</div>;
  }

  if (!personId) {
    return <div className="text-center py-4 text-gray-500">Seleziona prima una persona</div>;
  }

  if (assignedAssets.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        Nessun materiale attualmente assegnato a questa persona
      </div>
    );
  }

  const assetItems = assignedAssets.filter(m => m.item_type === 'asset');
  const inventoryItems = assignedAssets.filter(m => m.item_type === 'inventory');
  const simItems = assignedAssets.filter(m => m.item_type === 'sim');
  const badgeItems = assignedAssets.filter(m => m.item_type === 'badge');

  return (
    <div>
      {/* TAB NAVIGATION */}
      <div className="flex border-b border-gray-300 mb-3">
        <button
          onClick={() => setReturnTab('asset')}
          className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
            returnTab === 'asset'
              ? 'bg-orange-400 text-white border-b-4 border-orange-500'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          🖥️ Asset {assetItems.length > 0 && `(${assetItems.length})`}
        </button>
        <button
          onClick={() => setReturnTab('materiali')}
          className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
            returnTab === 'materiali'
              ? 'bg-orange-400 text-white border-b-4 border-orange-500'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          📦 Materiali {inventoryItems.length > 0 && `(${inventoryItems.length})`}
        </button>
        <button
          onClick={() => setReturnTab('sim')}
          className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
            returnTab === 'sim'
              ? 'bg-orange-400 text-white border-b-4 border-orange-500'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          📱 SIM {simItems.length > 0 && `(${simItems.length})`}
        </button>
        <button
          onClick={() => setReturnTab('badge')}
          className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
            returnTab === 'badge'
              ? 'bg-orange-400 text-white border-b-4 border-orange-500'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          🪪 Badge {badgeItems.length > 0 && `(${badgeItems.length})`}
        </button>
      </div>

      {/* TAB ASSET */}
      {returnTab === 'asset' && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {assetItems.length === 0 ? (
            <p className="text-gray-500 italic p-4 text-sm">Nessun asset assegnato</p>
          ) : (
            <>
              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                <table className="w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-100 sticky top-0 z-10">
                    <tr>
                      <th className="px-2 py-2 text-left w-10">
                  <input
                    type="checkbox"
                    checked={assetItems.length > 0 && assetItems.every(m => 
                      returnedItems.some(item => item.item_type === 'asset' && item.asset_id === m.asset_id)
                    )}
                    onChange={(e) => {
                      if (e.target.checked) {
                        const newItems = assetItems
                          .filter(m => !returnedItems.some(item => item.item_type === 'asset' && item.asset_id === m.asset_id))
                          .map(m => ({
                            item_type: 'asset' as const,
                            asset_id: m.asset_id,
                            quantity: m.quantity,
                            notes: `Ritirato da assegnazione ${m.assignment_number}`
                          }));
                        setReturnedItems([...returnedItems, ...newItems]);
                      } else {
                        setReturnedItems(returnedItems.filter(item => 
                          !(item.item_type === 'asset' && assetItems.some(m => m.asset_id === item.asset_id))
                        ));
                      }
                    }}
                    className="w-4 h-4"
                  />
                </th>
                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Tipo</th>
                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Marca/Modello</th>
                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Seriale</th>
                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-20">Stato</th>
              </tr>
            </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
              {assetItems.map((material, index) => {
                const isSelected = returnedItems.some(
                  item => item.item_type === 'asset' && item.asset_id === material.asset_id
                );
                const assetDetails = material.asset_details;
                return (
                  <tr 
                    key={index}
                          className={`hover:bg-gray-50 cursor-pointer transition-colors ${isSelected ? 'bg-orange-50' : ''}`}
                    onClick={() => handleToggleMaterial(material)}
                  >
                          <td className="px-2 py-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleToggleMaterial(material)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-4 h-4"
                      />
                    </td>
                          <td className="px-2 py-2 text-gray-600 text-xs">{assetDetails?.asset_type_name || material.item_description || 'Asset'}</td>
                          <td className="px-2 py-2 font-medium text-gray-800 text-xs">{assetDetails ? `${assetDetails.manufacturer || ''} ${assetDetails.model || ''}`.trim() : material.item_description}</td>
                          <td className="px-2 py-2 font-mono text-xs">{assetDetails?.serial_number || '-'}</td>
                          <td className="px-2 py-2 text-center">
                      {isSelected ? (
                              <span className="text-orange-600 font-bold text-xs">✓</span>
                      ) : (
                              <span className="text-gray-400 text-xs">○</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
              </div>
              <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                {returnedItems.filter(i => i.item_type === 'asset').length}/{assetItems.length} asset selezionati
              </div>
            </>
          )}
        </div>
      )}

      {/* TAB MATERIALI */}
      {returnTab === 'materiali' && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {inventoryItems.length === 0 ? (
            <p className="text-gray-500 italic p-4 text-sm">Nessun materiale di magazzino assegnato</p>
          ) : (
            <>
              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                <table className="w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-100 sticky top-0 z-10">
                    <tr>
                      <th className="px-2 py-2 text-left w-10">
                        <input
                          type="checkbox"
                          checked={inventoryItems.length > 0 && inventoryItems.every(m =>
                            returnedItems.some(item => item.item_type === 'inventory' && item.inventory_sku_id === m.inventory_sku_id)
                          )}
                          onChange={(e) => {
                            if (e.target.checked) {
                              const newItems = inventoryItems
                                .filter(m => !returnedItems.some(item => item.item_type === 'inventory' && item.inventory_sku_id === m.inventory_sku_id))
                                .map(m => ({
                                  item_type: 'inventory' as const,
                                  inventory_sku_id: m.inventory_sku_id,
                                  quantity: m.quantity,
                                  notes: `Ritirato da assegnazione ${m.assignment_number}`
                                }));
                              setReturnedItems([...returnedItems, ...newItems]);
                            } else {
                              setReturnedItems(returnedItems.filter(item =>
                                !(item.item_type === 'inventory' && inventoryItems.some(m => m.inventory_sku_id === item.inventory_sku_id))
                              ));
                            }
                          }}
                          className="w-4 h-4"
                        />
                      </th>
                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Descrizione</th>
                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase">Quantità</th>
                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-20">Stato</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inventoryItems.map((material, index) => {
            const isSelected = returnedItems.some(
                        item => item.item_type === 'inventory' && item.inventory_sku_id === material.inventory_sku_id
            );
            return (
                        <tr
                key={index}
                          className={`hover:bg-gray-50 cursor-pointer transition-colors ${isSelected ? 'bg-orange-50' : ''}`}
                onClick={() => handleToggleMaterial(material)}
                        >
                          <td className="px-2 py-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleMaterial(material)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-4 h-4"
                            />
                          </td>
                          <td className="px-2 py-2 font-medium text-gray-800 text-xs">📦 {material.item_description}</td>
                          <td className="px-2 py-2 text-center text-xs">{material.quantity}</td>
                          <td className="px-2 py-2 text-center">
                            {isSelected ? (
                              <span className="text-orange-600 font-bold text-xs">✓</span>
                            ) : (
                              <span className="text-gray-400 text-xs">○</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                    </div>
              <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                {returnedItems.filter(i => i.item_type === 'inventory').length}/{inventoryItems.length} materiali selezionati
                    </div>
            </>
          )}
                  </div>
      )}

      {/* TAB SIM */}
      {returnTab === 'sim' && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {simItems.length === 0 ? (
            <p className="text-gray-500 italic p-4 text-sm">Nessuna SIM assegnata</p>
          ) : (
            <>
              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                <table className="w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-100 sticky top-0 z-10">
                    <tr>
                      <th className="px-2 py-2 text-left w-10">
                        <input
                          type="checkbox"
                          checked={simItems.length > 0 && simItems.every(m =>
                            returnedItems.some(item => item.item_type === 'sim' && item.sim_id === m.sim_id)
                          )}
                          onChange={(e) => {
                            if (e.target.checked) {
                              const newItems = simItems
                                .filter(m => !returnedItems.some(item => item.item_type === 'sim' && item.sim_id === m.sim_id))
                                .map(m => ({
                                  item_type: 'sim' as const,
                                  sim_id: m.sim_id,
                                  quantity: m.quantity,
                                  notes: `Ritirato da assegnazione ${m.assignment_number}`
                                }));
                              setReturnedItems([...returnedItems, ...newItems]);
                            } else {
                              setReturnedItems(returnedItems.filter(item =>
                                !(item.item_type === 'sim' && simItems.some(m => m.sim_id === item.sim_id))
                              ));
                            }
                          }}
                          className="w-4 h-4"
                        />
                      </th>
                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Descrizione</th>
                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-20">Stato</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {simItems.map((material, index) => {
                      const isSelected = returnedItems.some(
                        item => item.item_type === 'sim' && item.sim_id === material.sim_id
                      );
                      return (
                        <tr
                          key={index}
                          className={`hover:bg-gray-50 cursor-pointer transition-colors ${isSelected ? 'bg-orange-50' : ''}`}
                          onClick={() => handleToggleMaterial(material)}
                        >
                          <td className="px-2 py-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleMaterial(material)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-4 h-4"
                            />
                          </td>
                          <td className="px-2 py-2 font-medium text-gray-800 text-xs">📱 {material.item_description}</td>
                          <td className="px-2 py-2 text-center">
                    {isSelected ? (
                              <span className="text-orange-600 font-bold text-xs">✓</span>
                            ) : (
                              <span className="text-gray-400 text-xs">○</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                  </div>
              <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                {returnedItems.filter(i => i.item_type === 'sim').length}/{simItems.length} SIM selezionate
                </div>
            </>
          )}
              </div>
      )}

      {/* TAB BADGE */}
      {returnTab === 'badge' && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {badgeItems.length === 0 ? (
            <p className="text-gray-500 italic p-4 text-sm">Nessun badge assegnato</p>
          ) : (
            <>
              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                <table className="w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-100 sticky top-0 z-10">
                    <tr>
                      <th className="px-2 py-2 text-left w-10">
                        <input
                          type="checkbox"
                          checked={badgeItems.length > 0 && badgeItems.every(m =>
                            returnedItems.some(item => item.item_type === 'badge' && item.badge_id === m.badge_id)
                          )}
                          onChange={(e) => {
                            if (e.target.checked) {
                              const newItems = badgeItems
                                .filter(m => !returnedItems.some(item => item.item_type === 'badge' && item.badge_id === m.badge_id))
                                .map(m => ({
                                  item_type: 'badge' as const,
                                  badge_id: m.badge_id,
                                  quantity: m.quantity,
                                  notes: `Ritirato da assegnazione ${m.assignment_number}`
                                }));
                              setReturnedItems([...returnedItems, ...newItems]);
                            } else {
                              setReturnedItems(returnedItems.filter(item =>
                                !(item.item_type === 'badge' && badgeItems.some(m => m.badge_id === item.badge_id))
                              ));
                            }
                          }}
                          className="w-4 h-4"
                        />
                      </th>
                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Descrizione</th>
                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-20">Stato</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {badgeItems.map((material, index) => {
                      const isSelected = returnedItems.some(
                        item => item.item_type === 'badge' && item.badge_id === material.badge_id
                      );
                      return (
                        <tr
                          key={index}
                          className={`hover:bg-gray-50 cursor-pointer transition-colors ${isSelected ? 'bg-orange-50' : ''}`}
                          onClick={() => handleToggleMaterial(material)}
                        >
                          <td className="px-2 py-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleMaterial(material)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-4 h-4"
                            />
                          </td>
                          <td className="px-2 py-2 font-medium text-gray-800 text-xs">🪪 {material.item_description}</td>
                          <td className="px-2 py-2 text-center">
                            {isSelected ? (
                              <span className="text-orange-600 font-bold text-xs">✓</span>
                            ) : (
                              <span className="text-gray-400 text-xs">○</span>
                            )}
                          </td>
                        </tr>
            );
          })}
                  </tbody>
                </table>
              </div>
              <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                {returnedItems.filter(i => i.item_type === 'badge').length}/{badgeItems.length} badge selezionati
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function Assignments() {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';
  
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [availableAssets, setAvailableAssets] = useState<Asset[]>([]);
  const [availableInventory, setAvailableInventory] = useState<InventorySku[]>([]);
  const [availableSims, setAvailableSims] = useState<Sim[]>([]);
  const [availableBadges, setAvailableBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);
  const [activeCount, setActiveCount] = useState(0);

  // Form wizard
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null);
  // Destination type toggle
  const [destinationType, setDestinationType] = useState<'person' | 'location'>('person');
  const [selectedLocationId, setSelectedLocationId] = useState<number | null>(null);
  const [availableLocations, setAvailableLocations] = useState<Array<{id: number; name: string; site_name?: string}>>([]);
  const [locationSearchQuery, setLocationSearchQuery] = useState('');
  const [selectedItems, setSelectedItems] = useState<AssignmentItemCreate[]>([]);
  const [assignmentDate, setAssignmentDate] = useState(new Date().toISOString().split('T')[0]);
  const [assignmentType, setAssignmentType] = useState('assegnazione');
  const [notes, setNotes] = useState('');
  const [password, setPassword] = useState('');
  const [pinSim, setPinSim] = useState('');
  const [pinSblocco, setPinSblocco] = useState('');

  // Filtri
  const [filterPersonId, setFilterPersonId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');

  // Elementi restituiti (campi allineati al backend: inventory_sku_id)
  const [returnedItems, setReturnedItems] = useState<Array<{
    item_type: 'asset' | 'inventory' | 'sim';
    asset_id?: number;
    inventory_sku_id?: number;
    sim_id?: number;
    quantity: number;
    notes?: string;
  }>>([]);

  const [activeTab, setActiveTab] = useState<'asset' | 'materiali' | 'sim' | 'badge'>('asset');
  const [assetSearchText, setAssetSearchText] = useState('');
  const [assetFilterType, setAssetFilterType] = useState('');
  const [inventorySearchText, setInventorySearchText] = useState('');
  const [simSearchText, setSimSearchText] = useState('');
  const [simFilterOperatore, setSimFilterOperatore] = useState('');
  const [badgeSearchText, setBadgeSearchText] = useState('');
  const [badgeFilterTipo, setBadgeFilterTipo] = useState('');

  // Person combobox (Step 1 wizard)
  const [personSearchQuery, setPersonSearchQuery] = useState('');
  const [personDropdownOpen, setPersonDropdownOpen] = useState(false);
  const personDropdownRef = useRef<HTMLDivElement>(null);
  const sortedPeople = useMemo(() => {
    return [...people].sort((a, b) => {
      const cmp = (a.last_name || '').localeCompare(b.last_name || '', 'it');
      return cmp !== 0 ? cmp : (a.first_name || '').localeCompare(b.first_name || '', 'it');
    });
  }, [people]);
  const filteredPeople = useMemo(() => {
    const q = personSearchQuery.trim().toLowerCase();
    if (!q) return sortedPeople;
    return sortedPeople.filter(
      p => (p.last_name || '').toLowerCase().includes(q) || (p.first_name || '').toLowerCase().includes(q)
    );
  }, [sortedPeople, personSearchQuery]);
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (personDropdownRef.current && !personDropdownRef.current.contains(e.target as Node)) {
        setPersonDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    fetchPeople();
    fetchAvailableAssets();
    fetchAvailableInventory();
    fetchAvailableSims();
    fetchAvailableBadges();
    fetchAvailableLocations();
  }, []);

  useEffect(() => {
    fetchAssignments();
  }, [activeOnly, filterPersonId, filterStatus, filterType]);

  const fetchPeople = async () => {
    try {
      const response = await api.get('/people', { params: { limit: 1000, is_active: true } });
      setPeople(response.data.items);
    } catch (error) {
      console.error('Errore caricamento persone:', error);
    }
  };

  const fetchAvailableAssets = async () => {
    try {
      const response = await api.get('/assets', { 
        params: { 
          limit: 1000, 
          is_active: true,
          status: 'disponibile'
        } 
      });
      setAvailableAssets(response.data.items);
    } catch (error) {
      console.error('Errore caricamento asset:', error);
    }
  };

  const fetchAvailableInventory = async () => {
    try {
      const response = await api.get('/inventory', { 
        params: { 
          limit: 1000, 
          is_active: true
        } 
      });
      setAvailableInventory(response.data.items);
    } catch (error) {
      console.error('Errore caricamento materiali:', error);
    }
  };

  const fetchAvailableSims = async () => {
    try {
      const response = await api.get('/sims', {
        params: {
          limit: 500,
          status: 'disponibile'
        }
      });
      setAvailableSims(response.data.items);
    } catch (error) {
      console.error('Errore caricamento SIM:', error);
    }
  };

  const fetchAvailableBadges = async () => {
    try {
      const response = await api.get('/badges', {
        params: {
          limit: 1000,
          status: 'attivo'
        }
      });
      setAvailableBadges(response.data.items || []);
    } catch (error) {
      console.error('Errore caricamento badge:', error);
    }
  };

  const fetchAvailableLocations = async () => {
    try {
      const response = await api.get('/locations', {
        params: { is_active: true, limit: 1000 }
      });
      setAvailableLocations(response.data.items || []);
    } catch (error) {
      console.error('Errore caricamento locazioni:', error);
    }
  };

  const handleAddSim = async (sim: Sim) => {
    try {
      // Chiamata API per ottenere le credenziali (PIN decriptato)
      const response = await api.get(`/sims/${sim.id}/credentials`);
      const credentials = response.data;

      // Popola automaticamente il campo PIN SIM
      if (credentials.pin) {
        setPinSim(credentials.pin);
      }

      // Aggiungi la SIM agli items selezionati
      setSelectedItems([...selectedItems, {
        item_type: 'sim',
        sim_id: sim.id,
        quantity: 1
      }]);

    } catch (error: unknown) {
      console.error('Errore recupero credenziali SIM:', error);
      // Anche in caso di errore, aggiungi la SIM (il PIN andrà inserito manualmente)
      setSelectedItems([...selectedItems, {
        item_type: 'sim',
        sim_id: sim.id,
        quantity: 1
      }]);
    }
  };

  const handleAddBadge = (badge: Badge) => {
    setSelectedItems([...selectedItems, {
      item_type: 'badge',
      badge_id: badge.id,
      quantity: 1,
      notes: ''
    }]);
  };

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (activeOnly) params.active_only = true;
      if (filterPersonId) params.person_id = filterPersonId;
      if (filterStatus) params.status = filterStatus;
      if (filterType) params.assignment_type = filterType;

      const response = await api.get('/assignments', { params });
      setAssignments(response.data.items);
      setActiveCount(response.data.active_count);
    } catch (error) {
      console.error('Errore caricamento assegnazioni:', error);
      alert('Errore nel caricamento delle assegnazioni');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAsset = (assetId: number) => {
    if (selectedItems.some(item => item.item_type === 'asset' && item.asset_id === assetId)) {
      alert('Asset già aggiunto');
      return;
    }
    setSelectedItems([...selectedItems, {
      item_type: 'asset',
      asset_id: assetId,
      quantity: 1
    }]);
  };

  const handleAddInventory = (skuId: number, quantity: number) => {
    if (quantity <= 0) {
      alert('Quantità deve essere maggiore di 0');
      return;
    }
    const sku = availableInventory.find(s => s.id === skuId);
    if (sku && quantity > sku.quantity) {
      alert(`Quantità disponibile: ${sku.quantity}`);
      return;
    }
    setSelectedItems([...selectedItems, {
      item_type: 'inventory',
      inventory_sku_id: skuId,
      quantity
    }]);
  };

  const handleRemoveItem = (index: number) => {
    const item = selectedItems[index];
    if (item?.item_type === 'sim') {
      setPinSim('');
    }
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (destinationType === 'person' && !selectedPersonId) {
      alert('Seleziona una persona');
      return;
    }
    if (destinationType === 'location' && !selectedLocationId) {
      alert('Seleziona una locazione');
      return;
    }
    if (assignmentType === 'riconsegna' && returnedItems.length === 0) {
      alert('Seleziona almeno un materiale da ritirare');
      return;
    }
    if (assignmentType === 'sostituzione' && (returnedItems.length === 0 || selectedItems.length === 0)) {
      alert('Seleziona materiale da ritirare E da assegnare');
      return;
    }
    if ((assignmentType === 'assegnazione' || assignmentType === 'rinnovo') && selectedItems.length === 0) {
      alert('Seleziona almeno un materiale da assegnare');
      return;
    }
    if (assignmentType !== 'sostituzione' && assignmentType !== 'riconsegna' && (!password || !pinSim || !pinSblocco)) {
      alert('Compila tutti i campi delle credenziali');
      return;
    }
    
    try {
      setSubmitting(true);
      
      // Crea assegnazione
      const response = await api.post('/assignments', {
        person_id: destinationType === 'person' ? selectedPersonId : null,
        location_id: destinationType === 'location' ? selectedLocationId : null,
        assignment_date: assignmentDate,
        assignment_type: assignmentType,
        items: assignmentType !== 'riconsegna' ? selectedItems : [], // Vuoto per riconsegna
        returned_items: (assignmentType === 'sostituzione' || assignmentType === 'riconsegna') ? returnedItems : undefined,
        notes: notes || null,
        status: 'attivo'
      });
      
      const newAssignment = response.data;
      const assignmentId = newAssignment.id;
      
      // Genera PDF in base al tipo di assegnazione
      if (assignmentType === 'sostituzione') {
        // PDF SOSTITUZIONE (include ritiro + consegna, no credenziali)
        try {
          const pdfResponse = await api.post(
            `/assignments/${assignmentId}/generate-substitution-pdf`,
            {},
            { responseType: 'blob' }
          );
          
          const blob = new Blob([pdfResponse.data], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${newAssignment.assignment_number.replace('/', '-')}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          alert('Sostituzione creata e PDF generato con successo!');
        } catch (pdfError: unknown) {
          console.error('Errore generazione PDF sostituzione:', pdfError);
          alert(getApiError(pdfError, 'Sostituzione creata ma errore nella generazione del PDF'));
        }
      } else if (assignmentType === 'riconsegna') {
        // PDF RICONSEGNA (include solo ritiro materiale, no credenziali)
        try {
          const pdfResponse = await api.post(
            `/assignments/${assignmentId}/generate-return-pdf`,
            {},
            { responseType: 'blob' }
          );

          const blob = new Blob([pdfResponse.data], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${newAssignment.assignment_number.replace('/', '-')}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);

          alert('Riconsegna creata e PDF generato con successo!');
        } catch (pdfError: unknown) {
          console.error('Errore generazione PDF riconsegna:', pdfError);
          alert(getApiError(pdfError, 'Riconsegna creata ma errore nella generazione del PDF'));
        }
      } else if (assignmentType !== 'riconsegna') {
        // PDF ASSEGNAZIONE STANDARD (nuova/rinnovo con credenziali)
        try {
        const pdfResponse = await api.post(
          `/assignments/${assignmentId}/generate-pdf`,
          {
            password: password,
            pin_sim: pinSim,
            pin_sblocco: pinSblocco
          },
          { responseType: 'blob' }
        );
        
        // Scarica automaticamente il PDF
        const blob = new Blob([pdfResponse.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${newAssignment.assignment_number}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        // Mostra messaggio con opzioni
        const personData = people.find(p => p.id === selectedPersonId);
        const locationData = availableLocations.find(l => l.id === selectedLocationId);
        const recipientName = destinationType === 'person'
          ? `${personData?.first_name || ''} ${personData?.last_name || ''}`.trim()
          : locationData?.name || 'Locazione';
        const personEmail = personData?.email || '';

        if (destinationType === 'person') {
          // Comportamento attuale: confirm + opzione email
          const action = confirm(
            `Assegnazione creata con successo!\nPDF generato: ${newAssignment.assignment_number}.pdf\n\n` +
            `Clicca OK per aprire l'email precompilata\nClicca Annulla per stampare il PDF`
          );
          if (action) {
            const subject = encodeURIComponent(`Foglio Assegnazione Materiale - ${newAssignment.assignment_number}`);
            const body = encodeURIComponent(
              `Gentile ${recipientName},\n\n` +
              `in allegato trovi il foglio di assegnazione materiale.\n\n` +
              `Credenziali:\n` +
              `- Password: ${password}\n` +
              `- PIN SIM: ${pinSim}\n` +
              `- PIN Sblocco: ${pinSblocco}\n\n` +
              `IMPORTANTE: Per motivi di sicurezza, cambia immediatamente la password del dispositivo e il PIN di sblocco del telefono.\n\n` +
              `Cordiali saluti,\nIT Asset Manager`
            );
            window.open(`mailto:${personEmail}?subject=${subject}&body=${body}`, '_blank');
          } else {
            const printWindow = window.open(url, '_blank');
            if (printWindow) {
              printWindow.onload = () => { printWindow.print(); };
            }
          }
        } else {
          // Locazione: solo conferma, niente email
          alert(`Assegnazione a locazione "${recipientName}" creata con successo!\nPDF generato: ${newAssignment.assignment_number}.pdf`);
        }
        
        } catch (pdfError: unknown) {
          console.error('Errore generazione PDF:', pdfError);
          alert('Assegnazione creata ma errore nella generazione del PDF: ' + getApiError(pdfError, 'errore sconosciuto'));
        }
      } else {
        // RICONSEGNA: non genera PDF automaticamente
        alert('Riconsegna registrata con successo!');
      }
      
      // Chiudi modal e resetta form
      setShowModal(false);
      resetForm();
      fetchAssignments();
      fetchAvailableAssets();
      fetchAvailableInventory();
      fetchAvailableSims();
      fetchAvailableBadges();
      
    } catch (error: unknown) {
      console.error('Errore creazione assegnazione:', error);
      alert(getApiError(error, 'Errore nella creazione dell\'assegnazione'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewPdf = (assignmentNumber: string) => {
    const pdfUrl = `/data/documents/${assignmentNumber}.pdf`;
    window.open(pdfUrl, '_blank');
  };

  const handleEmailPdf = async (assignment: Assignment) => {
    try {
      // URL diretto del PDF già generato (file statico)
      const pdfUrl = `/data/documents/${assignment.assignment_number}.pdf`;
      
      // Scarica il PDF usando fetch
      const response = await fetch(pdfUrl);
      
      if (!response.ok) {
        throw new Error('PDF non trovato');
      }
      
      const blob = await response.blob();
      
      // Scarica automaticamente il PDF nel computer
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${assignment.assignment_number}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Apri client email precompilato
      const personEmail = assignment.person_email || '';
      const subject = encodeURIComponent(`Foglio Assegnazione Materiale - ${assignment.assignment_number}`);
      const body = encodeURIComponent(
        `Gentile ${assignment.person_name},\n\n` +
        `in allegato trovi il foglio di assegnazione materiale.\n\n` +
        `Ti preghiamo di verificare i dati. Il documento cartaceo firmato ti verrà consegnato a mano.\n\n` +
        `Cordiali saluti,\nIT Asset Manager`
      );
      window.open(`mailto:${personEmail}?subject=${subject}&body=${body}`, '_blank');
      
    } catch (error) {
      console.error('Errore apertura email:', error);
      alert('Errore durante il download del PDF. Verifica che il PDF sia stato generato.');
    }
  };

  const handleReturn = async (assignmentId: number) => {
    const returnDate = prompt('Data riconsegna (YYYY-MM-DD):', new Date().toISOString().split('T')[0]);
    if (!returnDate) return;

    if (!confirm('Confermi la riconsegna? Gli asset torneranno disponibili e i materiali verranno ricaricati in magazzino.')) return;

    try {
      await api.post(`/assignments/${assignmentId}/complete?return_date=${returnDate}`);
      fetchAssignments();
      fetchAvailableAssets();
      fetchAvailableInventory();
      fetchAvailableSims();
      fetchAvailableBadges();
      alert('Riconsegna completata! Asset e materiali ripristinati.');
    } catch (error: unknown) {
      console.error('Errore riconsegna:', error);
      alert(getApiError(error, 'Errore nella riconsegna'));
    }
  };

  const handleSubstitution = (assignment: Assignment) => {
    if (!confirm(`Vuoi sostituire materiale per ${assignment.person_name}?\n\nVerrà creata una nuova assegnazione di tipo "sostituzione".`)) return;
    
    // Pre-compila il form con la persona esistente
    setSelectedPersonId(assignment.person_id);
    setAssignmentType('sostituzione');
    setAssignmentDate(new Date().toISOString().split('T')[0]);
    setNotes(`Sostituzione per assegnazione ${assignment.assignment_number}`);
    setReturnedItems([]);  // Reset materiali da ritirare
    setSelectedItems([]);  // Reset materiali da assegnare
    setShowModal(true);
  };

  const handleShowDetails = (assignment: Assignment) => {
    setSelectedAssignment(assignment);
    setShowDetailsModal(true);
  };

  const resetForm = () => {
    setCurrentStep(1);
    setSelectedPersonId(null);
    setSelectedItems([]);
    setReturnedItems([]);  // Reset materiali da ritirare
    setAssignmentDate(new Date().toISOString().split('T')[0]);
    setAssignmentType('assegnazione');
    setNotes('');
    setPassword('');
    setPinSim('');
    setPinSblocco('');
    setActiveTab('asset');
    setAssetSearchText('');
    setAssetFilterType('');
    setInventorySearchText('');
    setSimSearchText('');
    setSimFilterOperatore('');
    setBadgeSearchText('');
    setBadgeFilterTipo('');
    setPersonSearchQuery('');
    setPersonDropdownOpen(false);
    setDestinationType('person');
    setSelectedLocationId(null);
    setLocationSearchQuery('');
  };

  const getItemDescription = (item: AssignmentItemCreate): string => {
    if (item.item_type === 'asset' && item.asset_id) {
      const asset = availableAssets.find(a => a.id === item.asset_id);
      return asset ? `${asset.manufacturer} ${asset.model} (SN: ${asset.serial_number})` : 'Asset sconosciuto';
    }
    if (item.item_type === 'inventory' && item.inventory_sku_id) {
      const sku = availableInventory.find(s => s.id === item.inventory_sku_id);
      return sku ? `${sku.brand ? sku.brand + ' ' : ''}${sku.device} x${item.quantity}` : 'Materiale sconosciuto';
    }
    if (item.item_type === 'sim' && item.sim_id) {
      const sim = availableSims.find(s => s.id === item.sim_id);
      if (sim) {
        return `📱 SIM ${sim.operatore} - ${sim.numero_telefono}`;
      }
    }
    if (item.item_type === 'badge' && item.badge_id) {
      const badge = availableBadges.find(b => b.id === item.badge_id);
      if (badge) {
        return `🪪 Badge ${badge.numero_badge} (${badge.tipo})`;
      }
    }
    return 'Item sconosciuto';
  };

  // Calcolo statistiche assegnazioni
  const totalAssignments = assignments.length;
  const newAssignments = assignments.filter(a => a.assignment_type === 'assegnazione').length;
  const substitutions = assignments.filter(a => a.assignment_type === 'sostituzione').length;
  const returns = assignments.filter(a => a.assignment_type === 'riconsegna').length;
  const activeAssignments = assignments.filter(a => a.status === 'attivo').length;

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        {/* HEADER MODERNO */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <ClipboardDocumentListIcon className="w-7 h-7 text-white" />
            </div>
          <div>
              <h1 className="text-4xl font-bold text-gray-800">Gestione Assegnazioni</h1>
              <p className="text-sm text-gray-600 mt-1">
                {activeCount > 0 ? `${activeCount} ${activeCount === 1 ? 'assegnazione attiva' : 'assegnazioni attive'}` : 'Nessuna assegnazione attiva'}
              </p>
          </div>
          </div>
          <div className="flex justify-end">
          {!isUser && (
            <Button
              variant="primary"
              icon="➕"
              onClick={() => {
                resetForm();
                setShowModal(true);
              }}
            >
              Nuova Assegnazione
            </Button>
          )}
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatsCard
            title="Totale"
            value={totalAssignments}
            subtitle="Assegnazioni totali"
            icon={ClipboardDocumentListIcon}
            gradient="blue"
          />

          <StatsCard
            title="Nuove"
            value={newAssignments}
            subtitle="Assegnazioni"
            icon={PlusCircleIcon}
            gradient="yellow"
          />

          <StatsCard
            title="Sostituzioni"
            value={substitutions}
            icon={ArrowPathIcon}
            gradient="orange"
          />

          <StatsCard
            title="Riconsegne"
            value={returns}
            icon={ArrowUturnLeftIcon}
            gradient="red"
          />

          <StatsCard
            title="Attive"
            value={activeAssignments}
            subtitle="In corso"
            icon={ClipboardDocumentListIcon}
            gradient="green"
          />
        </div>

        {/* Filtri */}
        <div className="mb-4 flex gap-4 items-center flex-wrap">
          <select
            value={filterPersonId || ''}
            onChange={(e) => setFilterPersonId(e.target.value ? parseInt(e.target.value) : null)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
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
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          >
            <option value="">Tutti gli stati</option>
            <option value="attivo">Attivo</option>
            <option value="completato">Completato</option>
          </select>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
          >
            <option value="">Tutti i tipi</option>
            <option value="assegnazione">Assegnazione</option>
            <option value="riconsegna">Riconsegna</option>
            <option value="sostituzione">Sostituzione</option>
          </select>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="w-4 h-4 text-asset-manager-gray rounded focus:ring-2 focus:ring-asset-manager-yellow"
            />
            Solo attive
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
                  <th className="px-6 py-3 text-left">N° Assegnazione</th>
                  <th className="px-6 py-3 text-left">Persona</th>
                  <th className="px-6 py-3 text-left">Data</th>
                  <th className="px-6 py-3 text-left">Tipo</th>
                  <th className="px-6 py-3 text-left">Stato</th>
                  <th className="px-6 py-3 text-left">Items</th>
                  <th className="px-6 py-3 text-right">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((assignment) => (
                  <tr key={assignment.id} className="border-t hover:bg-yellow-50 transition-colors">
                    <td className="px-6 py-4 font-mono text-sm">{assignment.assignment_number}</td>
                    <td className="px-6 py-4">
                      <div className="font-medium">{assignment.person_name}</div>
                      {assignment.person_email && (
                        <div className="text-sm text-gray-600">{assignment.person_email}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div>{new Date(assignment.assignment_date).toLocaleDateString('it-IT')}</div>
                      {assignment.return_date && (
                        <div className="text-sm text-gray-600">
                          Ric: {new Date(assignment.return_date).toLocaleDateString('it-IT')}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 capitalize">{assignment.assignment_type}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                        assignment.status === 'attivo' 
                          ? 'bg-green-50 text-green-700 border-green-200' 
                          : 'bg-gray-50 text-gray-700 border-gray-200'
                      }`}>
                        {assignment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">{assignment.items.length} items</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        {/* Bottoni Gestione - Nascosti per user */}
                        {!isUser && (
                          <>
                            <div className="flex gap-2">
                              {/* 1. Dettagli - PRIMARY */}
                              <Button
                                variant="primary"
                                icon="👁️"
                                iconOnly
                                title="Visualizza dettagli"
                                onClick={() => handleShowDetails(assignment)}
                              />
                              {assignment.is_active && (
                                <>
                                  {/* 2. Riconsegna - SECONDARY */}
                                  <Button
                                    variant="secondary"
                                    icon="↩️"
                                    iconOnly
                                    title="Riconsegna materiale"
                                    onClick={() => handleReturn(assignment.id)}
                                  />
                                  {/* 3. Sostituzione - PRIMARY */}
                                  <Button
                                    variant="primary"
                                    icon="🔄"
                                    iconOnly
                                    title="Sostituisci materiale"
                                    onClick={() => handleSubstitution(assignment)}
                                  />
                                </>
                              )}
                            </div>
                            
                            {/* Separatore visivo */}
                            <div className="border-l border-gray-300 mx-2"></div>
                          </>
                        )}
                        
                        {/* Bottoni PDF - Visibili per tutti */}
                        <div className="flex gap-2">
                          {/* 4. PDF - SECONDARY */}
                          <Button
                            variant="secondary"
                            icon="📄"
                            iconOnly
                            title="Visualizza PDF"
                            onClick={() => handleViewPdf(assignment.assignment_number)}
                          />
                          {/* 5. Email - PRIMARY - Nascosto per user */}
                          {!isUser && (
                            <Button
                              variant="primary"
                              icon="📧"
                              iconOnly
                              title="Invia via Email"
                              onClick={() => handleEmailPdf(assignment)}
                            />
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
                {assignments.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                      Nessuna assegnazione trovata
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>
          </div>
        )}

        {/* Modal Nuova Assegnazione */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-lg p-6 w-full max-w-6xl my-8 shadow-2xl">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">Nuova Assegnazione</h2>
              
              {/* Step indicator */}
              <div className="flex justify-center mb-6">
                <div className="flex items-center">
                  {[
                    { num: 1, label: 'Persona' },
                    { num: 2, label: assignmentType === 'sostituzione' ? 'Materiali' : assignmentType === 'riconsegna' ? 'Ritiro' : 'Materiali' },
                    ...(assignmentType === 'sostituzione' || assignmentType === 'riconsegna' ? [] : [{ num: 3, label: 'Credenziali' }]),
                    { num: (assignmentType === 'sostituzione' || assignmentType === 'riconsegna') ? 3 : 4, label: 'Riepilogo' }
                  ].map((step, index, array) => (
                    <div key={step.num} className="flex items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold transition-colors duration-200 ${
                        currentStep >= step.num ? 'bg-asset-manager-yellow text-asset-manager-gray' : 'bg-gray-300 text-gray-600'
                      }`}>
                        {step.num}
                      </div>
                      {index < array.length - 1 && (
                        <div className={`w-16 h-1 ${currentStep > step.num ? 'bg-asset-manager-yellow' : 'bg-gray-300'}`}></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Step 1: Seleziona destinatario (Persona o Locazione) */}
              {currentStep === 1 && (
                <div className="space-y-4">

                  {/* RADIO TOGGLE PERSONA / LOCAZIONE */}
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-700">Destinatario *</label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="destinationType"
                          value="person"
                          checked={destinationType === 'person'}
                          onChange={() => {
                            setDestinationType('person');
                            setSelectedLocationId(null);
                            setLocationSearchQuery('');
                          }}
                          className="w-4 h-4 text-asset-manager-yellow"
                        />
                        <span className="text-sm font-medium text-gray-700">👤 Persona</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="destinationType"
                          value="location"
                          checked={destinationType === 'location'}
                          onChange={() => {
                            setDestinationType('location');
                            setSelectedPersonId(null);
                            setPersonSearchQuery('');
                            setPersonDropdownOpen(false);
                            // Locazione: forza tipo assegnazione (no riconsegna/sostituzione)
                            if (assignmentType === 'riconsegna' || assignmentType === 'sostituzione') {
                              setAssignmentType('assegnazione');
                            }
                          }}
                          className="w-4 h-4 text-asset-manager-yellow"
                        />
                        <span className="text-sm font-medium text-gray-700">📍 Locazione</span>
                      </label>
                    </div>
                  </div>

                  {/* SELEZIONE PERSONA (visibile solo se destinationType === 'person') */}
                  {destinationType === 'person' && (
                    <div ref={personDropdownRef} className="relative">
                      <label className="block text-sm font-medium mb-1 text-gray-700">Persona *</label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          required={!selectedPersonId}
                          value={selectedPersonId
                            ? `${people.find(p => p.id === selectedPersonId)?.last_name || ''} ${people.find(p => p.id === selectedPersonId)?.first_name || ''}`.trim()
                            : personSearchQuery
                          }
                          onChange={(e) => {
                            if (!selectedPersonId) {
                              setPersonSearchQuery(e.target.value);
                              setPersonDropdownOpen(true);
                            }
                          }}
                          onFocus={() => setPersonDropdownOpen(true)}
                          placeholder={selectedPersonId ? '' : 'Cerca persona per cognome o nome...'}
                          readOnly={!!selectedPersonId}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                        />
                        {selectedPersonId && (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedPersonId(null);
                              setPersonSearchQuery('');
                              setPersonDropdownOpen(false);
                            }}
                            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 text-gray-600"
                            title="Cancella selezione"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                      {personDropdownOpen && !selectedPersonId && (
                        <ul
                          className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto bg-white border border-gray-300 rounded-lg shadow-lg"
                          style={{ minHeight: '40px' }}
                        >
                          {filteredPeople.length === 0 ? (
                            <li className="px-3 py-2 text-sm text-gray-500">Nessuna persona trovata</li>
                          ) : (
                            filteredPeople.map(person => (
                              <li
                                key={person.id}
                                className="px-3 py-2 text-sm cursor-pointer hover:bg-asset-manager-yellow/30 hover:text-asset-manager-gray"
                                onClick={() => {
                                  setSelectedPersonId(person.id);
                                  setPersonSearchQuery('');
                                  setPersonDropdownOpen(false);
                                }}
                              >
                                {person.last_name} {person.first_name} {person.email ? `(${person.email})` : ''}
                              </li>
                            ))
                          )}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* SELEZIONE LOCAZIONE (visibile solo se destinationType === 'location') */}
                  {destinationType === 'location' && (
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Locazione *</label>
                      <input
                        type="text"
                        placeholder="Cerca locazione..."
                        value={locationSearchQuery}
                        onChange={(e) => setLocationSearchQuery(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow mb-2 text-sm"
                      />
                      <div className="max-h-48 overflow-y-auto border border-gray-300 rounded-lg">
                        {availableLocations
                          .filter(loc => {
                            const q = locationSearchQuery.toLowerCase();
                            return !q ||
                              loc.name.toLowerCase().includes(q) ||
                              (loc.site_name || '').toLowerCase().includes(q);
                          })
                          .map(loc => (
                            <div
                              key={loc.id}
                              onClick={() => {
                                setSelectedLocationId(loc.id);
                                setLocationSearchQuery(loc.name);
                              }}
                              className={`px-3 py-2 cursor-pointer text-sm border-b border-gray-100 last:border-0 ${
                                selectedLocationId === loc.id
                                  ? 'bg-asset-manager-yellow text-asset-manager-gray font-semibold'
                                  : 'hover:bg-gray-50'
                              }`}
                            >
                              📍 {loc.name}
                              {loc.site_name && <span className="text-gray-500 ml-2 text-xs">({loc.site_name})</span>}
                            </div>
                          ))
                        }
                        {availableLocations.length === 0 && (
                          <p className="px-3 py-2 text-sm text-gray-500">Nessuna locazione disponibile</p>
                        )}
                      </div>
                      {selectedLocationId && (
                        <div className="mt-1 flex items-center gap-2">
                          <span className="text-xs text-green-600 font-medium">
                            ✓ Selezionata: {availableLocations.find(l => l.id === selectedLocationId)?.name}
                          </span>
                          <button
                            type="button"
                            onClick={() => { setSelectedLocationId(null); setLocationSearchQuery(''); }}
                            className="text-xs text-gray-400 hover:text-red-500"
                          >
                            ✕
                          </button>
                        </div>
                      )}
                      <p className="text-xs text-gray-500 mt-2">
                        ℹ️ Per assegnazioni a locazione è disponibile solo il tipo &quot;Assegnazione&quot;
                      </p>
                    </div>
                  )}

                  {/* DATA, TIPO, NOTE — invariati ma Tipo filtrato per locazione */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Data Assegnazione *</label>
                      <input
                        type="date"
                        required
                        value={assignmentDate}
                        onChange={(e) => setAssignmentDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-700">Tipo *</label>
                      <select
                        required
                        value={assignmentType}
                        onChange={(e) => setAssignmentType(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                      >
                        <option value="assegnazione">Assegnazione</option>
                        {destinationType === 'person' && (
                          <>
                            <option value="riconsegna">Riconsegna</option>
                            <option value="sostituzione">Sostituzione</option>
                          </>
                        )}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1 text-gray-700">Note</label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                      rows={3}
                    />
                  </div>
                </div>
              )}

              {/* Step 2: Materiali */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  {/* Per RICONSEGNA: solo ritiro */}
                  {assignmentType === 'riconsegna' && (
                    <div className="border-2 border-orange-300 bg-orange-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold mb-3 text-orange-800">📥 Materiale da Ritirare</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        Seleziona i materiali che il dipendente deve restituire
                      </p>
                      
                      <MaterialReturnSelector 
                        personId={selectedPersonId}
                        returnedItems={returnedItems}
                        setReturnedItems={setReturnedItems}
                      />
                    </div>
                  )}

                  {/* Per SOSTITUZIONE: ritiro + assegnazione */}
                  {assignmentType === 'sostituzione' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        {/* Colonna sinistra: Materiale da Ritirare */}
                        <div className="border-2 border-orange-300 bg-orange-50 rounded-lg p-3">
                        <h3 className="text-base font-semibold mb-2 text-orange-800">📥 Materiale da Ritirare</h3>
                        {/* Componente per selezionare materiali da ritirare */}
                        <MaterialReturnSelector 
                          personId={selectedPersonId}
                          returnedItems={returnedItems}
                          setReturnedItems={setReturnedItems}
                        />
                      </div>

                        {/* Colonna destra: Materiale da Assegnare */}
                        <div className="border-2 border-green-300 bg-green-50 rounded-lg p-3">
                          <h3 className="text-base font-semibold mb-2 text-green-800">📤 Materiale da Assegnare</h3>

                          {/* TAB NAVIGATION */}
                          <div className="flex border-b border-gray-300 mb-3">
                            <button
                              onClick={() => setActiveTab('asset')}
                              className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
                              activeTab === 'asset'
                                ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            🖥️ Asset
                          </button>
                          <button
                            onClick={() => setActiveTab('materiali')}
                            className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
                              activeTab === 'materiali'
                                ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            📦 Materiali
                          </button>
                          <button
                            onClick={() => setActiveTab('sim')}
                            className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
                              activeTab === 'sim'
                                ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            📱 SIM
                          </button>
                          <button
                            onClick={() => setActiveTab('badge')}
                            className={`px-3 py-1.5 font-semibold text-xs transition-colors ${
                              activeTab === 'badge'
                                ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                          >
                            🪪 Badge
                          </button>
                        </div>

                        {/* TAB ASSET */}
                        {activeTab === 'asset' && (
                          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            {availableAssets.length === 0 ? (
                              <p className="text-gray-500 italic p-4">Nessun asset disponibile</p>
                            ) : (
                              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                                <table className="w-full divide-y divide-gray-200">
                                  <thead className="bg-gray-100 sticky top-0 z-10">
                                    <tr>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Tipo</th>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Marca/Modello</th>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Seriale</th>
                                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-16">Stato</th>
                                </tr>
                              </thead>
                                  <tbody className="bg-white divide-y divide-gray-200">
                                    {availableAssets
                                      .filter(asset => !selectedItems.some(item => item.item_type === 'asset' && item.asset_id === asset.id))
                                      .filter(asset => {
                                        const search = assetSearchText.toLowerCase();
                                        const matchesSearch = !search ||
                                          (asset.asset_type_name || '').toLowerCase().includes(search) ||
                                          (asset.manufacturer || '').toLowerCase().includes(search) ||
                                          (asset.model || '').toLowerCase().includes(search) ||
                                          (asset.serial_number || '').toLowerCase().includes(search);
                                        const matchesType = !assetFilterType || asset.asset_type_name === assetFilterType;
                                        return matchesSearch && matchesType;
                                      })
                                      .map(asset => (
                                      <tr key={asset.id} className="hover:bg-yellow-50 transition-colors">
                                        <td className="px-2 py-2 text-sm text-gray-600">{asset.asset_type_name}</td>
                                        <td className="px-2 py-2 text-sm font-medium text-gray-800">{asset.manufacturer} {asset.model}</td>
                                        <td className="px-2 py-2 text-sm text-gray-600">{asset.serial_number}</td>
                                        <td className="px-2 py-2 text-center">
                                          <button
                                        onClick={() => handleAddAsset(asset.id)}
                                            className="text-green-600 hover:text-green-800 font-bold text-sm"
                                            title="Aggiungi"
                                          >
                                            ＋
                                          </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                            )}
                            <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                              {availableAssets
                                .filter(asset => !selectedItems.some(item => item.item_type === 'asset' && item.asset_id === asset.id))
                                .filter(asset => {
                                  const search = assetSearchText.toLowerCase();
                                  const matchesSearch = !search ||
                                    (asset.asset_type_name || '').toLowerCase().includes(search) ||
                                    (asset.manufacturer || '').toLowerCase().includes(search) ||
                                    (asset.model || '').toLowerCase().includes(search) ||
                                    (asset.serial_number || '').toLowerCase().includes(search);
                                  const matchesType = !assetFilterType || asset.asset_type_name === assetFilterType;
                                  return matchesSearch && matchesType;
                                }).length} asset trovati
                        </div>
                          </div>
                        )}

                        {/* TAB MATERIALI */}
                        {activeTab === 'materiali' && (
                          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            {availableInventory.length === 0 ? (
                              <p className="text-gray-500 italic p-4">Nessun materiale disponibile</p>
                            ) : (
                              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                                <table className="w-full divide-y divide-gray-200">
                                  <thead className="bg-gray-100 sticky top-0 z-10">
                                    <tr>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Categoria</th>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Dispositivo</th>
                                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase">Disp.</th>
                                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase">Qta</th>
                                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-16">Stato</th>
                                </tr>
                              </thead>
                                  <tbody className="bg-white divide-y divide-gray-200">
                                    {availableInventory
                                      .filter(sku => sku.quantity > 0)
                                      .filter(sku => {
                                        const search = inventorySearchText.toLowerCase();
                                        return !search ||
                                          (sku.category || '').toLowerCase().includes(search) ||
                                          (sku.device || '').toLowerCase().includes(search) ||
                                          (sku.brand || '').toLowerCase().includes(search);
                                      })
                                      .map(sku => (
                                      <tr key={sku.id} className="hover:bg-yellow-50 transition-colors">
                                        <td className="px-2 py-2 text-sm text-gray-600">{sku.category}</td>
                                        <td className="px-2 py-2 text-sm font-medium text-gray-800">{sku.brand && `${sku.brand} `}{sku.device}</td>
                                        <td className="px-2 py-2 text-center text-sm">
                                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                            'min_quantity' in sku && sku.quantity <= (sku as { min_quantity: number }).min_quantity
                                              ? 'bg-red-100 text-red-800'
                                              : 'bg-green-100 text-green-800'
                                          }`}>
                                            {sku.quantity}
                                          </span>
                                        </td>
                                        <td className="px-2 py-2 text-center">
                                          <input
                                            type="number"
                                            min="1"
                                            max={sku.quantity}
                                            defaultValue="1"
                                            id={`qty-sub-${sku.id}`}
                                            className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                                          />
                                        </td>
                                        <td className="px-2 py-2 text-center">
                                          <button
                                        onClick={() => {
                                              const qtyInput = document.getElementById(`qty-sub-${sku.id}`) as HTMLInputElement;
                                              const qty = parseInt(qtyInput?.value || '1');
                                              handleAddInventory(sku.id, qty);
                                            }}
                                            className="text-green-600 hover:text-green-800 font-bold text-sm"
                                            title="Aggiungi"
                                          >
                                            ＋
                                          </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                            )}
                            <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                              {availableInventory
                                .filter(sku => sku.quantity > 0)
                                .filter(sku => {
                                  const search = inventorySearchText.toLowerCase();
                                  return !search ||
                                    (sku.category || '').toLowerCase().includes(search) ||
                                    (sku.device || '').toLowerCase().includes(search) ||
                                    (sku.brand || '').toLowerCase().includes(search);
                                }).length} materiali trovati
                        </div>
                          </div>
                        )}

                        {/* TAB SIM */}
                        {activeTab === 'sim' && (
                          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            {availableSims.length === 0 ? (
                              <p className="text-gray-500 italic p-4">Nessuna SIM disponibile</p>
                            ) : (
                              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                                <table className="w-full divide-y divide-gray-200">
                                  <thead className="bg-gray-100 sticky top-0 z-10">
                                    <tr>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Operatore</th>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Numero</th>
                                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-16">Stato</th>
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white divide-y divide-gray-200">
                                    {availableSims
                                      .filter(sim => {
                                        const search = simSearchText.toLowerCase();
                                        const matchesSearch = !search ||
                                          (sim.numero_telefono || '').toLowerCase().includes(search) ||
                                          (sim.seriale || '').toLowerCase().includes(search) ||
                                          (sim.operatore || '').toLowerCase().includes(search);
                                        const matchesOperatore = !simFilterOperatore || sim.operatore === simFilterOperatore;
                                        return matchesSearch && matchesOperatore;
                                      })
                                      .map(sim => (
                                      <tr key={sim.id} className="hover:bg-yellow-50 transition-colors">
                                        <td className="px-2 py-2 text-sm font-medium text-gray-800">📱 {sim.operatore}</td>
                                        <td className="px-2 py-2 text-sm text-gray-600">{sim.numero_telefono}</td>
                                        <td className="px-2 py-2 text-center">
                                          <button
                                            onClick={() => handleAddSim(sim)}
                                            className="text-green-600 hover:text-green-800 font-bold text-sm"
                                            title="Aggiungi"
                                          >
                                            ＋
                                          </button>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                                  </div>
                            )}
                            <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                              {availableSims
                                .filter(sim => {
                                  const search = simSearchText.toLowerCase();
                                  const matchesSearch = !search ||
                                    (sim.numero_telefono || '').toLowerCase().includes(search) ||
                                    (sim.seriale || '').toLowerCase().includes(search) ||
                                    (sim.operatore || '').toLowerCase().includes(search);
                                  const matchesOperatore = !simFilterOperatore || sim.operatore === simFilterOperatore;
                                  return matchesSearch && matchesOperatore;
                                }).length} SIM trovate
                                </div>
                          </div>
                        )}

                        {/* TAB BADGE */}
                        {activeTab === 'badge' && (
                          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            {availableBadges.length === 0 ? (
                              <p className="text-gray-500 italic p-4">Nessun badge disponibile</p>
                            ) : (
                              <div className="max-h-56 overflow-y-auto overflow-x-hidden">
                                <table className="w-full divide-y divide-gray-200">
                                  <thead className="bg-gray-100 sticky top-0 z-10">
                                    <tr>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Numero</th>
                                      <th className="px-2 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Tipo</th>
                                      <th className="px-2 py-2 text-center text-xs font-semibold text-gray-700 uppercase w-16">Stato</th>
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white divide-y divide-gray-200">
                                    {availableBadges
                                      .filter(badge => !selectedItems.some(item => item.item_type === 'badge' && item.badge_id === badge.id))
                                      .filter(badge => {
                                        const search = badgeSearchText.toLowerCase();
                                        const matchesSearch = !search ||
                                          (badge.numero_badge || '').toLowerCase().includes(search) ||
                                          (badge.tipo || '').toLowerCase().includes(search);
                                        const matchesTipo = !badgeFilterTipo || badge.tipo === badgeFilterTipo;
                                        return matchesSearch && matchesTipo;
                                      })
                                      .map(badge => (
                                      <tr key={badge.id} className="hover:bg-yellow-50 transition-colors">
                                        <td className="px-2 py-2 text-sm font-medium text-gray-800">🪪 {badge.numero_badge}</td>
                                        <td className="px-2 py-2 text-sm text-gray-600">{badge.tipo}</td>
                                        <td className="px-2 py-2 text-center">
                                          <button
                                            onClick={() => handleAddBadge(badge)}
                                            className="text-green-600 hover:text-green-800 font-bold text-sm"
                                            title="Aggiungi"
                                          >
                                            ＋
                                          </button>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                            <div className="px-3 py-1 bg-gray-50 border-t text-xs text-gray-500">
                              {availableBadges
                                .filter(badge => !selectedItems.some(item => item.item_type === 'badge' && item.badge_id === badge.id))
                                .filter(badge => {
                                  const search = badgeSearchText.toLowerCase();
                                  const matchesSearch = !search ||
                                    (badge.numero_badge || '').toLowerCase().includes(search) ||
                                    (badge.tipo || '').toLowerCase().includes(search);
                                  const matchesTipo = !badgeFilterTipo || badge.tipo === badgeFilterTipo;
                                  return matchesSearch && matchesTipo;
                                }).length} badge trovati
                            </div>
                          </div>
                        )}
                      </div>
                      </div>

                      {/* Items Selezionati - a tutta larghezza sotto il grid */}
                      {selectedItems.length > 0 && (
                        <div className="mt-4 bg-white border border-green-300 rounded-lg p-4">
                          <h4 className="font-semibold mb-3 text-green-800">
                            📋 Items da Assegnare ({selectedItems.length})
                          </h4>
                          <ul className="space-y-2">
                            {selectedItems.map((item, idx) => (
                              <li key={idx} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                                <span className="text-gray-800">
                                  {getItemDescription(item)}
                                </span>
                                <button
                                  onClick={() => handleRemoveItem(idx)}
                                  className="text-red-600 hover:text-red-800 font-bold"
                                >
                                  ❌
                                </button>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Step 2: Materiali da Assegnare CON TAB (solo assegnazione/rinnovo) */}
                  {(assignmentType === 'assegnazione' || assignmentType === 'rinnovo') && (
                <div className="space-y-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">
                    Seleziona Materiali da Assegnare
                  </h3>

                  {/* TAB NAVIGATION */}
                  <div className="flex border-b border-gray-300 mb-6">
                    <button
                      onClick={() => setActiveTab('asset')}
                      className={`px-6 py-3 font-semibold transition-colors ${
                        activeTab === 'asset'
                          ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      🖥️ Asset
                    </button>
                    <button
                      onClick={() => setActiveTab('materiali')}
                      className={`px-6 py-3 font-semibold transition-colors ${
                        activeTab === 'materiali'
                          ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      📦 Materiali Magazzino
                    </button>
                    <button
                      onClick={() => setActiveTab('sim')}
                      className={`px-6 py-3 font-semibold transition-colors ${
                        activeTab === 'sim'
                          ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      📱 SIM
                    </button>
                    <button
                      onClick={() => setActiveTab('badge')}
                      className={`px-6 py-3 font-semibold transition-colors ${
                        activeTab === 'badge'
                          ? 'bg-asset-manager-yellow text-asset-manager-gray border-b-4 border-asset-manager-yellow'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      🪪 Badge
                    </button>
                  </div>

                  {/* TAB CONTENT - ASSET */}
                  {activeTab === 'asset' && (
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                      <h4 className="font-semibold p-4 bg-gray-50 text-gray-700 border-b">Asset Disponibili</h4>
                      <div className="p-4 border-b border-gray-200 flex gap-3 items-center flex-wrap">
                        <div className="flex-1 min-w-[200px]">
                          <input
                            type="text"
                            placeholder="🔍 Cerca per codice, marca, modello, seriale..."
                            value={assetSearchText}
                            onChange={(e) => setAssetSearchText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                          />
                        </div>
                        <select
                          value={assetFilterType}
                          onChange={(e) => setAssetFilterType(e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                        >
                          <option value="">Tutte le tipologie</option>
                          {[...new Set(availableAssets.map(a => a.asset_type_name))].sort().map(type => (
                            <option key={type} value={type}>{type}</option>
                          ))}
                        </select>
                        {(assetSearchText || assetFilterType) && (
                          <button
                            onClick={() => { setAssetSearchText(''); setAssetFilterType(''); }}
                            className="px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Reset filtri"
                          >
                            ✕ Reset
                          </button>
                        )}
                      </div>
                      {availableAssets.length === 0 ? (
                        <p className="text-gray-500 italic p-4">Nessun asset disponibile</p>
                      ) : (
                        <>
                        <div className="max-h-96 overflow-y-auto border-t border-gray-200">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100 sticky top-0 z-10">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Tipo
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Marca/Modello
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Seriale
                                </th>
                                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Azione
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {availableAssets
                                .filter(asset => !selectedItems.some(item => item.item_type === 'asset' && item.asset_id === asset.id))
                                .filter(asset => {
                                  const search = assetSearchText.toLowerCase();
                                  const matchesSearch = !search ||
                                    (asset.asset_type_name || '').toLowerCase().includes(search) ||
                                    (asset.manufacturer || '').toLowerCase().includes(search) ||
                                    (asset.model || '').toLowerCase().includes(search) ||
                                    (asset.serial_number || '').toLowerCase().includes(search);
                                  const matchesType = !assetFilterType || asset.asset_type_name === assetFilterType;
                                  return matchesSearch && matchesType;
                                })
                                .map(asset => (
                                <tr key={asset.id} className="hover:bg-yellow-50 transition-colors">
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {asset.asset_type_name}
                                  </td>
                                  <td className="px-4 py-3 text-sm font-medium text-gray-800">
                                    {asset.manufacturer} {asset.model}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {asset.serial_number}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-center">
                                    <button
                                      onClick={() => handleAddAsset(asset.id)}
                                      className="bg-asset-manager-yellow text-asset-manager-gray px-3 py-1 rounded text-sm font-medium hover:bg-yellow-500 transition-colors"
                                    >
                                      + Aggiungi
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
                          {availableAssets
                            .filter(asset => !selectedItems.some(item => item.item_type === 'asset' && item.asset_id === asset.id))
                            .filter(asset => {
                              const search = assetSearchText.toLowerCase();
                              const matchesSearch = !search ||
                                (asset.asset_type_name || '').toLowerCase().includes(search) ||
                                (asset.manufacturer || '').toLowerCase().includes(search) ||
                                (asset.model || '').toLowerCase().includes(search) ||
                                (asset.serial_number || '').toLowerCase().includes(search);
                              const matchesType = !assetFilterType || asset.asset_type_name === assetFilterType;
                              return matchesSearch && matchesType;
                            }).length} asset trovati
                      </div>
                        </>
                      )}
                    </div>
                  )}

                  {/* TAB CONTENT - MATERIALI MAGAZZINO */}
                  {activeTab === 'materiali' && (
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                      <h4 className="font-semibold p-4 bg-gray-50 text-gray-700 border-b">Materiali Magazzino</h4>
                      <div className="p-4 border-b border-gray-200 flex gap-3 items-center flex-wrap">
                        <div className="flex-1 min-w-[200px]">
                          <input
                            type="text"
                            placeholder="🔍 Cerca per categoria, dispositivo, marca..."
                            value={inventorySearchText}
                            onChange={(e) => setInventorySearchText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                          />
                        </div>
                        {inventorySearchText && (
                          <button
                            onClick={() => setInventorySearchText('')}
                            className="px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Reset filtri"
                          >
                            ✕ Reset
                          </button>
                        )}
                      </div>
                      {availableInventory.length === 0 ? (
                        <p className="text-gray-500 italic p-4">Nessun materiale disponibile in magazzino</p>
                      ) : (
                        <>
                        <div className="max-h-96 overflow-y-auto border-t border-gray-200">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100 sticky top-0 z-10">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Categoria
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Dispositivo
                                </th>
                                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Disponibili
                                </th>
                                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Quantità
                                </th>
                                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Azione
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {availableInventory
                                .filter(sku => {
                                  const search = inventorySearchText.toLowerCase();
                                  return !search ||
                                    (sku.category || '').toLowerCase().includes(search) ||
                                    (sku.device || '').toLowerCase().includes(search) ||
                                    (sku.brand || '').toLowerCase().includes(search);
                                })
                                .map(sku => (
                                <tr key={sku.id} className="hover:bg-yellow-50 transition-colors">
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {sku.category}
                                  </td>
                                  <td className="px-4 py-3 text-sm font-medium text-gray-800">
                                    {sku.brand && `${sku.brand} `}{sku.device}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-center text-sm text-gray-600">
                                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                      'min_quantity' in sku && sku.quantity <= (sku as { min_quantity: number }).min_quantity
                                        ? 'bg-red-100 text-red-800'
                                        : 'bg-green-100 text-green-800'
                                    }`}>
                                      {sku.quantity}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-center">
                                    <input
                                      type="number"
                                      min="1"
                                      max={sku.quantity}
                                      defaultValue="1"
                                      id={`qty-${sku.id}`}
                                      className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                                    />
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-center">
                                    <button
                                      onClick={() => {
                                        const qtyInput = document.getElementById(`qty-${sku.id}`) as HTMLInputElement;
                                        const qty = parseInt(qtyInput?.value || '1');
                                        handleAddInventory(sku.id, qty);
                                      }}
                                      className="bg-asset-manager-yellow text-asset-manager-gray px-3 py-1 rounded text-sm font-medium hover:bg-yellow-500 transition-colors"
                                    >
                                      + Aggiungi
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
                          {availableInventory
                            .filter(sku => {
                              const search = inventorySearchText.toLowerCase();
                              return !search ||
                                (sku.category || '').toLowerCase().includes(search) ||
                                (sku.device || '').toLowerCase().includes(search) ||
                                (sku.brand || '').toLowerCase().includes(search);
                            }).length} materiali trovati
                      </div>
                        </>
                      )}
                                </div>
                  )}

                  {/* TAB CONTENT - SIM */}
                  {activeTab === 'sim' && (
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                      <h4 className="font-semibold p-4 bg-gray-50 text-gray-700 border-b">SIM Disponibili</h4>
                      <div className="p-4 border-b border-gray-200 flex gap-3 items-center flex-wrap">
                        <div className="flex-1 min-w-[200px]">
                          <input
                            type="text"
                            placeholder="🔍 Cerca per numero telefono, seriale..."
                            value={simSearchText}
                            onChange={(e) => setSimSearchText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                                />
                              </div>
                        <select
                          value={simFilterOperatore}
                          onChange={(e) => setSimFilterOperatore(e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                        >
                          <option value="">Tutti gli operatori</option>
                          {[...new Set(availableSims.map(s => s.operatore))].sort().map(op => (
                            <option key={op} value={op}>{op}</option>
                          ))}
                        </select>
                        {(simSearchText || simFilterOperatore) && (
                          <button
                            onClick={() => { setSimSearchText(''); setSimFilterOperatore(''); }}
                            className="px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Reset filtri"
                          >
                            ✕ Reset
                          </button>
                        )}
                          </div>
                      {availableSims.length === 0 ? (
                        <p className="text-gray-500 italic p-4">Nessuna SIM disponibile</p>
                      ) : (
                        <>
                        <div className="max-h-96 overflow-y-auto border-t border-gray-200">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100 sticky top-0 z-10">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Operatore
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Numero Telefono
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Seriale
                                </th>
                                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Azione
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {availableSims
                                .filter(sim => {
                                  const search = simSearchText.toLowerCase();
                                  const matchesSearch = !search ||
                                    (sim.numero_telefono || '').toLowerCase().includes(search) ||
                                    (sim.seriale || '').toLowerCase().includes(search) ||
                                    (sim.operatore || '').toLowerCase().includes(search);
                                  const matchesOperatore = !simFilterOperatore || sim.operatore === simFilterOperatore;
                                  return matchesSearch && matchesOperatore;
                                })
                                .map(sim => (
                                <tr key={sim.id} className="hover:bg-yellow-50 transition-colors">
                                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-800">
                                    📱 {sim.operatore}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {sim.numero_telefono}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {sim.seriale}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-center">
                                    <button
                                      onClick={() => handleAddSim(sim)}
                                      className="bg-asset-manager-yellow text-asset-manager-gray px-3 py-1 rounded text-sm font-medium hover:bg-yellow-500 transition-colors"
                                    >
                                      + Aggiungi
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
                          {availableSims
                            .filter(sim => {
                              const search = simSearchText.toLowerCase();
                              const matchesSearch = !search ||
                                (sim.numero_telefono || '').toLowerCase().includes(search) ||
                                (sim.seriale || '').toLowerCase().includes(search) ||
                                (sim.operatore || '').toLowerCase().includes(search);
                              const matchesOperatore = !simFilterOperatore || sim.operatore === simFilterOperatore;
                              return matchesSearch && matchesOperatore;
                            }).length} SIM trovate
                        </div>
                        </>
                      )}
                    </div>
                  )}

                  {/* TAB CONTENT - BADGE */}
                  {activeTab === 'badge' && (
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                      <h4 className="font-semibold p-4 bg-gray-50 text-gray-700 border-b">Badge Disponibili</h4>
                      <div className="p-4 border-b border-gray-200 flex gap-3 items-center flex-wrap">
                        <div className="flex-1 min-w-[200px]">
                          <input
                            type="text"
                            placeholder="🔍 Cerca per numero badge..."
                            value={badgeSearchText}
                            onChange={(e) => setBadgeSearchText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                          />
                        </div>
                        <select
                          value={badgeFilterTipo}
                          onChange={(e) => setBadgeFilterTipo(e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
                        >
                          <option value="">Tutti i tipi</option>
                          {[...new Set(availableBadges.map(b => b.tipo))].sort().map(tipo => (
                            <option key={tipo} value={tipo}>{tipo}</option>
                          ))}
                        </select>
                        {(badgeSearchText || badgeFilterTipo) && (
                          <button
                            onClick={() => { setBadgeSearchText(''); setBadgeFilterTipo(''); }}
                            className="px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Reset filtri"
                          >
                            ✕ Reset
                          </button>
                        )}
                      </div>
                      {availableBadges.length === 0 ? (
                        <p className="text-gray-500 italic p-4">Nessun badge disponibile</p>
                      ) : (
                        <>
                        <div className="max-h-96 overflow-y-auto border-t border-gray-200">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100 sticky top-0 z-10">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Numero
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Tipo
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Data Emissione
                                </th>
                                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                  Azione
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {availableBadges
                                .filter(badge => !selectedItems.some(item => item.item_type === 'badge' && item.badge_id === badge.id))
                                .filter(badge => {
                                  const search = badgeSearchText.toLowerCase();
                                  const matchesSearch = !search ||
                                    (badge.numero_badge || '').toLowerCase().includes(search) ||
                                    (badge.tipo || '').toLowerCase().includes(search);
                                  const matchesTipo = !badgeFilterTipo || badge.tipo === badgeFilterTipo;
                                  return matchesSearch && matchesTipo;
                                })
                                .map(badge => (
                                <tr key={badge.id} className="hover:bg-yellow-50 transition-colors">
                                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-800">
                                    🪪 {badge.numero_badge}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {badge.tipo}
                                  </td>
                                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                                    {new Date(badge.data_emissione).toLocaleDateString('it-IT')}
                                  </td>
                                  <td className="px-4 py-3 text-center">
                                    <button
                                      onClick={() => handleAddBadge(badge)}
                                      className="bg-asset-manager-yellow text-asset-manager-gray px-3 py-1 rounded text-sm font-medium hover:bg-yellow-500 transition-colors"
                                    >
                                      + Aggiungi
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
                          {availableBadges
                            .filter(badge => !selectedItems.some(item => item.item_type === 'badge' && item.badge_id === badge.id))
                            .filter(badge => {
                              const search = badgeSearchText.toLowerCase();
                              const matchesSearch = !search ||
                                (badge.numero_badge || '').toLowerCase().includes(search) ||
                                (badge.tipo || '').toLowerCase().includes(search);
                              const matchesTipo = !badgeFilterTipo || badge.tipo === badgeFilterTipo;
                              return matchesSearch && matchesTipo;
                            }).length} badge trovati
                        </div>
                        </>
                      )}
                    </div>
                  )}

                  {/* Items Selezionati (sotto le tab) */}
                  {selectedItems.length > 0 && (
                    <div className="mt-6 bg-green-50 border border-green-300 rounded-lg p-4">
                      <h4 className="font-semibold mb-3 text-green-800">
                        📋 Items da Assegnare ({selectedItems.length})
                      </h4>
                      <ul className="space-y-2">
                        {selectedItems.map((item, idx) => (
                          <li key={idx} className="flex justify-between items-center bg-white p-2 rounded">
                            <span className="text-gray-800">
                              {item.item_type === 'asset' && availableAssets.find(a => a.id === item.asset_id)
                                ? `${availableAssets.find(a => a.id === item.asset_id)?.manufacturer} ${availableAssets.find(a => a.id === item.asset_id)?.model}`
                                : item.item_type === 'inventory' && availableInventory.find(s => s.id === item.inventory_sku_id)
                                ? `${availableInventory.find(s => s.id === item.inventory_sku_id)?.device} x${item.quantity}`
                                : item.item_type === 'sim' && availableSims.find(s => s.id === item.sim_id)
                                ? `SIM ${availableSims.find(s => s.id === item.sim_id)?.operatore} - ${availableSims.find(s => s.id === item.sim_id)?.numero_telefono}`
                                : item.item_type === 'badge' && availableBadges.find(b => b.id === item.badge_id)
                                ? `🪪 Badge ${availableBadges.find(b => b.id === item.badge_id)?.numero_badge} (${availableBadges.find(b => b.id === item.badge_id)?.tipo})`
                                : getItemDescription(item)}
                            </span>
                            <button
                              onClick={() => handleRemoveItem(idx)}
                              className="text-red-600 hover:text-red-800 font-bold"
                            >
                              ❌
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                  )}
                </div>
              )}

              {/* Step 3: Credenziali - SOLO per nuova/rinnovo */}
              {currentStep === 3 && assignmentType !== 'sostituzione' && assignmentType !== 'riconsegna' && (
                <div className="space-y-4">
                  <div className="bg-asset-manager-yellow bg-opacity-10 border border-asset-manager-yellow rounded-lg p-4">
                    <h3 className="font-semibold text-asset-manager-gray mb-2">Inserisci Credenziali</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      Compila le credenziali da fornire al dipendente per l'utilizzo dei dispositivi assegnati.
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password *
                    </label>
                    <input
                      type="text"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      placeholder="Es: Password123!"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      PIN SIM *
                    </label>
                    <input
                      type="text"
                      value={pinSim}
                      onChange={(e) => setPinSim(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      placeholder="Es: 1234"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      PIN Sblocco *
                    </label>
                    <input
                      type="text"
                      value={pinSblocco}
                      onChange={(e) => setPinSblocco(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                      placeholder="Es: 5678"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Step 4 (o 3 per sostituzione/riconsegna): Riepilogo */}
              {((currentStep === 4 && assignmentType !== 'sostituzione' && assignmentType !== 'riconsegna') || 
                (currentStep === 3 && (assignmentType === 'sostituzione' || assignmentType === 'riconsegna'))) && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-lg">Riepilogo Assegnazione</h3>
                  
                  {/* Dati persona */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p><strong>Persona:</strong> {people.find(p => p.id === selectedPersonId)?.first_name} {people.find(p => p.id === selectedPersonId)?.last_name}</p>
                    <p><strong>Data:</strong> {assignmentDate}</p>
                    <p><strong>Tipo:</strong> {assignmentType}</p>
                  </div>

                  {/* MATERIALE DA RITIRARE - Per sostituzione E riconsegna */}
                  {(assignmentType === 'sostituzione' || assignmentType === 'riconsegna') && returnedItems.length > 0 && (
                    <div className="border-2 border-orange-300 bg-orange-50 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2 text-orange-800">📥 Materiale da Ritirare ({returnedItems.length})</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {returnedItems.map((item, idx) => (
                          <li key={idx}>
                            {item.item_type === 'asset' ? `💻 Asset #${item.asset_id}` : 
                             item.item_type === 'inventory' ? `📦 Materiale #${item.inventory_sku_id} x${item.quantity}` :
                             item.item_type === 'sim' ? `📱 SIM #${item.sim_id}` :
                             `${item.item_type} (Qta: ${item.quantity})`}
                            {item.notes && ` - ${item.notes}`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* MATERIALE DA ASSEGNARE - NO per riconsegna */}
                  {assignmentType !== 'riconsegna' && (
                    <div className="border-2 border-green-300 bg-green-50 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2 text-green-800">
                        📤 Materiale da Assegnare ({selectedItems.length})
                      </h4>
                      <ul className="list-disc list-inside space-y-1">
                        {selectedItems.map((item, index) => (
                          <li key={index}>{getItemDescription(item)}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Credenziali - NO per sostituzione E riconsegna */}
                  {assignmentType !== 'sostituzione' && assignmentType !== 'riconsegna' && (
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <h4 className="font-semibold mb-2">🔒 Credenziali</h4>
                      <p><strong>Password:</strong> {password}</p>
                      <p><strong>PIN SIM:</strong> {pinSim}</p>
                      <p><strong>PIN Sblocco:</strong> {pinSblocco}</p>
                    </div>
                  )}

                  {/* Note */}
                  <div>
                    <label className="block text-sm font-medium mb-1">Note (opzionali)</label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              )}

              {/* Bottoni navigazione */}
              <div className="flex justify-between mt-6 pt-4 border-t">
                <Button
                  variant="secondary"
                  type="button"
                  onClick={() => {
                    if (currentStep === 1) {
                      setShowModal(false);
                      resetForm();
                    } else {
                      setCurrentStep(currentStep - 1);
                    }
                  }}
                >
                  {currentStep === 1 ? 'Annulla' : 'Indietro'}
                </Button>
                <Button
                  variant="primary"
                  onClick={() => {
                    if (currentStep === 1) {
                      if (destinationType === 'person' && !selectedPersonId) {
                        alert('Seleziona una persona');
                        return;
                      }
                      if (destinationType === 'location' && !selectedLocationId) {
                        alert('Seleziona una locazione');
                        return;
                      }
                    }
                    if (currentStep === 2) {
                      if (assignmentType === 'riconsegna' && returnedItems.length === 0) {
                        alert('Seleziona almeno un materiale da ritirare');
                        return;
                      }
                      if (assignmentType === 'sostituzione' && (returnedItems.length === 0 || selectedItems.length === 0)) {
                        alert('Seleziona materiale da ritirare E da assegnare');
                        return;
                      }
                      if ((assignmentType === 'assegnazione' || assignmentType === 'rinnovo') && selectedItems.length === 0) {
                        alert('Seleziona almeno un materiale da assegnare');
                        return;
                      }
                    }
                    if (currentStep === 3 && assignmentType !== 'sostituzione' && assignmentType !== 'riconsegna') {
                      if (!password || !pinSim || !pinSblocco) {
                        alert('Compila tutti i campi delle credenziali');
                        return;
                      }
                    }
                    if (currentStep === 4 || (currentStep === 3 && (assignmentType === 'sostituzione' || assignmentType === 'riconsegna'))) {
                      handleSubmit();
                    } else {
                      setCurrentStep(currentStep + 1);
                    }
                  }}
                >
                  {(currentStep === 4 || (currentStep === 3 && (assignmentType === 'sostituzione' || assignmentType === 'riconsegna'))) ? 'Conferma Assegnazione' : 'Avanti'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Dettagli */}
        {showDetailsModal && selectedAssignment && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">Dettagli Assegnazione</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-medium text-gray-700">Persona:</span>
                    <p>{selectedAssignment.person_name}</p>
                    {selectedAssignment.person_email && <p className="text-sm text-gray-600">{selectedAssignment.person_email}</p>}
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Data Assegnazione:</span>
                    <p>{new Date(selectedAssignment.assignment_date).toLocaleDateString('it-IT')}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Tipo:</span>
                    <p className="capitalize">{selectedAssignment.assignment_type}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Stato:</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border inline-block ${
                      selectedAssignment.status === 'attivo' 
                        ? 'bg-green-50 text-green-700 border-green-200' 
                        : 'bg-gray-50 text-gray-700 border-gray-200'
                    }`}>
                      {selectedAssignment.status}
                    </span>
                  </div>
                  {selectedAssignment.return_date && (
                    <div>
                      <span className="font-medium text-gray-700">Data Riconsegna:</span>
                      <p>{new Date(selectedAssignment.return_date).toLocaleDateString('it-IT')}</p>
                    </div>
                  )}
                  {selectedAssignment.creator_name && (
                    <div>
                      <span className="font-medium text-gray-700">Creato da:</span>
                      <p>{selectedAssignment.creator_name}</p>
                    </div>
                  )}
                </div>

                {selectedAssignment.notes && (
                  <div>
                    <span className="font-medium text-gray-700">Note:</span>
                    <p className="text-gray-600 mt-1">{selectedAssignment.notes}</p>
                  </div>
                )}

                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Items Assegnati ({selectedAssignment.items.length})</h3>
                  <div className="border border-gray-300 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-100 sticky top-0 z-10">
                        <tr>
                          <th className="px-4 py-2 text-left">Tipo</th>
                          <th className="px-4 py-2 text-left">Descrizione</th>
                          <th className="px-4 py-2 text-center">Quantità</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedAssignment.items.map((item) => (
                          <tr key={item.id} className="border-t">
                            <td className="px-4 py-2 capitalize">{item.item_type}</td>
                            <td className="px-4 py-2">{item.item_description}</td>
                            <td className="px-4 py-2 text-center">{item.quantity}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6 pt-4 border-t">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowDetailsModal(false);
                    setSelectedAssignment(null);
                  }}
                >
                  Chiudi
                </Button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
