import { useState, useEffect } from 'react';
import api, { getApiError } from '../api';
import Button from '../components/Button';
import type { Document } from '../types';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const ACCEPTED_EXTENSIONS = '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.txt';

interface UploadForm {
  name: string;
  category: string;
  description: string;
  file: File | null;
}

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<UploadForm>({
    name: '',
    category: '',
    description: '',
    file: null,
  });

  useEffect(() => {
    fetchDocuments();
  }, [search, categoryFilter]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params: Record<string, string | number> = {
        limit: 200,
      };
      if (search) params.search = search;
      if (categoryFilter) params.category = categoryFilter;
      const response = await api.get('/documents', { params });
      const items = response.data.items || [];
      setDocuments(items);
      if (!categoryFilter) {
        setCategories([...new Set(items.map((d: Document) => d.category).filter(Boolean))].sort() as string[]);
      }
    } catch (error) {
      console.error('Errore caricamento documenti:', error);
      alert('Errore nel caricamento dei documenti');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.file || !formData.name.trim() || !formData.category.trim()) {
      alert('Compila tutti i campi obbligatori (Nome, Categoria, File)');
      return;
    }
    try {
      setUploading(true);
      const fd = new FormData();
      fd.append('file', formData.file);
      fd.append('name', formData.name.trim());
      fd.append('category', formData.category.trim());
      if (formData.description.trim()) {
        fd.append('description', formData.description.trim());
      }
      await api.post('/documents/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setShowModal(false);
      resetForm();
      fetchDocuments();
    } catch (error: unknown) {
      console.error('Errore upload documento:', error);
      alert(getApiError(error, 'Errore nel caricamento del documento'));
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (doc: Document) => {
    try {
      const response = await api.get(`/documents/${doc.id}/download`, {
        responseType: 'blob',
      });
      const blob = response.data;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = doc.filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error: unknown) {
      console.error('Errore download:', error);
      alert(getApiError(error, 'Errore nel download del documento'));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Eliminare questo documento?')) return;
    try {
      await api.delete(`/documents/${id}`);
      fetchDocuments();
    } catch (error: unknown) {
      console.error('Errore eliminazione documento:', error);
      alert(getApiError(error, 'Errore nell\'eliminazione del documento'));
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      category: '',
      description: '',
      file: null,
    });
  };

  const handleCloseModal = () => {
    setShowModal(false);
    resetForm();
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 w-full mx-auto px-2 py-6">
      {/* HEADER */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 bg-gradient-to-br from-slate-400 to-slate-600 rounded-xl flex items-center justify-center shadow-lg">
            <span className="text-2xl">📄</span>
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Documenti</h1>
            <p className="text-sm text-gray-600 mt-1">Carica e gestisci i documenti aziendali</p>
          </div>
        </div>
        <div className="flex justify-end">
          <Button variant="primary" icon="📤" onClick={() => setShowModal(true)}>
            Carica Documento
          </Button>
        </div>
      </div>

      {/* Barra filtri */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        <input
          type="text"
          placeholder="Cerca per nome..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-asset-manager-yellow"
        >
          <option value="">Tutte le categorie</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
        <Button variant="primary" onClick={fetchDocuments}>
          Cerca
        </Button>
      </div>

      {/* Tabella */}
      {loading ? (
        <div className="text-center py-12 text-gray-600">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-asset-manager-yellow"></div>
          <p className="mt-2">Caricamento...</p>
        </div>
      ) : (
        <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
          <div className="overflow-x-auto">
            <table className="w-full divide-y divide-gray-200">
              <thead className="bg-asset-manager-gray text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Nome</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Categoria</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Dimensione</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Caricato da</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold">Data</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold">Azioni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-yellow-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{doc.name}</td>
                    <td className="px-6 py-4 text-gray-600">{doc.category}</td>
                    <td className="px-6 py-4 text-gray-600">{formatFileSize(doc.file_size)}</td>
                    <td className="px-6 py-4 text-gray-600">{doc.uploader_username || '-'}</td>
                    <td className="px-6 py-4 text-gray-600">{formatDate(doc.created_at)}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="secondary"
                          icon="⬇"
                          iconOnly
                          title="Scarica"
                          onClick={() => handleDownload(doc)}
                        />
                        <Button
                          variant="destructive"
                          icon="🗑"
                          iconOnly
                          title="Elimina"
                          onClick={() => handleDelete(doc.id)}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
                {documents.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      <div className="flex flex-col items-center">
                        <span className="text-4xl mb-2">📄</span>
                        <p className="text-lg font-medium">Nessun documento trovato</p>
                        <p className="text-sm mt-1">Carica un documento per iniziare</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal Upload */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-2xl">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Carica Documento</h2>
            <form onSubmit={handleUpload}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Nome *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Categoria *</label>
                  <input
                    type="text"
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    placeholder="es. Contratti, Manuali, ..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">
                    Descrizione (opzionale)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">File *</label>
                  <input
                    type="file"
                    required
                    accept={ACCEPTED_EXTENSIONS}
                    onChange={(e) =>
                      setFormData({ ...formData, file: e.target.files?.[0] || null })
                    }
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-asset-manager-yellow focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Formati: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, TXT (max 20MB)
                  </p>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
                <Button variant="secondary" type="button" onClick={handleCloseModal}>
                  Annulla
                </Button>
                <Button variant="primary" type="submit" disabled={uploading}>
                  {uploading ? 'Caricamento...' : 'Carica'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
