/**
 * REST client for the chat agent CRUD API.
 *
 * Mirrors the lightweight `fetch`-based style of `agui-client.ts`: typed
 * inputs, explicit error handling, typed results. Consumed via the TanStack
 * Query hooks in `hooks/use-agents.ts`.
 */

import { API_ENDPOINTS } from './constants';

export interface Agent {
  id: string;
  name: string;
  description: string;
  prompt: string;
  pipeline: string;
  created_at: string;
  updated_at: string;
}

export interface AgentCreateInput {
  name: string;
  description?: string;
  prompt?: string;
}

export type AgentUpdateInput = Partial<AgentCreateInput>;

export interface AgentDeleteResponse {
  status: string;
  message: string;
}

const agentsUrl = `${API_ENDPOINTS.BASE_URL}${API_ENDPOINTS.AGENTS}`;
const agentUrl = (id: string): string =>
  `${API_ENDPOINTS.BASE_URL}${API_ENDPOINTS.AGENT_DETAIL(id)}`;

function _formatDetail(detail: unknown): string | null {
  if (typeof detail === 'string') return detail;
  // FastAPI/Pydantic validation errors arrive as [{ loc, msg, type }, ...].
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        item && typeof item === 'object' && 'msg' in item
          ? String((item as { msg: unknown }).msg)
          : null,
      )
      .filter((m): m is string => Boolean(m));
    return messages.length ? messages.join('; ') : null;
  }
  return null;
}

async function _parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      message = _formatDetail(data?.detail) ?? message;
    } catch {
      // Response body was not JSON; keep the status-based message.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function listAgents(signal?: AbortSignal): Promise<Agent[]> {
  return _parse<Agent[]>(await fetch(agentsUrl, { signal }));
}

export async function getAgent(id: string, signal?: AbortSignal): Promise<Agent> {
  return _parse<Agent>(await fetch(agentUrl(id), { signal }));
}

export async function createAgent(input: AgentCreateInput): Promise<Agent> {
  return _parse<Agent>(
    await fetch(agentsUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }),
  );
}

export async function updateAgent(
  id: string,
  input: AgentUpdateInput,
): Promise<Agent> {
  return _parse<Agent>(
    await fetch(agentUrl(id), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }),
  );
}

export async function deleteAgent(id: string): Promise<AgentDeleteResponse> {
  return _parse<AgentDeleteResponse>(
    await fetch(agentUrl(id), { method: 'DELETE' }),
  );
}
