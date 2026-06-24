import { useState, useEffect } from 'react';
import api, { getApiError } from '../../api';
import axios from 'axios';
import Button from '../../components/Button';

interface DocumentTemplate {
  id: number;
  name: string;
  description: string | null;
  logo_path: string | null;
  footer_path: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const BASE_URL = '';

export default function LetterheadTab() {
  const [template, setTemplate] = useState<DocumentTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [uploadingFooter, setUploadingFooter] = useState(false);
  const [removingLogo, setRemovingLogo] = useState(false);
  const [removingFooter, setRemovingFooter] = useState(false);

  useEffect(() => {
    fetchDefaultTemplate();
  }, []);

  const fetchDefaultTemplate = async () => {
    try {
      setLoading(true);
      const response = await api.get('/document-templates/default');
      setTemplate(response.data);
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        // Nessun template predefinito trovato - è normale
        setTemplate(null);
      } else {
        console.error('Errore caricamento template:', error);
        alert(getApiError(error, 'Errore nel caricamento del template predefinito'));
      }
    } finally {
      setLoading(false);
    }
  };

  const validateImageFile = (file: File): string | null => {
    // Verifica dimensione (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      return 'Il file deve essere inferiore a 2MB';
    }

    // Verifica formato
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      return 'Formato non supportato. Usa PNG, JPG o JPEG';
    }

    return null;
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validazione client-side
    const validationError = validateImageFile(file);
    if (validationError) {
      alert(validationError);
      e.target.value = ''; // Reset input
      return;
    }

    if (!template) {
      alert('Nessun template configurato');
      return;
    }

    try {
      setUploadingLogo(true);
      const formData = new FormData();
      formData.append('file', file);

      await api.post(
        `/document-templates/${template.id}/upload-logo`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      alert('Logo caricato con successo');
      await fetchDefaultTemplate();
    } catch (error: unknown) {
      console.error('Errore upload logo:', error);
      alert(getApiError(error, 'Errore durante il caricamento del logo'));
    } finally {
      setUploadingLogo(false);
      e.target.value = ''; // Reset input
    }
  };

  const handleFooterUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validazione client-side
    const validationError = validateImageFile(file);
    if (validationError) {
      alert(validationError);
      e.target.value = ''; // Reset input
      return;
    }

    if (!template) {
      alert('Nessun template configurato');
      return;
    }

    try {
      setUploadingFooter(true);
      const formData = new FormData();
      formData.append('file', file);

      await api.post(
        `/document-templates/${template.id}/upload-footer`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      alert('Footer caricato con successo');
      await fetchDefaultTemplate();
    } catch (error: unknown) {
      console.error('Errore upload footer:', error);
      alert(getApiError(error, 'Errore durante il caricamento del footer'));
    } finally {
      setUploadingFooter(false);
      e.target.value = ''; // Reset input
    }
  };

  const handleRemoveLogo = async () => {
    if (!template || !template.logo_path) return;

    if (!confirm('Rimuovere il logo?')) return;

    try {
      setRemovingLogo(true);
      await api.delete(`/document-templates/${template.id}/delete-logo`);
      alert('Logo rimosso con successo');
      await fetchDefaultTemplate();
    } catch (error: unknown) {
      console.error('Errore rimozione logo:', error);
      alert(getApiError(error, 'Errore durante la rimozione del logo'));
    } finally {
      setRemovingLogo(false);
    }
  };

  const handleRemoveFooter = async () => {
    if (!template || !template.footer_path) return;

    if (!confirm('Rimuovere il footer?')) return;

    try {
      setRemovingFooter(true);
      await api.delete(`/document-templates/${template.id}/delete-footer`);
      alert('Footer rimosso con successo');
      await fetchDefaultTemplate();
    } catch (error: unknown) {
      console.error('Errore rimozione footer:', error);
      alert(getApiError(error, 'Errore durante la rimozione del footer'));
    } finally {
      setRemovingFooter(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
        <p className="mt-4 text-gray-600">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Impostazioni Carta Intestata</h2>
        <p className="text-gray-600 mt-2">
          Configura logo e footer per i documenti di assegnazione
        </p>
      </div>

      {!template ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">
            Nessun template configurato. Contatta l'amministratore per configurare un template predefinito.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          
          {/* Sezione Upload */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Upload Logo */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-base font-semibold text-gray-800 mb-3">📄 Logo Intestazione</h3>
              <label className="cursor-pointer flex items-center justify-center px-4 py-2 bg-asset-manager-yellow text-asset-manager-gray rounded-lg hover:bg-asset-manager-yellow-hover transition-colors shadow-md">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                {uploadingLogo ? 'Caricamento...' : 'Carica Logo'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  onChange={handleLogoUpload}
                  disabled={uploadingLogo}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2 text-center">Max 2MB (PNG, JPG)</p>
              {template.logo_path && (
                <Button
                  variant="destructive"
                  icon="🗑️"
                  onClick={handleRemoveLogo}
                  disabled={removingLogo}
                  fullWidth
                  className="mt-3"
                >
                  {removingLogo ? 'Rimozione...' : 'Rimuovi Logo'}
                </Button>
              )}
            </div>

            {/* Upload Footer */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-base font-semibold text-gray-800 mb-3">📄 Footer Piè di Pagina</h3>
              <label className="cursor-pointer flex items-center justify-center px-4 py-2 bg-asset-manager-yellow text-asset-manager-gray rounded-lg hover:bg-asset-manager-yellow-hover transition-colors shadow-md">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                {uploadingFooter ? 'Caricamento...' : 'Carica Footer'}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  onChange={handleFooterUpload}
                  disabled={uploadingFooter}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2 text-center">Max 2MB (PNG, JPG)</p>
              {template.footer_path && (
                <Button
                  variant="destructive"
                  icon="🗑️"
                  onClick={handleRemoveFooter}
                  disabled={removingFooter}
                  fullWidth
                  className="mt-3"
                >
                  {removingFooter ? 'Rimozione...' : 'Rimuovi Footer'}
                </Button>
              )}
            </div>

          </div>

          {/* SEZIONE ANTEPRIME - 3 Box Separati Responsive */}
          <div className="space-y-4">
            
            {/* Box Anteprima Logo */}
            <div className="bg-white border-4 border-asset-manager-yellow rounded-lg p-4">
              <h3 className="text-base font-semibold text-gray-800 mb-3">👁️ Anteprima Logo</h3>
              <div className="w-full h-36 border-2 border-gray-300 rounded-lg bg-gray-50 flex items-center justify-center">
                {template.logo_path ? (
                  <img
                    src={`${BASE_URL}${template.logo_path}?v=${new Date(template.updated_at).getTime()}`}
                    alt="Logo Preview"
                    className="object-contain p-2 w-full h-full"
                    onError={(e) => {
                      console.error('Errore caricamento logo');
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <span className="text-gray-400 text-sm">Nessun logo caricato</span>
                )}
              </div>
            </div>

            {/* Box Anteprima Footer */}
            <div className="bg-white border-4 border-asset-manager-yellow rounded-lg p-4">
              <h3 className="text-base font-semibold text-gray-800 mb-3">👁️ Anteprima Footer</h3>
              <div className="w-full h-32 border-2 border-gray-300 rounded-lg bg-gray-50 flex items-center justify-center">
                {template.footer_path ? (
                  <img
                    src={`${BASE_URL}${template.footer_path}?v=${new Date(template.updated_at).getTime()}`}
                    alt="Footer Preview"
                    className="object-contain p-2 w-full h-full"
                    onError={(e) => {
                      console.error('Errore caricamento footer');
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <span className="text-gray-400 text-sm">Nessun footer caricato</span>
                )}
              </div>
            </div>

            {/* Box Anteprima Documento Completo */}
            <div className="bg-white border-4 border-asset-manager-yellow rounded-lg p-4">
              <h3 className="text-base font-semibold text-gray-800 mb-3">📄 Anteprima Documento Completo</h3>
              <div className="w-full max-w-4xl mx-auto bg-white border-2 border-gray-300 rounded-lg overflow-hidden shadow-sm">
                
                {/* Header */}
                <div className="h-32 border-b border-gray-200 bg-gray-50 flex items-center justify-center">
                  {template.logo_path ? (
                    <img
                      src={`${BASE_URL}${template.logo_path}?v=${new Date(template.updated_at).getTime()}`}
                      alt="Logo"
                      className="object-contain p-2 w-full h-full"
                    />
                  ) : (
                    <span className="text-gray-400 text-xs">Logo Intestazione</span>
                  )}
                </div>

                {/* Corpo */}
                <div className="h-48 flex items-center justify-center bg-white">
                  <span className="text-gray-300 text-sm">Contenuto Documento</span>
                </div>

                {/* Footer */}
                <div className="h-24 border-t border-gray-200 bg-gray-50 flex items-center justify-center">
                  {template.footer_path ? (
                    <img
                      src={`${BASE_URL}${template.footer_path}?v=${new Date(template.updated_at).getTime()}`}
                      alt="Footer"
                      className="object-contain p-2 w-full h-full"
                    />
                  ) : (
                    <span className="text-gray-400 text-xs">Footer Piè di Pagina</span>
                  )}
                </div>
                
              </div>
              <p className="text-xs text-gray-500 text-center mt-3">
                Anteprima simulata del documento finale con logo e footer
              </p>
            </div>

          </div>

        </div>
      )}
    </div>
  );
}
