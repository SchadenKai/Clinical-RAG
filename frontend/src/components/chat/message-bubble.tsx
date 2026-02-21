import * as React from 'react';
import { cn } from '@/lib/utils';
import { AgentId } from '@/lib/agents-config';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface MessageProps {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentId?: AgentId;
}

export function MessageBubble({ message }: { message: MessageProps }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex w-full max-w-3xl mx-auto justify-end mb-4">
        <div className="bg-muted max-w-[85%] sm:max-w-[75%] rounded-3xl px-5 py-3 text-foreground leading-relaxed shadow-sm">
          <div className="prose prose-slate dark:prose-invert max-w-none text-base font-sans break-words prose-p:my-1 prose-pre:my-1">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-3xl mx-auto items-start mb-6">
      <div className="flex-1 space-y-2 overflow-hidden px-1">
        <div className="prose prose-slate dark:prose-invert max-w-none text-base font-sans leading-relaxed tracking-tight break-words">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
