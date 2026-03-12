import { AguiEvent } from './agui-types';
import { API_ENDPOINTS } from './constants';

export interface StreamChatParams {
  query: string;
  agentId: 'general' | 'clinical_rag';
  systemPrompt?: string;
  isLlmEnabled?: boolean;
}

export async function* streamChat(
  params: StreamChatParams,
  signal?: AbortSignal,
): AsyncGenerator<AguiEvent> {
  const url = `${API_ENDPOINTS.BASE_URL}/chat/stream`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: params.query,
      agent_id: params.agentId,
      system_prompt: params.systemPrompt ?? 'You are a helpful assistant',
      is_llm_enabled: params.isLlmEnabled ?? true,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines: "data: {...}\n\n"
    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';

    for (const part of parts) {
      const trimmed = part.trim();
      if (!trimmed.startsWith('data: ')) continue;
      const json = trimmed.slice(6);
      try {
        const event: AguiEvent = JSON.parse(json);
        yield event;
      } catch {
        console.warn('Failed to parse AGUI event:', json);
      }
    }
  }
}
