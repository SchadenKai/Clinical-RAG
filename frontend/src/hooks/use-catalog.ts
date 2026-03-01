import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export interface CatalogDocument {
  id: string;
  source: string;
  filename: string;
  url?: string;
  status: string;
  indexed_at?: string;
}

export function useCatalog() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<CatalogDocument[]>([]);

  const fetchCatalog = async (source?: string, search?: string, status?: string, page = 1) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getCatalog(source, search, status, page);
      setDocuments(data.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch catalog');
    } finally {
      setLoading(false);
    }
  };

  return {
    documents,
    loading,
    error,
    fetchCatalog
  };
}
