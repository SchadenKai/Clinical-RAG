import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export interface LLMSettings {
  provider: string;
  model_name: string;
  api_key: string;
}

export interface EmbeddingSettings {
  provider: string;
  model_name: string;
  api_key: string;
}

export function useSettings() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLLMSettings = async (): Promise<LLMSettings | null> => {
    try {
      setLoading(true);
      setError(null);
      return await apiClient.getLLMSettings();
    } catch (err: any) {
      setError(err.message || 'Failed to fetch LLM settings');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const fetchEmbeddingSettings = async (): Promise<EmbeddingSettings | null> => {
    try {
      setLoading(true);
      setError(null);
      return await apiClient.getEmbeddingSettings();
    } catch (err: any) {
      setError(err.message || 'Failed to fetch embedding settings');
      return null;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    fetchLLMSettings,
    fetchEmbeddingSettings,
  };
}
