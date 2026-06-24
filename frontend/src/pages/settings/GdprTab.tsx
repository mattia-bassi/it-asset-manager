import { useState } from 'react';
import api, { getApiError } from '../../api';
import { ArrowDownTrayIcon, DocumentDuplicateIcon, TrashIcon, LockClosedIcon, PencilSquareIcon } from '@heroicons/react/24/outline';

export default function GdprTab() {
  const [gdprData, setGdprData] = useState<any>(null);
  const [gdprLoading, setGdprLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showRestrictionModal, setShowRestrictionModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [restrictionReason, setRestrictionReason] = useState('');
  const [restrictionType, setRestrictionType] = useState<'temporary' | 'permanent'>('temporary');
  const [showRectificationModal, setShowRectificationModal] = useState(false);
  const [rectificationData, setRectificationData] = useState({
    person_first_name: '',
    person_last_name: '',
    person_email: '',
    person_phone: '',
    reason: ''
  });

  // Funzione per export dati personali (Art. 15)
  const handleExportMyData = async () => {
    setGdprLoading(true);
    try {
      const response = await api.get('/gdpr/my-data');
      setGdprData(response.data);

      // Download automatico JSON
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `my-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert('Dati esportati con successo!');
    } catch (error) {
      console.error('Errore export dati:', error);
      alert('Errore durante export dati');
    } finally {
      setGdprLoading(false);
    }
  };

  // Funzione per portabilità dati (Art. 20)
  const handleDataPortability = async () => {
    setGdprLoading(true);
    try {
      const response = await api.get('/gdpr/data-portability');

      // Download JSON portabile
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `data-portability-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert('Dati esportati in formato portabile!');
    } catch (error) {
      console.error('Errore portabilità dati:', error);
      alert('Errore durante export portabilità');
    } finally {
      setGdprLoading(false);
    }
  };

  // Funzione per cancellazione account (Art. 17)
  const handleDeleteAccount = async () => {
    if (!deleteReason.trim()) {
      alert('Inserire motivazione richiesta');
      return;
    }

    setGdprLoading(true);
    try {
      await api.delete('/gdpr/erasure', {
        data: {
          reason: deleteReason,
          confirm_deletion: true
        }
      });

      alert('Account cancellato con successo. Verrai disconnesso.');
      // Logout
      localStorage.removeItem('token');
      window.location.href = '/login';
    } catch (error) {
      console.error('Errore cancellazione account:', error);
      alert('Errore durante cancellazione account');
    } finally {
      setGdprLoading(false);
      setShowDeleteModal(false);
    }
  };

  // Funzione per rettifica dati personali (Art. 16)
  const handleRectification = async () => {
    if (!rectificationData.reason.trim()) {
      alert('Inserire motivazione richiesta');
      return;
    }
    const hasAtLeastOneField = rectificationData.person_first_name.trim() ||
      rectificationData.person_last_name.trim() ||
      rectificationData.person_email.trim() ||
      rectificationData.person_phone.trim();
    if (!hasAtLeastOneField) {
      alert('Compila almeno un campo da correggere (Nome, Cognome, Email o Telefono)');
      return;
    }

    setGdprLoading(true);
    try {
      const payload = {
        person_first_name: rectificationData.person_first_name.trim() || undefined,
        person_last_name: rectificationData.person_last_name.trim() || undefined,
        person_email: rectificationData.person_email.trim() || undefined,
        person_phone: rectificationData.person_phone.trim() || undefined,
        reason: rectificationData.reason.trim()
      };
      const response = await api.put('/gdpr/rectification', payload);
      const updated = response.data?.updated_fields || [];
      alert(`Rettifica completata con successo! Campi aggiornati: ${updated.length ? updated.join(', ') : 'nessuno'}`);
      setShowRectificationModal(false);
      setRectificationData({
        person_first_name: '',
        person_last_name: '',
        person_email: '',
        person_phone: '',
        reason: ''
      });
    } catch (error: unknown) {
      console.error('Errore rettifica dati:', error);
      alert(getApiError(error, 'Errore durante la rettifica dei dati'));
    } finally {
      setGdprLoading(false);
    }
  };

  // Funzione per limitazione trattamento (Art. 18)
  const handleRestriction = async () => {
    if (!restrictionReason.trim()) {
      alert('Inserire motivazione richiesta');
      return;
    }

    setGdprLoading(true);
    try {
      await api.post('/gdpr/restriction', {
        reason: restrictionReason,
        restriction_type: restrictionType
      });

      alert('Limitazione trattamento attivata. Il tuo account è stato disabilitato.');
      // Logout
      localStorage.removeItem('token');
      window.location.href = '/login';
    } catch (error) {
      console.error('Errore limitazione trattamento:', error);
      alert('Errore durante limitazione trattamento');
    } finally {
      setGdprLoading(false);
      setShowRestrictionModal(false);
    }
  };

  return (
    <>
      <div className="bg-white shadow-lg rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">Diritti GDPR</h3>
            <p className="text-sm text-gray-600 mb-4">
              In conformità al GDPR (Regolamento UE 2016/679), hai diritto di accedere,
              rettificare, cancellare e limitare il trattamento dei tuoi dati personali.
            </p>
          </div>

          {/* Art. 15 - Diritto di Accesso */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2">
              <ArrowDownTrayIcon className="h-5 w-5 text-blue-600" />
              <h4 className="font-semibold">Export Dati Personali (Art. 15)</h4>
            </div>
            <p className="text-sm text-gray-600">
              Scarica una copia completa di tutti i tuoi dati personali in formato JSON.
            </p>
            <button
              onClick={handleExportMyData}
              disabled={gdprLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {gdprLoading ? 'Caricamento...' : 'Scarica i miei dati'}
            </button>
          </div>

          {/* Art. 20 - Portabilità */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2">
              <DocumentDuplicateIcon className="h-5 w-5 text-green-600" />
              <h4 className="font-semibold">Portabilità Dati (Art. 20)</h4>
            </div>
            <p className="text-sm text-gray-600">
              Scarica i tuoi dati in formato strutturato e machine-readable per trasferirli ad altro sistema.
            </p>
            <button
              onClick={handleDataPortability}
              disabled={gdprLoading}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {gdprLoading ? 'Caricamento...' : 'Export portabile'}
            </button>
          </div>

          {/* Art. 16 - Rettifica Dati Personali */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2">
              <PencilSquareIcon className="h-5 w-5 text-yellow-600" />
              <h4 className="font-semibold">Rettifica Dati Personali (Art. 16)</h4>
            </div>
            <p className="text-sm text-gray-600">
              Correggi dati personali inesatti o incompleti associati al tuo account.
            </p>
            <button
              onClick={() => setShowRectificationModal(true)}
              disabled={gdprLoading}
              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
            >
              Richiedi rettifica
            </button>
          </div>

          {/* Art. 18 - Limitazione Trattamento */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2">
              <LockClosedIcon className="h-5 w-5 text-orange-600" />
              <h4 className="font-semibold">Limitazione Trattamento (Art. 18)</h4>
            </div>
            <p className="text-sm text-gray-600">
              Richiedi la limitazione del trattamento dei tuoi dati (disabilita account temporaneamente o permanentemente).
            </p>
            <button
              onClick={() => setShowRestrictionModal(true)}
              disabled={gdprLoading}
              className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
            >
              Richiedi limitazione
            </button>
          </div>

          {/* Art. 17 - Cancellazione */}
          <div className="border rounded-lg p-4 space-y-3 bg-red-50">
            <div className="flex items-center gap-2">
              <TrashIcon className="h-5 w-5 text-red-600" />
              <h4 className="font-semibold text-red-900">Cancellazione Account (Art. 17 - Right to be Forgotten)</h4>
            </div>
            <p className="text-sm text-red-700">
              ⚠️ ATTENZIONE: Questa azione è irreversibile. Il tuo account verrà anonimizzato e non potrai più accedere al sistema.
            </p>
            <button
              onClick={() => setShowDeleteModal(true)}
              disabled={gdprLoading}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
            >
              Cancella il mio account
            </button>
          </div>
        </div>
      </div>

      {/* Modale Cancellazione Account */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-red-900">Conferma Cancellazione Account</h3>
            <p className="text-sm text-gray-600 mb-4">
              Sei sicuro di voler cancellare il tuo account? Questa azione è <strong>irreversibile</strong>.
              I tuoi dati verranno anonimizzati per compliance legale.
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Motivazione richiesta *</label>
              <textarea
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                placeholder="Inserisci il motivo della cancellazione (obbligatorio)"
                className="w-full border rounded px-3 py-2 h-24"
                required
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2 border rounded hover:bg-gray-50"
              >
                Annulla
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={!deleteReason.trim() || gdprLoading}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                Conferma Cancellazione
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modale Limitazione Trattamento */}
      {showRestrictionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Richiesta Limitazione Trattamento</h3>
            <p className="text-sm text-gray-600 mb-4">
              La limitazione del trattamento disabiliterà il tuo account. Non potrai più accedere finché la limitazione è attiva.
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Tipo limitazione</label>
              <select
                value={restrictionType}
                onChange={(e) => setRestrictionType(e.target.value as 'temporary' | 'permanent')}
                className="w-full border rounded px-3 py-2"
              >
                <option value="temporary">Temporanea</option>
                <option value="permanent">Permanente</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Motivazione richiesta *</label>
              <textarea
                value={restrictionReason}
                onChange={(e) => setRestrictionReason(e.target.value)}
                placeholder="Inserisci il motivo della limitazione (obbligatorio)"
                className="w-full border rounded px-3 py-2 h-24"
                required
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowRestrictionModal(false)}
                className="flex-1 px-4 py-2 border rounded hover:bg-gray-50"
              >
                Annulla
              </button>
              <button
                onClick={handleRestriction}
                disabled={!restrictionReason.trim() || gdprLoading}
                className="flex-1 px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
              >
                Conferma Limitazione
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modale Rettifica Dati Personali */}
      {showRectificationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Richiesta Rettifica Dati Personali</h3>
            <p className="text-sm text-gray-600 mb-4">
              Compila solo i campi che desideri correggere. I campi lasciati vuoti non verranno modificati.
            </p>
            <div className="space-y-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nome</label>
                <input
                  type="text"
                  value={rectificationData.person_first_name}
                  onChange={(e) => setRectificationData({ ...rectificationData, person_first_name: e.target.value })}
                  placeholder="Nome (opzionale)"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Cognome</label>
                <input
                  type="text"
                  value={rectificationData.person_last_name}
                  onChange={(e) => setRectificationData({ ...rectificationData, person_last_name: e.target.value })}
                  placeholder="Cognome (opzionale)"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="text"
                  value={rectificationData.person_email}
                  onChange={(e) => setRectificationData({ ...rectificationData, person_email: e.target.value })}
                  placeholder="Email (opzionale)"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Telefono</label>
                <input
                  type="text"
                  value={rectificationData.person_phone}
                  onChange={(e) => setRectificationData({ ...rectificationData, person_phone: e.target.value })}
                  placeholder="Telefono (opzionale)"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Motivazione della rettifica *</label>
                <textarea
                  value={rectificationData.reason}
                  onChange={(e) => setRectificationData({ ...rectificationData, reason: e.target.value })}
                  placeholder="Inserisci la motivazione (obbligatorio)"
                  className="w-full border rounded px-3 py-2 h-24"
                  required
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowRectificationModal(false);
                  setRectificationData({
                    person_first_name: '',
                    person_last_name: '',
                    person_email: '',
                    person_phone: '',
                    reason: ''
                  });
                }}
                className="flex-1 px-4 py-2 border rounded hover:bg-gray-50"
              >
                Annulla
              </button>
              <button
                onClick={handleRectification}
                disabled={!rectificationData.reason.trim() || gdprLoading}
                className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
              >
                Conferma Rettifica
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
