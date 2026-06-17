/**
 * TanStack Query hooks for chat agents.
 *
 * A single query key (`['agents']`) backs the list; every mutation invalidates
 * it so the management page and the chat agent selector stay in sync.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  Agent,
  AgentCreateInput,
  AgentUpdateInput,
  createAgent,
  deleteAgent,
  listAgents,
  updateAgent,
} from '@/lib/agents-api';

const AGENTS_QUERY_KEY = ['agents'] as const;

export function useAgents() {
  return useQuery<Agent[]>({
    queryKey: AGENTS_QUERY_KEY,
    queryFn: ({ signal }) => listAgents(signal),
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AgentCreateInput) => createAgent(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEY }),
  });
}

export function useUpdateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: AgentUpdateInput }) =>
      updateAgent(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEY }),
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteAgent(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEY }),
  });
}
