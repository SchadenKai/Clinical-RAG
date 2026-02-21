import * as React from 'react';
import { SendHorizonal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { AgentSelector } from './agent-selector';
import { AgentId } from '@/lib/agents-config';

interface MessageInputProps {
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  activeAgent: AgentId;
  onAgentChange: (agent: AgentId) => void;
  mode?: 'fixed' | 'inline';
}

export function MessageInput({
  input,
  handleInputChange,
  onSubmit,
  isLoading,
  activeAgent,
  onAgentChange,
  mode = 'fixed',
}: MessageInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  React.useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        onSubmit(e);
      }
    }
  };

  return (
    <div 
      className={cn(
        mode === 'fixed' 
          ? "fixed bottom-0 left-0 lg:left-[calc(var(--sidebar-width))] right-0 p-4 pb-6 bg-background/95 backdrop-blur-sm z-50"
          : "w-full"
      )}
    >
      <div className="mx-auto max-w-3xl flex flex-col gap-3">
        {/* Agent Selector pinned just above the input for quick access */}
        <div className="flex items-center justify-between">
          <AgentSelector value={activeAgent} onChange={onAgentChange} />
          <div className="text-xs text-muted-foreground mr-2 font-mono hidden sm:block">
            Shift + Enter for new line
          </div>
        </div>

        <form
          onSubmit={onSubmit}
          className={cn(
            'relative flex w-full grow flex-col overflow-hidden bg-background rounded-2xl border border-border shadow-sm focus-within:ring-1 focus-within:ring-ring transition-shadow',
            isLoading && 'opacity-70'
          )}
        >
          <Textarea
            ref={textareaRef}
            tabIndex={0}
            onKeyDown={handleKeyDown}
            placeholder="Send a message..."
            className="min-h-[56px] w-full resize-none bg-transparent px-4 py-[1.2rem] focus-within:outline-none sm:text-sm border-0 focus-visible:ring-0 shadow-none leading-relaxed"
            autoFocus
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            name="message"
            rows={1}
            value={input}
            onChange={handleInputChange}
          />
          <div className="absolute right-0 top-1/2 -translate-y-1/2 pr-3">
            <Button
              type="submit"
              size="icon"
              disabled={isLoading || input.trim() === ''}
              className="h-8 w-8 rounded-full transition-all bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              <SendHorizonal className="h-4 w-4" />
              <span className="sr-only">Send message</span>
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
