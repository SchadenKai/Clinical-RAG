import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export interface IndexingStatus {
  who?: { INDEXED?: number; PENDING?: number; INDEXING?: number; FAILED?: number };
  cdc?: { INDEXED?: number; PENDING?: number; INDEXING?: number; FAILED?: number };
  upload?: { INDEXED?: number; PENDING?: number; INDEXING?: number; FAILED?: number };
  web?: { INDEXED?: number; PENDING?: number; INDEXING?: number; FAILED?: number };
}

export function useIndexing() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<IndexingStatus>({});

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getOverallIndexingStatus();
      setStatus(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  };

  const triggerSearch = async (source: 'who' | 'cdc') => {
    try {
      setLoading(true);
      setError(null);
      await apiClient.triggerIndexing(source);
      await fetchStatus();
    } catch (err: any) {
      setError(err.message || `Failed to trigger ${source} indexing`);
    } finally {
      setLoading(false);
    }
  };

  return {
    status,
    loading,
    error,
    fetchStatus,
    triggerSearch
  };
}
