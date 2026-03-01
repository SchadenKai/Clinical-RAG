import { useState, useCallback, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { AgentId } from '@/lib/agents-config';
import { MessageProps } from '@/components/chat/message-bubble';
import { apiClient } from '@/lib/api-client';
import { useChatSessions } from '@/hooks/use-chat-sessions';

export function useChatSession(initialSessionId?: string, initialAgent: AgentId = 'general') {
  const router = useRouter();
  const { addSession } = useChatSessions();

  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId);
  const [activeAgent, setActiveAgent] = useState<AgentId>(initialAgent);
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * When sendMessage creates a brand-new session, we hold the session ID in
   * this ref so the loadSession effect can skip the API fetch — we already
   * have the messages in local state and the chat POST is still in flight.
   * Once navigation completes and the new page mounts fresh, this ref is gone
   * (it belongs to the old component instance), so loadSession runs normally.
   */
  const skipLoadForSession = useRef<string | undefined>(undefined);

  // Sync internal sessionId when the route-level chatId prop changes
  useEffect(() => {
    setSessionId(initialSessionId);
  }, [initialSessionId]);

  // Load chat session messages whenever sessionId is set (e.g. after navigation)
  useEffect(() => {
    async function loadSession() {
      if (!sessionId) {
        setMessages([]);
        setActiveAgent(initialAgent);
        return;
      }

      // Skip the fetch if sendMessage just created this session — we already
      // have the user message in local state and the chat POST is still in flight.
      if (skipLoadForSession.current === sessionId) {
        return;
      }

      setIsLoading(true);
      try {
        const data = await apiClient.getSessionMessages(sessionId);
        setMessages(
          data.messages.map((m: any) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            agentId: m.agent_id as AgentId,
          }))
        );
        if (data.messages.length > 0) {
          const lastAgentId = data.messages[data.messages.length - 1].agent_id;
          if (lastAgentId) setActiveAgent(lastAgentId as AgentId);
        }
      } catch (e) {
        console.error('Failed to load session messages:', e);
      } finally {
        setIsLoading(false);
      }
    }
    loadSession();
  }, [sessionId, initialAgent]);

  const sendMessage = useCallback(
    async (content: string) => {
      // ① Push user message immediately (optimistic UI)
      const userMessage: MessageProps = { id: Date.now().toString(), role: 'user', content };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      // Track whether a new session was created in this call
      let newlyCreatedId: string | undefined;

      try {
        let currentSessionId = sessionId;

        // ② Create a session if none exists yet
        if (!currentSessionId) {
          const sessionTitle = content.trim() ? (content.length > 50 ? `${content.substring(0, 50)}...` : content) : 'New Chat';
          const session = await apiClient.createChatSession(sessionTitle);
          const newId: string = session.session_id;
          currentSessionId = newId;
          newlyCreatedId = newId;

          // Tell the loadSession effect to skip the fetch for this session —
          // we already have the user message locally and the chat is in flight.
          skipLoadForSession.current = newId;

          // Sync sessionId state so the loadSession effect fires but is skipped (see above)
          setSessionId(newId);

          // Add to sidebar immediately so it highlights right away
          addSession({ session_id: newId, title: session.title ?? sessionTitle });
        }

        // ③ Call the chat agent — isLoading stays true the entire time
        const response = await apiClient.chat(activeAgent, content, currentSessionId);

        // ④ Append the AI response to local state
        const aiMessage: MessageProps = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          agentId: activeAgent,
        };
        setMessages((prev) => [...prev, aiMessage]);

        // ⑤ Now that we have the full response, navigate to the new session URL.
        //    We do this AFTER the chat response so the component is still mounted
        //    when setMessages fires — avoiding any lost-state race conditions.
        if (newlyCreatedId) {
          // Clear the skip flag before navigating — the new page instance won't
          // have this ref anyway, but clearing it keeps the logic tidy.
          skipLoadForSession.current = undefined;
          router.replace(`/chat/${newlyCreatedId}`);
        }
      } catch (error) {
        console.error('Failed to send message:', error);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: 'An error occurred while sending your message. Please try again.',
            agentId: activeAgent,
          },
        ]);
        // Still navigate on error so the user lands on the session page
        if (newlyCreatedId) {
          skipLoadForSession.current = undefined;
          router.replace(`/chat/${newlyCreatedId}`);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [activeAgent, sessionId, router, addSession]
  );

  const resetSession = useCallback(() => {
    setSessionId(undefined);
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    activeAgent,
    setActiveAgent,
    sessionId,
    resetSession,
  };
}
