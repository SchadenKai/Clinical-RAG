'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { useChatSession } from '@/hooks/use-chat-session';
import { MessageBubble } from './message-bubble';
import { MessageInput } from './message-input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import db from '@/lib/dummy-db.json';

export function ChatInterface() {
  const params = useParams();
  const chatId = typeof params?.id === 'string' ? params.id : undefined;
  const { messages, isLoading, sendMessage, activeAgent, setActiveAgent } = useChatSession(chatId);
  const [input, setInput] = React.useState('');
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput('');
  };

  // Auto-scroll to bottom
  React.useEffect(() => {
    if (scrollRef.current) {
      const scrollElement = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages, isLoading]);

  const isNewChat = messages.length === 0;

  // Function to format the user's display name based on their role
  const getDisplayName = () => {
    const { name, role } = db.user;
    const isDoctor = role.toLowerCase().includes('doctor') || role.toLowerCase().includes('chief medical officer');
    
    if (isDoctor) {
      const lastName = name.split(' ').slice(1).join(' ');
      return lastName ? `Dr. ${lastName}` : `Dr. ${name}`;
    }
    
    // For nurses, admins, or other roles, just use their first name or full name
    return name.split(' ')[0] || name;
  };

  return (
    <div className="flex flex-col flex-1 h-full min-h-0 relative">
      {isNewChat ? (
        <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
          <div className="flex flex-col p-4 max-w-3xl mx-auto w-full min-h-full justify-center pb-20 pt-[10vh]">
            <div className="w-full flex flex-col gap-2 mb-8 px-4">
              <h1 className="text-2xl sm:text-3xl font-medium text-foreground flex items-center gap-2">
                <span className="text-xl">🩺</span> 
                {getDisplayName()}
              </h1>
              <h2 className="text-4xl sm:text-5xl font-semibold tracking-tight text-muted-foreground">
                How can I assist with your clinical queries?
              </h2>
            </div>
            
            <div className="w-full">
              <MessageInput
                input={input}
                handleInputChange={handleInputChange}
                onSubmit={handleSubmit}
                isLoading={isLoading}
                activeAgent={activeAgent}
                onAgentChange={setActiveAgent}
                mode="inline"
              />
              <div className="flex flex-wrap gap-2 mt-4 justify-center sm:justify-center px-4">
                {db.promptTemplates.map((suggestion) => (
                  <Button
                    key={suggestion.label}
                    variant="secondary"
                    className="rounded-full bg-secondary/50 hover:bg-secondary text-sm px-4 shadow-sm border border-border/50 transition-colors"
                    onClick={() => {
                      if (!isLoading) {
                        setInput(suggestion.prompt || suggestion.label);
                      }
                    }}
                    disabled={isLoading}
                  >
                    <span className="mr-2 text-base">{suggestion.icon}</span>
                    <span className="font-medium text-muted-foreground">{suggestion.label}</span>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <ScrollArea className="flex-1 min-h-0 w-full pb-36" ref={scrollRef}>
          <div className="flex flex-col gap-2 py-8 px-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && (
              <div className="max-w-3xl mx-auto w-full px-1 py-4">
                <div className="flex items-center gap-2 text-muted-foreground animate-pulse">
                  <div className="w-2 h-2 rounded-full bg-primary/40" />
                  <div className="w-2 h-2 rounded-full bg-primary/40 animation-delay-200" />
                  <div className="w-2 h-2 rounded-full bg-primary/40 animation-delay-400" />
                  <span className="text-sm ml-2">Agent is thinking...</span>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      )}

      {!isNewChat && (
        <MessageInput
          input={input}
          handleInputChange={handleInputChange}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          activeAgent={activeAgent}
          onAgentChange={setActiveAgent}
          mode="fixed"
        />
      )}
    </div>
  );
}
