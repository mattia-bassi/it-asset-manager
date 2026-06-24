import React, { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import {
  CubeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DevicePhoneMobileIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import StatsCard from '../components/common/StatsCard';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'];

interface Overview {
  total_assets?: number;
  assets_assigned?: number;
  assets_available?: number;
  low_stock_items?: number;
  active_sims?: number;
  active_assignments?: number;
}

interface StatusItem {
  status: string;
  count: number;
}

interface TypeItem {
  type_name: string;
  count: number;
}

interface TimelineItem {
  date: string;
  count: number;
}

interface RecentAssignment {
  assignment_number: string;
  person_name: string;
  assignment_date: string | null;
  assignment_type: string;
}

interface LowStockItem {
  id: number;
  category: string;
  device: string;
  brand?: string | null;
  quantity: number;
  min_quantity: number;
}

interface AssetTypeOption {
  id: number;
  name: string;
}

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [overview, setOverview] = useState<Overview>({});
  const [assetsByStatus, setAssetsByStatus] = useState<StatusItem[]>([]);
  const [assetsByType, setAssetsByType] = useState<TypeItem[]>([]);
  const [assignmentsTimeline, setAssignmentsTimeline] = useState<TimelineItem[]>([]);
  const [recentAssignments, setRecentAssignments] = useState<RecentAssignment[]>([]);
  const [lowStockItems, setLowStockItems] = useState<LowStockItem[]>([]);

  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: '30',
    assetStatus: 'all',
    assetType: 'all',
    assignmentType: 'all',
    alertsOnly: false,
  });
  const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' });
  const [assetTypes, setAssetTypes] = useState<AssetTypeOption[]>([]);

  async function fetchAssetTypes() {
    try {
      const response = await api.get('/asset-types', {
        params: { level: 1, is_active: true },
      });
      const data = response.data;
      setAssetTypes(Array.isArray(data) ? data : (data?.items ?? []));
    } catch (error) {
      console.error('Errore fetch tipologie:', error);
    }
  }

  async function fetchData() {
    try {
      setLoading(true);

      const params = new URLSearchParams();
      if (filters.dateRange !== 'all') {
        if (filters.dateRange === 'custom') {
          if (customDateRange.start) params.append('date_from', customDateRange.start);
          if (customDateRange.end) params.append('date_to', customDateRange.end);
        } else {
          params.append('days', filters.dateRange);
        }
      }
      if (filters.assetStatus !== 'all') params.append('status', filters.assetStatus);
      if (filters.assetType !== 'all') params.append('asset_type_id', filters.assetType);
      if (filters.assignmentType !== 'all') params.append('assignment_type', filters.assignmentType);
      if (filters.alertsOnly) params.append('alerts_only', 'true');

      const queryString = params.toString();
      const suffix = queryString ? `?${queryString}` : '';

      const [overviewRes, byStatusRes, byTypeRes, timelineRes, recentRes] = await Promise.all([
        api.get(`/dashboard/overview${suffix}`),
        api.get(`/dashboard/assets-by-status${suffix}`),
        api.get(`/dashboard/assets-by-type${suffix}`),
        api.get(`/dashboard/assignments-timeline${suffix}`),
        api.get(`/dashboard/recent-assignments${suffix}`),
      ]);
      setOverview(overviewRes.data);
      setAssetsByStatus(Array.isArray(byStatusRes.data) ? byStatusRes.data : []);
      setAssetsByType(Array.isArray(byTypeRes.data) ? byTypeRes.data : []);
      setAssignmentsTimeline(Array.isArray(timelineRes.data) ? timelineRes.data : []);
      setRecentAssignments(Array.isArray(recentRes.data) ? recentRes.data : []);

      try {
        const lowStockRes = await api.get('/dashboard/low-stock-items');
        setLowStockItems(Array.isArray(lowStockRes.data) ? lowStockRes.data : []);
      } catch {
        setLowStockItems([]);
      }

      setLastUpdated(new Date().toLocaleString('it-IT'));
    } catch (error) {
      console.error('Errore fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAssetTypes();
    fetchData();
  }, []);

  const totalAssets = overview.total_assets ?? 0;
  const assetsAssigned = overview.assets_assigned ?? 0;
  const assignPct = totalAssets > 0 ? Math.round((assetsAssigned / totalAssets) * 100) : 0;
  const lowStockCount = overview.low_stock_items ?? 0;
  const activeSims = overview.active_sims ?? 0;
  const recentFive = recentAssignments.slice(0, 5);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="inline-block animate-spin rounded-full w-16 h-16 border-4 border-[#FFDD0F] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 overflow-x-hidden">
      <div className="w-full mx-auto px-6 py-6">
        {/* HEADER */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                <CubeIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold text-gray-800">Dashboard</h1>
                <p className="text-sm text-gray-600 mt-1">
                  Ultimo aggiornamento: {lastUpdated || '—'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
                showFilters
                  ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-300'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="w-5 h-5" />
              {showFilters ? 'Nascondi Filtri' : 'Mostra Filtri'}
            </button>
          </div>
        </div>

        {/* Pannello Filtri Collapsabile */}
        {showFilters && (
          <div className="mb-8 bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-700">Filtri Dashboard</h3>
              <button
                onClick={() => {
                  setFilters({
                    dateRange: '30',
                    assetStatus: 'all',
                    assetType: 'all',
                    assignmentType: 'all',
                    alertsOnly: false,
                  });
                  setCustomDateRange({ start: '', end: '' });
                }}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Reset Filtri
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ⏰ Periodo Temporale
                </label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="7">Ultimi 7 giorni</option>
                  <option value="30">Ultimi 30 giorni</option>
                  <option value="90">Ultimi 3 mesi</option>
                  <option value="180">Ultimi 6 mesi</option>
                  <option value="365">Ultimo anno</option>
                  <option value="custom">Personalizzato</option>
                </select>
                {filters.dateRange === 'custom' && (
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <input
                      type="date"
                      value={customDateRange.start}
                      onChange={(e) => setCustomDateRange({ ...customDateRange, start: e.target.value })}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                      placeholder="Da"
                    />
                    <input
                      type="date"
                      value={customDateRange.end}
                      onChange={(e) => setCustomDateRange({ ...customDateRange, end: e.target.value })}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                      placeholder="A"
                    />
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📦 Stato Asset
                </label>
                <select
                  value={filters.assetStatus}
                  onChange={(e) => setFilters({ ...filters, assetStatus: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="all">Tutti gli stati</option>
                  <option value="disponibile">Disponibili</option>
                  <option value="assegnato">Assegnati</option>
                  <option value="manutenzione">In Manutenzione</option>
                  <option value="riparazione">In Riparazione</option>
                  <option value="dismesso">Dismessi</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  💻 Tipologia Asset
                </label>
                <select
                  value={filters.assetType}
                  onChange={(e) => setFilters({ ...filters, assetType: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="all">Tutte le tipologie</option>
                  {assetTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📋 Tipo Assegnazione
                </label>
                <select
                  value={filters.assignmentType}
                  onChange={(e) => setFilters({ ...filters, assignmentType: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="all">Tutti i tipi</option>
                  <option value="assegnazione">Nuove Assegnazioni</option>
                  <option value="sostituzione">Sostituzioni</option>
                  <option value="riconsegna">Riconsegne</option>
                  <option value="rinnovo">Rinnovi</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ⚠️ Mostra Solo Alert
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.alertsOnly}
                    onChange={(e) => setFilters({ ...filters, alertsOnly: e.target.checked })}
                    className="w-5 h-5 text-yellow-500 border-gray-300 rounded focus:ring-yellow-500"
                  />
                  <span className="text-sm text-gray-600">
                    Evidenzia solo elementi critici
                  </span>
                </label>
              </div>

              <div className="flex items-end">
                <button
                  onClick={() => fetchData()}
                  className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-800 font-semibold px-4 py-2 rounded-lg transition"
                >
                  Applica Filtri
                </button>
              </div>
            </div>
          </div>
        )}

        {/* KPI CARDS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-10">
          <StatsCard
            title="Asset Totali"
            value={totalAssets}
            subtitle="Dispositivi tracciati"
            icon={CubeIcon}
            gradient="blue"
          />

          <StatsCard
            title="Assegnati"
            value={assetsAssigned}
            subtitle={`${assignPct}% del totale`}
            icon={CheckCircleIcon}
            gradient="green"
          />

          <StatsCard
            title="Alert Magazzino"
            value={lowStockCount}
            icon={ExclamationTriangleIcon}
            gradient="red"
            badge={{
              text: lowStockCount > 0 ? 'Attenzione' : 'Tutto OK',
              variant: lowStockCount > 0 ? 'warning' : 'success',
            }}
          />

          <StatsCard
            title="SIM Attive"
            value={activeSims}
            subtitle="Schede in uso"
            icon={DevicePhoneMobileIcon}
            gradient="purple"
          />
        </div>

        {/* SEZIONE GRAFICI */}
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            Distribuzione Asset
          </h2>
          <p className="text-gray-500 text-sm mt-1 ml-11">Panoramica dello stato e della tipologia degli asset</p>
        </div>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Asset per Status</h3>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={assetsByStatus} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="status" tick={{ fill: '#6B7280', fontSize: 12 }} />
                <YAxis tick={{ fill: '#6B7280', fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                  }}
                  cursor={{ fill: 'rgba(0, 0, 0, 0.04)' }}
                  formatter={(value: any) => [`${value} asset`, 'Quantità']}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]} animationDuration={800}>
                  {assetsByStatus.map((entry, index) => {
                    const barColors: Record<string, string> = {
                      disponibile: '#10B981',
                      assegnato: '#3B82F6',
                      manutenzione: '#F59E0B',
                      riparazione: '#EF4444',
                      dismesso: '#6B7280',
                    };
                    return <Cell key={`cell-${index}`} fill={barColors[entry.status] || '#FFDD0F'} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Asset per Tipologia</h3>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                layout="vertical"
                data={[...assetsByType].sort((a, b) => b.count - a.count)}
                margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="type_name" width={150} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                  }}
                  formatter={(value: any) => [`${value} asset`, 'Quantità']}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {[...assetsByType].sort((a, b) => b.count - a.count).map((_: any, i: number) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* TIMELINE */}
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
            Trend Temporale
          </h2>
          <p className="text-gray-500 text-sm mt-1 ml-11">Andamento delle assegnazioni negli ultimi 12 mesi</p>
        </div>

        <section className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 mb-10">
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={assignmentsTimeline} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#6B7280', fontSize: 11 }}
                tickFormatter={(value: string) => {
                  try {
                    const d = new Date(value);
                    return d.toLocaleDateString('it-IT', { month: 'short', year: '2-digit' });
                  } catch { return value; }
                }}
              />
              <YAxis tick={{ fill: '#6B7280', fontSize: 12 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                }}
                labelFormatter={(label: string) => {
                  try {
                    const d = new Date(label);
                    return d.toLocaleDateString('it-IT', { month: 'long', year: 'numeric' });
                  } catch { return label; }
                }}
                formatter={(value: any) => [`${value} assegnazioni`, 'Totale']}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#F59E0B"
                strokeWidth={3}
                dot={{ fill: '#F59E0B', r: 5, strokeWidth: 2, stroke: '#fff' }}
                activeDot={{ r: 7, fill: '#D97706', strokeWidth: 2, stroke: '#fff' }}
                animationDuration={800}
              />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* ATTIVITÀ RECENTI */}
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            Attività Recenti
          </h2>
          <p className="text-gray-500 text-sm mt-1 ml-11">Ultimi movimenti e alert di sistema</p>
        </div>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Ultime 5 Assegnazioni</h3>
            <div className="overflow-hidden">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gradient-to-r from-gray-50 to-gray-100">
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider w-32">N°</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Persona</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider w-32">Data</th>
                    <th className="px-6 py-4 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">Tipo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {recentFive.map((assignment, idx) => (
                    <tr key={idx} className="hover:bg-yellow-50 transition-colors duration-150">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {assignment.assignment_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-xs ${
                              idx % 4 === 0
                                ? 'bg-gradient-to-br from-yellow-400 to-orange-500'
                                : idx % 4 === 1
                                  ? 'bg-gradient-to-br from-green-400 to-emerald-500'
                                  : idx % 4 === 2
                                    ? 'bg-gradient-to-br from-blue-400 to-indigo-500'
                                    : 'bg-gradient-to-br from-purple-400 to-pink-500'
                            }`}
                          >
                            {(assignment.person_name || '')
                              .trim()
                              .split(/\s+/)
                              .filter((n) => n)
                              .map((n) => n[0])
                              .join('')
                              .toUpperCase()
                              .slice(0, 2)}
                          </div>
                          <span className="text-sm font-medium text-gray-900">{assignment.person_name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {assignment.assignment_date
                          ? new Date(assignment.assignment_date).toLocaleDateString('it-IT')
                          : '—'}
                      </td>
                      <td className="px-6 py-3">
                        <div className="flex justify-center">
                          <span
                            className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-base shadow-md hover:shadow-lg transition-all cursor-help ${
                              assignment.assignment_type === 'assegnazione'
                                ? 'bg-green-500 text-white'
                                : assignment.assignment_type === 'sostituzione'
                                  ? 'bg-blue-500 text-white'
                                  : assignment.assignment_type === 'riconsegna'
                                    ? 'bg-red-500 text-white'
                                    : 'bg-yellow-500 text-white'
                            }`}
                            title={
                              assignment.assignment_type === 'assegnazione'
                                ? 'Nuova Assegnazione'
                                : assignment.assignment_type === 'sostituzione'
                                  ? 'Sostituzione'
                                  : assignment.assignment_type === 'riconsegna'
                                    ? 'Riconsegna'
                                    : 'Rinnovo'
                            }
                          >
                            {assignment.assignment_type === 'assegnazione'
                              ? '✓'
                              : assignment.assignment_type === 'sostituzione'
                                ? '⟳'
                                : assignment.assignment_type === 'riconsegna'
                                  ? '↩'
                                  : '↻'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {recentFive.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                        Nessuna assegnazione recente
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">Materiali Sotto Soglia</h3>
            <div className="space-y-3">
              {lowStockItems.length > 0 ? (
                lowStockItems.map((item, idx) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg hover:bg-red-100 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
                        <ExclamationTriangleIcon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">
                          {item.category} - {item.device}
                        </p>
                        {item.brand && <p className="text-xs text-gray-600">{item.brand}</p>}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="inline-flex items-center gap-2 bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                        {item.quantity} / {item.min_quantity}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center p-8 bg-green-50 border-2 border-green-200 rounded-lg">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-3">
                      <CheckCircleIcon className="w-10 h-10 text-white" />
                    </div>
                    <p className="text-green-800 font-semibold">✓ Tutto OK</p>
                    <p className="text-green-600 text-sm">Nessun materiale sotto soglia</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dashboard;
