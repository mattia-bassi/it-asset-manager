import { useState, useEffect } from 'react';
import api, { getApiError } from '../../api';

interface GuideInfo {
  host_ip: string;
  project_path: string;
  ssh_user: string;
  ssh_command: string;
  test_command: string;
}

interface TestResult {
  category: string;
  name: string;
  status: string;
  detail: string;
}

interface ComplianceResults {
  date: string;
  version: string;
  app_url: string;
  operator: string;
  total_tests: number;
  passed: number;
  failed: number;
  compliance_status: string;
  tests: TestResult[];
  status?: string;
  message?: string;
}

export default function ComplianceTab() {
  const [results, setResults] = useState<ComplianceResults | null>(null);
  const [guide, setGuide] = useState<GuideInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState<string[]>([]);
  const [copied, setCopied] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [resResults, resGuide, resReports] = await Promise.all([
        api.get('/compliance/results'),
        api.get('/compliance/guide'),
        api.get('/compliance/reports'),
      ]);
      if (resResults.data && !resResults.data.status) {
        setResults(resResults.data);
      } else {
        setResults(null);
      }
      setGuide(resGuide.data);
      setReports(resReports.data.reports || []);
    } catch (error) {
      console.error('Errore caricamento dati compliance:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(label);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(label);
      setTimeout(() => setCopied(null), 2000);
    }
  };

  const downloadReport = async (filename: string) => {
    try {
      const response = await api.get(`/compliance/download-report/${filename}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Errore download report:', error);
      alert('Errore durante il download del report');
    }
  };

  const CopyButton = ({ text, label }: { text: string; label: string }) => (
    <button
      onClick={() => copyToClipboard(text, label)}
      className="ml-2 px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex-shrink-0"
      title="Copia negli appunti"
    >
      {copied === label ? 'Copiato' : 'Copia'}
    </button>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Controllo Conformita ISO 27001:2022
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Verifica la conformita del sistema tramite il container di audit esterno.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Caricamento...
            </>
          ) : (
            'Aggiorna Risultati'
          )}
        </button>
      </div>

      {/* Guida SSH */}
      {guide && guide.host_ip && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
          <h4 className="font-semibold text-gray-800 mb-3">
            Come eseguire il test di conformita
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Il test viene eseguito da un container Docker indipendente (principio ISO 27001 — separazione auditor/auditee).
            Apri un terminale e segui questi passaggi:
          </p>
          <div className="space-y-3">
            {/* Step 1: SSH */}
            <div>
              <div className="flex items-center gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                <span className="text-sm text-gray-700">Collegati al server:</span>
                <code className="flex-1 bg-gray-800 text-green-400 px-3 py-1.5 rounded text-sm font-mono">
                  {`ssh <utente>@${guide.host_ip}`}
                </code>
                <CopyButton text={`ssh <utente>@${guide.host_ip}`} label="ssh" />
              </div>
              <p className="text-xs text-gray-500 mt-1 ml-8">
                Sostituisci {'<utente>'} con il tuo nome utente SSH del server.
              </p>
            </div>
            {/* Step 2: Run test */}
            <div className="flex items-center gap-2">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <span className="text-sm text-gray-700">Lancia il test:</span>
              <code className="flex-1 bg-gray-800 text-green-400 px-3 py-1.5 rounded text-sm font-mono">
                {guide.test_command}
              </code>
              <CopyButton text={guide.test_command} label="test" />
            </div>
            {/* Step 3 */}
            <div>
              <div className="flex items-center gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
                <span className="text-sm text-gray-700">
                  Attendi ~90 secondi, poi clicca <strong>"Aggiorna Risultati"</strong> qui sopra.
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-2 ml-8">
                Nota: al primo avvio, il sistema costruirà il container di test.
                L&apos;operazione potrebbe richiedere qualche minuto in più.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Risultati */}
      {results && (
        <>
          {/* Box Riepilogo */}
          <div className={`rounded-lg p-6 border-2 ${
            results.compliance_status === 'CONFORME'
              ? 'bg-green-50 border-green-500'
              : 'bg-red-50 border-red-500'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h4 className={`text-2xl font-bold ${
                  results.compliance_status === 'CONFORME' ? 'text-green-700' : 'text-red-700'
                }`}>
                  {results.compliance_status === 'CONFORME' ? 'CONFORME' : 'NON CONFORME'}
                </h4>
                <p className="text-gray-600 mt-1">
                  {results.passed}/{results.total_tests} test superati
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Eseguito il: {new Date(results.date).toLocaleString('it-IT')}
                </p>
                {results.operator && (
                  <p className="text-sm text-gray-500">
                    Operatore: {results.operator}
                  </p>
                )}
              </div>
              {reports.length > 0 && (
                <button
                  onClick={() => downloadReport(reports[0])}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors flex items-center gap-2"
                >
                  Scarica Report PDF
                </button>
              )}
            </div>
          </div>

          {/* Dettaglio Test per Categoria */}
          <div className="space-y-4">
            {(() => {
              const categories: string[] = [
                ...new Set(results.tests.map((t) => t.category)),
              ] as string[];
              return categories.map((category) => {
                const categoryTests = results.tests.filter(
                  (t) => t.category === category
                );
                const allPassed = categoryTests.every(
                  (t) => t.status === 'PASS'
                );
                return (
                  <div
                    key={category}
                    className="bg-white border rounded-lg overflow-hidden"
                  >
                    <div
                      className={`px-4 py-3 font-semibold text-sm flex items-center justify-between ${
                        allPassed
                          ? 'bg-green-50 text-green-800'
                          : 'bg-red-50 text-red-800'
                      }`}
                    >
                      <span>
                        {allPassed ? '\u2705' : '\u274c'} {category}
                      </span>
                      <span className="text-xs">
                        {
                          categoryTests.filter((t) => t.status === 'PASS')
                            .length
                        }
                        /{categoryTests.length}
                      </span>
                    </div>
                    <div className="divide-y divide-gray-100">
                      {categoryTests.map((test, idx) => (
                        <div
                          key={idx}
                          className="px-4 py-2 flex items-center justify-between text-sm"
                        >
                          <span className="text-gray-700">{test.name}</span>
                          <div className="flex items-center gap-2">
                            {test.detail && (
                              <span className="text-xs text-gray-400">
                                {test.detail}
                              </span>
                            )}
                            <span
                              className={
                                test.status === 'PASS'
                                  ? 'text-green-600 font-semibold'
                                  : 'text-red-600 font-semibold'
                              }
                            >
                              {test.status === 'PASS' ? '\u2713' : '\u2717'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </>
      )}

      {/* Stato vuoto */}
      {!results && !loading && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
          <p className="text-gray-500 text-lg">Nessun test eseguito</p>
          <p className="text-gray-400 text-sm mt-2">
            Segui la guida sopra per lanciare il primo test di conformita.
          </p>
        </div>
      )}
    </div>
  );
}
