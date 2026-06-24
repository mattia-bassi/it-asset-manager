import { useState, useEffect } from 'react';
import api, { getApiError } from '../../api';

export default function AuditLogsTab() {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditPage, setAuditPage] = useState(1);
  const [auditFilters, setAuditFilters] = useState({
    action: '',
    entity_type: '',
    username: '',
    date_from: '',
    date_to: ''
  });

  useEffect(() => {
    fetchAuditLogs(1);
  }, [auditFilters]);

  const fetchAuditLogs = async (page: number = 1) => {
    try {
      setAuditLoading(true);
      const limit = 50;
      const skip = (page - 1) * limit;

      const params = new URLSearchParams();
      params.append('skip', skip.toString());
      params.append('limit', limit.toString());

      if (auditFilters.action) params.append('action', auditFilters.action);
      if (auditFilters.entity_type) params.append('entity_type', auditFilters.entity_type);
      if (auditFilters.username) params.append('username', auditFilters.username);
      if (auditFilters.date_from) params.append('date_from', auditFilters.date_from);
      if (auditFilters.date_to) params.append('date_to', auditFilters.date_to);

      const response = await api.get(`/audit-logs?${params.toString()}`);
      setAuditLogs(response.data.items);
      setAuditTotal(response.data.total);
      setAuditPage(page);
    } catch (error) {
      console.error('Errore caricamento audit logs:', error);
      alert('Errore nel caricamento dei log di audit');
    } finally {
      setAuditLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Audit Logs</h2>
        <p className="text-gray-600 mt-2">
          Registro completo delle operazioni effettuate nel sistema
        </p>
      </div>

      {/* Filtri */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Azione</label>
          <select
            value={auditFilters.action}
            onChange={(e) => setAuditFilters({ ...auditFilters, action: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
          >
            <option value="">Tutte</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="DELETE">DELETE</option>
            <option value="LOGIN">LOGIN</option>
            <option value="LOGIN_FAILED">LOGIN_FAILED</option>
            <option value="CHANGE_PASSWORD">CHANGE_PASSWORD</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Entità</label>
          <select
            value={auditFilters.entity_type}
            onChange={(e) => setAuditFilters({ ...auditFilters, entity_type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
          >
            <option value="">Tutte</option>
            <option value="user">User</option>
            <option value="asset">Asset</option>
            <option value="person">Person</option>
            <option value="assignment">Assignment</option>
            <option value="sim">SIM</option>
            <option value="badge">Badge</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            type="text"
            value={auditFilters.username}
            onChange={(e) => setAuditFilters({ ...auditFilters, username: e.target.value })}
            placeholder="Cerca username..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Data da</label>
          <input
            type="date"
            value={auditFilters.date_from}
            onChange={(e) => setAuditFilters({ ...auditFilters, date_from: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Data a</label>
          <input
            type="date"
            value={auditFilters.date_to}
            onChange={(e) => setAuditFilters({ ...auditFilters, date_to: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
          />
        </div>
      </div>

      {/* Reset filtri */}
      <div className="mb-6">
        <button
          onClick={() => setAuditFilters({ action: '', entity_type: '', username: '', date_from: '', date_to: '' })}
          className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Reset Filtri
        </button>
      </div>

      {/* Tabella Audit Logs */}
      {auditLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
          <p className="mt-4 text-gray-600">Caricamento log...</p>
        </div>
      ) : auditLogs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">Nessun log trovato</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data/Ora</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Azione</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entità</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dettagli</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.created_at).toLocaleString('it-IT')}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {log.username || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        log.action === 'CREATE' ? 'bg-green-100 text-green-800' :
                        log.action === 'UPDATE' ? 'bg-blue-100 text-blue-800' :
                        log.action === 'DELETE' ? 'bg-red-100 text-red-800' :
                        log.action === 'LOGIN' ? 'bg-purple-100 text-purple-800' :
                        log.action === 'LOGIN_FAILED' ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {log.entity_type}
                      {log.entity_id && ` #${log.entity_id}`}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-md truncate">
                      {log.details}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {log.ip_address || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginazione */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Mostrando {((auditPage - 1) * 50) + 1} - {Math.min(auditPage * 50, auditTotal)} di {auditTotal} log
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => fetchAuditLogs(auditPage - 1)}
                disabled={auditPage === 1}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Precedente
              </button>
              <button
                onClick={() => fetchAuditLogs(auditPage + 1)}
                disabled={auditPage * 50 >= auditTotal}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Successivo
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
