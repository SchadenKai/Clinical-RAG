import { useState, useCallback, useEffect, useRef } from 'react';
import { AgentId } from '@/lib/agents-config';
import { MessageProps, ChatDocument } from '@/components/chat/message-bubble';
import { StepProgress } from '@/components/chat/agent-steps';
import { applyPatch, Operation } from 'fast-json-patch';
import { streamChat } from '@/lib/agui-client';
import { CustomEvent as AguiCustomEvent } from '@/lib/agui-types';
import db from '@/lib/dummy-db.json';

export function useChatSession(chatId?: string, initialAgent: AgentId = 'general') {
  const [activeAgent, setActiveAgent] = useState<AgentId>(initialAgent);
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [steps, setSteps] = useState<StepProgress[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<unknown>(null);
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
      setStreamingContent('');
      setError(null);
      setSessionState(null);

      // Accumulate data for the assistant message
      let messageId = '';
      let fullContent = '';
      let documents: ChatDocument[] = [];
      let sources: string[] = [];

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
              messageId = event.messageId;
              break;

            case 'TEXT_MESSAGE_CONTENT':
              fullContent += event.delta;
              setStreamingContent(fullContent);
              break;

            case 'TEXT_MESSAGE_END':
              break;

            case 'CUSTOM': {
              const customEvt = event as AguiCustomEvent;
              if (customEvt.name === 'documents') {
                documents = (customEvt.value as Array<Record<string, unknown>>).map(
                  (doc, idx) => ({
                    id: (doc.id as number) ?? idx,
                    text: (doc.text as string) ?? '',
                    source: (doc.source as string) ?? '',
                    score: (doc.score as number) ?? 0,
                  }),
                );
              }
              if (customEvt.name === 'sources') {
                sources = customEvt.value as string[];
              }
              break;
            }

            case 'RUN_ERROR':
              setError(event.message);
              break;

            case 'RUN_FINISHED':
              break;

            case 'STATE_SNAPSHOT':
              setSessionState(event.snapshot);
              break;

            case 'STATE_DELTA':
              setSessionState((prev) => {
                const doc = structuredClone(prev ?? {}) as object;
                return applyPatch(doc, event.delta as Operation[]).newDocument;
              });
              break;
          }
        }

        // Add the completed assistant message
        if (fullContent) {
          const aiMessage: MessageProps = {
            id: messageId || (Date.now() + 1).toString(),
            role: 'assistant',
            content: fullContent,
            agentId: activeAgent,
            documents: documents.length > 0 ? documents : undefined,
            sources: sources.length > 0 ? sources : undefined,
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
    [activeAgent],
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
    streamingContent,
    error,
    sessionState,
    cancelStream,
  };
}
