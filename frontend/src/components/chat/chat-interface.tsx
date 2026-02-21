'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { useChatSession } from '@/hooks/use-chat-session';
import { MessageBubble, ChatDocument } from './message-bubble';
import { MessageInput } from './message-input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { FileText, ExternalLink, XIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import db from '@/lib/dummy-db.json';

export function ChatInterface() {
  const params = useParams();
  const chatId = typeof params?.id === 'string' ? params.id : undefined;
  const { messages, isLoading, sendMessage, activeAgent, setActiveAgent } = useChatSession(chatId);
  const [input, setInput] = React.useState('');
  const [selectedDocument, setSelectedDocument] = React.useState<ChatDocument | null>(null);
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
    <div className="flex w-full h-full overflow-hidden bg-background relative">
      <div 
        className={cn(
          "flex flex-col h-full min-h-0 relative transition-all duration-300 ease-in-out shrink-0",
          selectedDocument ? "w-full md:w-[60%] lg:w-[65%] xl:w-[70%] border-r border-border/60 hidden md:flex" : "w-full"
        )}
      >
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
              <MessageBubble 
                key={msg.id} 
                message={msg} 
                onDocumentClick={setSelectedDocument}
              />
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

      {/* Document Sidebar (Side-by-side) */}
      {selectedDocument && (
        <div className="absolute md:static inset-0 z-20 flex flex-col w-full md:w-[40%] lg:w-[35%] xl:w-[30%] h-full bg-muted/5 animate-in slide-in-from-right-8 duration-300 shrink-0 shadow-2xl md:shadow-none">
          <div className="p-4 sm:p-5 border-b border-border/60 shrink-0 bg-background/80 backdrop-blur-md flex flex-col gap-2 relative">
            <button 
              onClick={() => setSelectedDocument(null)}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground p-1.5 rounded-md hover:bg-muted transition-colors bg-background border shadow-sm"
              title="Close sidebar"
            >
              <XIcon className="w-4 h-4" />
            </button>
            <h3 className="flex items-center gap-2 text-base font-semibold text-foreground pr-8">
              <FileText className="w-4 h-4 text-primary" />
              Document Reference
            </h3>
            <div className="flex items-center justify-between mt-1">
              <span className="font-medium text-sm text-muted-foreground truncate mr-3" title={selectedDocument.source}>
                {selectedDocument.source}
              </span>
              <a 
                href={`#`} 
                className="flex items-center gap-1 text-xs text-primary hover:underline whitespace-nowrap shrink-0"
                onClick={(e) => { e.preventDefault(); alert("Open original document features would go here"); }}
              >
                <ExternalLink className="w-3 h-3" /> View
              </a>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-background/50 custom-scrollbar">
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p className="text-muted-foreground mb-4 text-xs font-medium uppercase tracking-wider">
                Referenced Excerpt
              </p>
              
              {/* Highlight container */}
              <div 
                key={selectedDocument.id} // Re-animate if document changes
                ref={(el) => {
                  if (el) {
                    el.classList.add('bg-primary/20');
                    setTimeout(() => el.classList.remove('bg-primary/20'), 1500);
                  }
                }} 
                className="p-4 rounded-xl bg-primary/5 border border-primary/20 transition-colors duration-1000 shadow-sm"
              >
                <p className="whitespace-pre-wrap leading-relaxed text-[13px] sm:text-sm text-foreground">
                  {selectedDocument.text}
                </p>
              </div>
              
              <div className="mt-8 pt-4 border-t text-[10px] text-muted-foreground flex justify-between uppercase tracking-wider font-medium">
                <span>Relevance Score: {selectedDocument.score?.toFixed(1) || 'N/A'}</span>
                <span>ID: {selectedDocument.id}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
