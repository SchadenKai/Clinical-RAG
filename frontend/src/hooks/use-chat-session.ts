import { useState, useCallback, useEffect } from 'react';
import { AgentId } from '@/lib/agents-config';
import { MessageProps } from '@/components/chat/message-bubble';
import db from '@/lib/dummy-db.json';

// Mock hook for chat session. Real implementation would use TanStack Query/Mutations
export function useChatSession(chatId?: string, initialAgent: AgentId = 'general') {
  const [activeAgent, setActiveAgent] = useState<AgentId>(initialAgent);
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load chat session if a chatId is provided
  useEffect(() => {
    if (chatId) {
      const history = db.chatHistory.find((c) => c.id === chatId);
      if (history) {
        setMessages(history.messages as MessageProps[]);
        setActiveAgent((history.agentId as AgentId) || initialAgent);
        return;
      }
    }
    // Fallback/Default for new chats
    setMessages([]);
    setActiveAgent(initialAgent);
  }, [chatId, initialAgent]);

  const sendMessage = useCallback(
    async (content: string) => {
      // 1. Add user message
      const userMessage: MessageProps = {
        id: Date.now().toString(),
        role: 'user',
        content,
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      // 2. Simulate API call
      setTimeout(() => {
        const aiMessage: MessageProps = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `This is a mock response from the ${
            activeAgent === 'clinical_rag' ? 'Clinical Guidelines Agent' : 'General Assistant'
          }.\n\nI received your message: "${content}"`,
          agentId: activeAgent,
        };
        setMessages((prev) => [...prev, aiMessage]);
        setIsLoading(false);
      }, 1500);
    },
    [activeAgent]
  );

  return {
    messages,
    isLoading,
    sendMessage,
    activeAgent,
    setActiveAgent,
  };
}
