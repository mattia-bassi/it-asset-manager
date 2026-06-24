import { useState, useEffect } from 'react';
import api from '../api';
import Button from '../components/Button';
import ChangePasswordForm from '../components/ChangePasswordForm';
import { auth } from '../auth';
import { Cog6ToothIcon } from '@heroicons/react/24/outline';
import AssetTypesTab from './settings/AssetTypesTab';
import LocationsTab from './settings/LocationsTab';
import UsersTab from './settings/UsersTab';
import LetterheadTab from './settings/LetterheadTab';
import AuditLogsTab from './settings/AuditLogsTab';
import ComplianceTab from './settings/ComplianceTab';
import GdprTab from './settings/GdprTab';

// Importa i contenuti che erano pagine separate
// (li integreremo come componenti interni)

export default function Settings() {
  const currentUser = auth.getUser();
  const isUser = currentUser?.role === 'user';
  const [activeTab, setActiveTab] = useState<'letterhead' | 'asset-types' | 'locations' | 'users' | 'audit-logs' | 'account' | 'gdpr' | 'compliance'>(
    isUser ? 'account' : 'letterhead'
  );

  useEffect(() => {
    if (isUser && activeTab !== 'account' && activeTab !== 'gdpr') {
      setActiveTab('account');
    }
  }, [isUser, activeTab]);

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
        {/* HEADER MODERNO */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-gray-600 to-gray-800 rounded-xl flex items-center justify-center shadow-lg">
              <Cog6ToothIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-800">Impostazioni</h1>
              <p className="text-sm text-gray-600 mt-1">Gestisci le configurazioni dell'applicazione e del tuo account</p>
            </div>
          </div>
        </div>

        {/* TAB NAVIGATION MODERNA */}
        <div className="mb-8 border-b-2 border-gray-200">
          <nav className="flex space-x-2">
            {!isUser && (
              <button
                onClick={() => setActiveTab('letterhead')}
                className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                  activeTab === 'letterhead'
                    ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                📄 Carta Intestata
              </button>
            )}
            {!isUser && (
              <button
                onClick={() => setActiveTab('asset-types')}
                className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                  activeTab === 'asset-types'
                    ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                📑 Tipologie
              </button>
            )}
            {!isUser && (
              <button
                onClick={() => setActiveTab('locations')}
                className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                  activeTab === 'locations'
                    ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                📍 Locazioni
              </button>
            )}
            {!isUser && currentUser?.role === 'admin' && (
              <button
                onClick={() => setActiveTab('users')}
                className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                  activeTab === 'users'
                    ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                👥 Utenti
              </button>
            )}
            {!isUser && currentUser?.role === 'admin' && (
              <button
                onClick={() => setActiveTab('audit-logs')}
                className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                  activeTab === 'audit-logs'
                    ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                📋 Audit Logs
              </button>
            )}
            {!isUser && currentUser?.role === 'admin' && (
              <button
                onClick={() => setActiveTab('compliance')}
                className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                  activeTab === 'compliance'
                    ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                🛡️ Compliance
              </button>
            )}
            <button
              onClick={() => setActiveTab('account')}
              className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                activeTab === 'account'
                  ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              👤 Account
            </button>
            <button
              onClick={() => setActiveTab('gdpr')}
              className={`py-3 px-6 border-b-2 font-semibold text-sm transition-all ${
                activeTab === 'gdpr'
                  ? 'border-yellow-400 text-gray-800 bg-yellow-50'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              📋 I miei dati
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeTab === 'letterhead' ? (
          <LetterheadTab />
        ) : activeTab === 'asset-types' ? (
          <AssetTypesTab />
        ) : activeTab === 'locations' ? (
          <LocationsTab currentUserRole={currentUser?.role || ''} />
        ) : activeTab === 'users' ? (
          <UsersTab />
        ) : activeTab === 'audit-logs' ? (
          <AuditLogsTab />
        ) : activeTab === 'compliance' ? (
          <ComplianceTab />
        ) : activeTab === 'account' ? (
          <div className="space-y-6">
            {/* Cambio Password */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🔒 Cambio Password</h3>
              <ChangePasswordForm />
            </div>
          </div>
        ) : activeTab === 'gdpr' ? (
          <GdprTab />
        ) : null}
    </div>
  );
}

