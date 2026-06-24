import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import { auth } from '../auth';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import {
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const CHART_COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16'];

interface Report {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
}

interface Overview {
  total_assets?: number;
  assets_assigned?: number;
  assets_available?: number;
  low_stock_items?: number;
  low_stock_count?: number;
  active_sims?: number;
  active_badges?: number;
}

interface ChartItem {
  name?: string;
  type_name?: string;
  status?: string;
  date?: string;
  month?: string;
  count: number;
}

interface Asset {
  id: number;
  site_id: number | null;
  site_name?: string | null;
}

interface Site {
  id: number;
  name: string;
}

export default function Reports() {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';

  const [overview, setOverview] = useState<Overview | null>(null);
  const [assetsByType, setAssetsByType] = useState<ChartItem[]>([]);
  const [assetsByStatus, setAssetsByStatus] = useState<ChartItem[]>([]);
  const [assignmentsTimeline, setAssignmentsTimeline] = useState<ChartItem[]>([]);
  const [assetsBySite, setAssetsBySite] = useState<ChartItem[]>([]);
  const [loadingCharts, setLoadingCharts] = useState(true);
  const [loadingExcel, setLoadingExcel] = useState<{ [key: string]: boolean }>({});
  const [error, setError] = useState<string | null>(null);

  const userReports: Report[] = [
    { id: 'my-assets', title: 'I Miei Asset', description: 'Lista completa degli asset attualmente assegnati a me', icon: '💼', color: 'bg-blue-50 border-blue-200' },
    { id: 'my-assignments', title: 'Storico Mie Assegnazioni', description: 'Cronologia completa di tutte le mie assegnazioni (attive e completate)', icon: '📋', color: 'bg-purple-50 border-purple-200' },
  ];

  const excelReports: Report[] = [
    { id: 'active-assignments', title: 'Assegnazioni Attive', description: '', icon: '📋', color: 'bg-green-50 border-green-200' },
    { id: 'low-stock', title: 'Inventario Sotto Soglia', description: '', icon: '📦', color: 'bg-orange-50 border-orange-200' },
    { id: 'sims-by-operator', title: 'SIM per Operatore', description: '', icon: '📱', color: 'bg-cyan-50 border-cyan-200' },
    { id: 'sims-by-status', title: 'SIM per Status', description: '', icon: '📊', color: 'bg-teal-50 border-teal-200' },
    { id: 'sims-detailed', title: 'SIM Dettagliato', description: '', icon: '🔐', color: 'bg-pink-50 border-pink-200' },
  ];

  const fetchAllData = async () => {
    if (isUser) {
      setLoadingCharts(false);
      setError(null);
      return;
    }
    setError(null);
    setLoadingCharts(true);
    try {
      const [overviewRes, byTypeRes, byStatusRes, timelineRes, assetsRes, sitesRes] = await Promise.all([
        api.get('/dashboard/overview'),
        api.get('/dashboard/assets-by-type'),
        api.get('/dashboard/assets-by-status'),
        api.get('/dashboard/assignments-timeline', { params: { days: 365 } }),
        api.get('/assets', { params: { limit: 500, is_active: true } }),
        api.get('/sites'),
      ]);

      setOverview(overviewRes.data);

      const byType = Array.isArray(byTypeRes.data) ? byTypeRes.data : [];
      setAssetsByType(byType);

      setAssetsByStatus(Array.isArray(byStatusRes.data) ? byStatusRes.data : []);

      const timeline = Array.isArray(timelineRes.data) ? timelineRes.data : [];
      const byMonth = timeline.reduce<Record<string, number>>((acc, x: ChartItem) => {
        const month = x.date ? x.date.substring(0, 7) : (x.month ?? '');
        if (month) acc[month] = (acc[month] || 0) + x.count;
        return acc;
      }, {});
      setAssignmentsTimeline(
        Object.entries(byMonth)
          .map(([month, count]) => ({ month, count }))
          .sort((a, b) => a.month.localeCompare(b.month))
          .slice(-12)
      );

      const assets: Asset[] = assetsRes.data?.items ?? [];
      const sites: Site[] = sitesRes.data?.items ?? [];
      const siteMap = Object.fromEntries(sites.map((s) => [s.id, s.name]));
      const siteCounts: Record<string, number> = {};
      assets.forEach((a) => {
        const sid = a.site_id;
        const name = sid ? (siteMap[sid] ?? `Sede ${sid}`) : 'Non assegnata';
        siteCounts[name] = (siteCounts[name] || 0) + 1;
      });
      setAssetsBySite(
        Object.entries(siteCounts)
          .map(([name, count]) => ({ name, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 8)
      );
    } catch (err) {
      console.error('Errore fetch report:', err);
      setError('Errore nel caricamento dati. Riprova.');
    } finally {
      setLoadingCharts(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleDownload = async (reportId: string) => {
    try {
      setLoadingExcel((prev) => ({ ...prev, [reportId]: true }));
      const response = await api.get(`/reports/${reportId}/excel`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      let filename = `report_${reportId}_${new Date().toISOString().split('T')[0]}.xlsx`;
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/i);
        if (match) filename = match[1];
      }
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      console.error('Errore download report:', err);
      alert(getApiError(err, 'Errore nel download del report'));
    } finally {
      setLoadingExcel((prev) => ({ ...prev, [reportId]: false }));
    }
  };

  const lowStockCount = overview?.low_stock_count ?? overview?.low_stock_items ?? 0;

  if (isUser) {
    return (
      <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <ChartBarIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Report e Statistiche</h1>
              <p className="text-sm text-gray-600 mt-1">Scarica i tuoi report personalizzati in formato Excel</p>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {userReports.map((report) => (
            <div key={report.id} className={`${report.color} border-2 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all`}>
              <div className="flex items-start justify-between mb-4">
                <div className="text-5xl">{report.icon}</div>
                <button
                  onClick={() => handleDownload(report.id)}
                  disabled={loadingExcel[report.id]}
                  className="px-4 py-2 bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-800 rounded-lg font-semibold hover:from-yellow-500 hover:to-yellow-600 shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingExcel[report.id] ? '⏳ Scarico...' : '📥 Download'}
                </button>
              </div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">{report.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{report.description}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
      {/* HEADER */}
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
            <ChartBarIcon className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Report e Statistiche</h1>
            <p className="text-sm text-gray-600 mt-1">Analisi visive e export Excel</p>
          </div>
        </div>
        <button
          onClick={fetchAllData}
          disabled={loadingCharts}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          🔄 Aggiorna
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between">
          <span className="text-red-700">{error}</span>
          <button onClick={fetchAllData} className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700">
            🔄 Riprova
          </button>
        </div>
      )}

      {/* SEZIONE KPI */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border-l-4 border-blue-500 rounded-xl p-5 shadow-md">
          <div className="text-3xl font-bold text-gray-800">{overview?.total_assets ?? '—'}</div>
          <div className="text-sm text-gray-600 mt-1">🖥️ Asset Totali</div>
        </div>
        <div className="bg-white border-l-4 border-green-500 rounded-xl p-5 shadow-md">
          <div className="text-3xl font-bold text-gray-800">{overview?.assets_available ?? '—'}</div>
          <div className="text-sm text-gray-600 mt-1">✅ Disponibili</div>
        </div>
        <div className="bg-white border-l-4 border-indigo-500 rounded-xl p-5 shadow-md">
          <div className="text-3xl font-bold text-gray-800">{overview?.assets_assigned ?? '—'}</div>
          <div className="text-sm text-gray-600 mt-1">📋 Assegnati</div>
        </div>
        <div className="bg-white border-l-4 border-orange-500 rounded-xl p-5 shadow-md">
          <div className="text-3xl font-bold text-gray-800">{lowStockCount}</div>
          <div className="text-sm text-gray-600 mt-1">⚠️ Sotto Soglia</div>
        </div>
      </div>

      {/* SEZIONE GRAFICI */}
      <h2 className="text-xl font-bold text-gray-800 mb-4">Analisi Visive</h2>
      {loadingCharts ? (
        <div className="flex justify-center items-center py-24">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* CARD 1 - Asset per Tipo */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
            <h3 className="text-lg font-bold text-gray-800 mb-1">Asset per Tipo</h3>
            <p className="text-sm text-gray-500 mb-3">Distribuzione per tipologia</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                layout="vertical"
                data={[...assetsByType].sort((a, b) => b.count - a.count)}
                margin={{ top: 0, right: 20, left: 10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="type_name" width={140} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {[...assetsByType].sort((a, b) => b.count - a.count).map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex justify-end mt-2">
              <button
                onClick={() => handleDownload('assets-by-type')}
                disabled={loadingExcel['assets-by-type']}
                className="px-3 py-1.5 text-sm bg-yellow-400 hover:bg-yellow-500 text-gray-800 rounded-lg font-medium disabled:opacity-50"
              >
                📥 Excel
              </button>
            </div>
          </div>

          {/* CARD 2 - Asset per Stato */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
            <h3 className="text-lg font-bold text-gray-800 mb-1">Asset per Stato</h3>
            <p className="text-sm text-gray-500 mb-3">Conteggio per stato</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={assetsByStatus} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="status" width={110} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex justify-end mt-2">
              <button
                onClick={() => handleDownload('faulty-assets')}
                disabled={loadingExcel['faulty-assets']}
                className="px-3 py-1.5 text-sm bg-yellow-400 hover:bg-yellow-500 text-gray-800 rounded-lg font-medium disabled:opacity-50"
              >
                📥 Excel
              </button>
            </div>
          </div>

          {/* CARD 3 - Trend Assegnazioni */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
            <h3 className="text-lg font-bold text-gray-800 mb-1">Trend Assegnazioni (12 mesi)</h3>
            <p className="text-sm text-gray-500 mb-3">Andamento mensile</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={assignmentsTimeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
            <div className="flex justify-end mt-2">
              <button
                onClick={() => handleDownload('assignment-history')}
                disabled={loadingExcel['assignment-history']}
                className="px-3 py-1.5 text-sm bg-yellow-400 hover:bg-yellow-500 text-gray-800 rounded-lg font-medium disabled:opacity-50"
              >
                📥 Excel
              </button>
            </div>
          </div>

          {/* CARD 4 - Asset per Sede */}
          <div className="bg-white border border-gray-200 rounded-xl shadow-md p-5">
            <h3 className="text-lg font-bold text-gray-800 mb-1">Asset per Sede</h3>
            <p className="text-sm text-gray-500 mb-3">Top 8 sedi</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={assetsBySite}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex justify-end mt-2">
              <button
                onClick={() => handleDownload('assets-by-site')}
                disabled={loadingExcel['assets-by-site']}
                className="px-3 py-1.5 text-sm bg-yellow-400 hover:bg-yellow-500 text-gray-800 rounded-lg font-medium disabled:opacity-50"
              >
                📥 Excel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SEZIONE EXPORT EXCEL */}
      <h2 className="text-xl font-bold text-gray-800 mb-4">📥 Export Excel</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {excelReports.map((report) => (
          <div key={report.id} className={`${report.color} border rounded-xl py-3 px-4 flex items-center justify-between`}>
            <span className="font-medium text-gray-800">{report.icon} {report.title}</span>
            <button
              onClick={() => handleDownload(report.id)}
              disabled={loadingExcel[report.id]}
              className="px-3 py-1.5 text-sm bg-yellow-400 hover:bg-yellow-500 text-gray-800 rounded-lg font-medium disabled:opacity-50"
            >
              ⬇ Scarica
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
