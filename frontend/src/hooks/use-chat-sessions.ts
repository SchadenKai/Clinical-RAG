'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export interface ChatSession {
  session_id: string;
  title: string;
  created_at?: string;
}

export const CHAT_SESSIONS_KEY = ['chat-sessions'] as const;

/**
 * Fetches and manages the list of chat sessions from the API.
 * Uses react-query so the sidebar and the hook stay in sync automatically.
 */
export function useChatSessions() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: CHAT_SESSIONS_KEY,
    queryFn: async () => {
      const result = await apiClient.getChatSessions();
      // The backend GET /sessions returns { sessions: [{ id, title, ... }] }
      // Normalise to { session_id, title } so all downstream code is consistent.
      const raw: any[] = result.sessions ?? result ?? [];
      return raw.map((s) => ({
        session_id: s.session_id ?? s.id,
        title: s.title,
        created_at: s.created_at,
      })) as ChatSession[];
    },
    staleTime: 30_000,
  });

  /**
   * Optimistically prepend a newly created session so the sidebar
   * updates immediately without a round-trip.
   */
  const addSession = (session: ChatSession) => {
    queryClient.setQueryData<ChatSession[]>(CHAT_SESSIONS_KEY, (prev = []) =>
      [session, ...prev.filter((s) => s.session_id !== session.session_id)]
    );
  };

  const deleteSession = useMutation({
    mutationFn: (sessionId: string) => apiClient.deleteChatSession(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.setQueryData<ChatSession[]>(CHAT_SESSIONS_KEY, (prev) =>
        prev ? prev.filter((s) => s.session_id !== sessionId) : []
      );
    },
  });

  const updateSession = useMutation({
    mutationFn: ({ sessionId, title }: { sessionId: string; title: string }) =>
      apiClient.updateChatSession(sessionId, title),
    onSuccess: (data, { sessionId, title }) => {
      queryClient.setQueryData<ChatSession[]>(CHAT_SESSIONS_KEY, (prev) =>
        prev
          ? prev.map((s) =>
              s.session_id === sessionId ? { ...s, title: data.title || title } : s
            )
          : []
      );
    },
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_KEY });

  return {
    sessions: data ?? [],
    isLoading,
    addSession,
    deleteSession,
    updateSession,
    refresh,
  };
}
