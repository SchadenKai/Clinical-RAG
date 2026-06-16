import { useState, useCallback, useEffect, useRef } from 'react';
import { AgentId } from '@/lib/agents-config';
import { MessageProps, ChatDocument } from '@/components/chat/message-bubble';
import { StepProgress } from '@/components/chat/agent-steps';
import { ToolCallProgress } from '@/components/chat/tool-calls';
import { applyPatch, Operation } from 'fast-json-patch';
import { streamChat } from '@/lib/agui-client';
import {
  CustomEvent as AguiCustomEvent,
  ToolCallStartEvent,
  ToolCallArgsEvent,
  ToolCallEndEvent,
  ToolCallResultEvent,
} from '@/lib/agui-types';
import db from '@/lib/dummy-db.json';

/**
 * Normalises a raw document payload (custom-event value or session state) into
 * the ChatDocument shape the UI renders. Returns [] for non-array input.
 */
function _mapDocuments(raw: unknown): ChatDocument[] {
  if (!Array.isArray(raw)) return [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return raw.map((doc: any, idx: number) => ({
    id: typeof doc.id === 'number' ? doc.id : idx,
    text: doc.entity?.text || doc.text || '',
    source: doc.entity?.source || doc.source || doc.page_title || '',
    score: doc.score || doc.distance || 0,
  }));
}

export function useChatSession(chatId?: string, initialAgent: AgentId = 'general') {
  const [activeAgent, setActiveAgent] = useState<AgentId>(initialAgent);
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [steps, setSteps] = useState<StepProgress[]>([]);
  const [toolCalls, setToolCalls] = useState<ToolCallProgress[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<unknown>(null);
  const [documents, setDocuments] = useState<ChatDocument[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  // Load chat session history if chatId provided
  useEffect(() => {
    if (chatId) {
      const history = db.chatHistory.find((c) => c.id === chatId);
      if (history) {
        setMessages(history.messages as MessageProps[]);
        setActiveAgent((history.agentId as AgentId) || initialAgent);
        return;
      }
    }
    setMessages([]);
    setActiveAgent(initialAgent);
  }, [chatId, initialAgent]);

  const sendMessage = useCallback(
    async (content: string) => {
      // Abort any in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      // Add user message immediately
      const userMessage: MessageProps = {
        id: Date.now().toString(),
        role: 'user',
        content,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setSteps([]);
      setToolCalls([]);
      setStreamingContent('');
      setError(null);
      setSessionState(null);
      setDocuments([]);

      // Accumulate data for the assistant message
      let messageId = '';
      let fullContent = '';
      let localToolCalls: ToolCallProgress[] = [];
      let localDocuments: ChatDocument[] = [];
      let localSources: string[] = [];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let finalState: Record<string, any> | null = (sessionState as Record<string, any>) || null;

      try {
        for await (const event of streamChat(
          { query: content, agentId: activeAgent, isLlmEnabled: true },
          controller.signal,
        )) {
          switch (event.type) {
            case 'STEP_STARTED':
              setSteps((prev) => [
                ...prev.map((s) =>
                  s.status === 'active' ? { ...s, status: 'completed' as const } : s,
                ),
                { name: event.stepName, status: 'active' },
              ]);
              break;

            case 'STEP_FINISHED':
              setSteps((prev) =>
                prev.map((s) =>
                  s.name === event.stepName ? { ...s, status: 'completed' as const } : s,
                ),
              );
              break;

            case 'TEXT_MESSAGE_START':
              // A new message starts: reset the buffer so a regenerated answer
              // (citation/judge retries) replaces the previous in-progress text.
              messageId = event.messageId;
              fullContent = '';
              setStreamingContent('');
              break;

            case 'TEXT_MESSAGE_CONTENT':
              fullContent += event.delta;
              setStreamingContent(fullContent);
              break;

            case 'TEXT_MESSAGE_END':
              break;

            case 'TOOL_CALL_START': {
              const evt = event as ToolCallStartEvent;
              const toolCall: ToolCallProgress = {
                id: evt.toolCallId,
                name: evt.toolCallName,
                status: 'running',
                args: '',
              };
              localToolCalls = [...localToolCalls, toolCall];
              setToolCalls(localToolCalls);
              break;
            }

            case 'TOOL_CALL_ARGS': {
              const evt = event as ToolCallArgsEvent;
              localToolCalls = localToolCalls.map((tc) =>
                tc.id === evt.toolCallId ? { ...tc, args: tc.args + evt.delta } : tc,
              );
              setToolCalls(localToolCalls);
              break;
            }

            case 'TOOL_CALL_END': {
              const evt = event as ToolCallEndEvent;
              localToolCalls = localToolCalls.map((tc) =>
                tc.id === evt.toolCallId ? { ...tc, status: 'completed' as const } : tc,
              );
              setToolCalls(localToolCalls);
              break;
            }

            case 'TOOL_CALL_RESULT': {
              const evt = event as ToolCallResultEvent;
              localToolCalls = localToolCalls.map((tc) =>
                tc.id === evt.toolCallId
                  ? { ...tc, status: 'completed' as const, result: evt.content }
                  : tc,
              );
              setToolCalls(localToolCalls);
              break;
            }

            case 'CUSTOM': {
              const customEvt = event as AguiCustomEvent;
              if (customEvt.name === 'documents') {
                const docs = _mapDocuments(customEvt.value);
                localDocuments = docs;
                setDocuments(docs);
              }
              if (customEvt.name === 'sources') {
                localSources = customEvt.value as string[];
              }
              break;
            }

            case 'RUN_ERROR':
              setError(event.message);
              break;

            case 'RUN_FINISHED':
              break;

            case 'STATE_SNAPSHOT': {
              finalState = event.snapshot as typeof finalState;
              setSessionState(finalState);
              if (finalState?.documents && Array.isArray(finalState.documents)) {
                const docs = _mapDocuments(finalState.documents);
                localDocuments = docs;
                setDocuments(docs);
              }
              break;
            }

            case 'STATE_DELTA': {
              const doc = structuredClone(finalState ?? {}) as object;
              const newDoc = applyPatch(doc, event.delta as Operation[]).newDocument;
              finalState = newDoc as typeof finalState;
              setSessionState(finalState);
              if (finalState?.documents && Array.isArray(finalState.documents)) {
                const docs = _mapDocuments(finalState.documents);
                localDocuments = docs;
                setDocuments(docs);
              }
              break;
            }
          }
        }

        // Add the completed assistant message
        if (fullContent) {
          if (finalState?.sources && Array.isArray(finalState.sources) && localSources.length === 0) {
            localSources = finalState.sources;
          }

          const aiMessage: MessageProps = {
            id: messageId || (Date.now() + 1).toString(),
            role: 'assistant',
            content: fullContent,
            agentId: activeAgent,
            documents: localDocuments.length > 0 ? localDocuments : undefined,
            sources: localSources.length > 0 ? localSources : undefined,
            toolCalls: localToolCalls.length > 0 ? localToolCalls : undefined,
          };
          setMessages((prev) => [...prev, aiMessage]);
        }
      } catch (err: unknown) {
        if ((err as Error).name !== 'AbortError') {
          setError((err as Error).message ?? 'Stream failed');
        }
      } finally {
        setIsLoading(false);
        setStreamingContent('');
      }
    },
    [activeAgent, sessionState],
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
    setStreamingContent('');
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    activeAgent,
    setActiveAgent,
    steps,
    toolCalls,
    streamingContent,
    error,
    sessionState,
    cancelStream,
    documents,
  };
}
