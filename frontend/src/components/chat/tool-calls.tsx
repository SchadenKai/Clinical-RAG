'use client';

import * as React from 'react';
import { Loader2, Wrench, Search, ListFilter, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ToolCallProgress {
  id: string;
  name: string;
  status: 'running' | 'completed';
  /** Accumulated JSON string of the tool arguments. */
  args: string;
  /** JSON string of the tool result, present once the call resolves. */
  result?: string;
}

interface ToolCallsProps {
  toolCalls: ToolCallProgress[];
  className?: string;
}

const TOOL_LABELS: Record<string, string> = {
  search_knowledge_base: 'Search knowledge base',
  rerank_documents: 'Rerank documents',
};

function _toolLabel(name: string): string {
  return TOOL_LABELS[name] ?? name.replace(/_/g, ' ');
}

function _toolIcon(name: string): React.ReactNode {
  if (name === 'search_knowledge_base') return <Search className="w-3.5 h-3.5" />;
  if (name === 'rerank_documents') return <ListFilter className="w-3.5 h-3.5" />;
  return <Wrench className="w-3.5 h-3.5" />;
}

/** Pretty-print a JSON string, falling back to the raw value on parse errors. */
function _formatJson(value?: string): string | null {
  if (!value) return null;
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}

function ToolCallCard({ toolCall }: { toolCall: ToolCallProgress }) {
  const [isOpen, setIsOpen] = React.useState(false);
  const args = _formatJson(toolCall.args);
  const result = _formatJson(toolCall.result);
  const hasDetails = Boolean(args || result);
  const isRunning = toolCall.status === 'running';

  return (
    <div className="rounded-lg border border-border/60 bg-card/60 shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => hasDetails && setIsOpen((v) => !v)}
        className={cn(
          'w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors',
          hasDetails ? 'hover:bg-accent/40 cursor-pointer' : 'cursor-default',
        )}
      >
        <span
          className={cn(
            'flex items-center justify-center w-6 h-6 rounded-md shrink-0',
            isRunning
              ? 'bg-primary/10 text-primary'
              : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
          )}
        >
          {_toolIcon(toolCall.name)}
        </span>
        <span className="font-medium text-foreground/90">{_toolLabel(toolCall.name)}</span>
        <span className="ml-auto flex items-center gap-2">
          {isRunning ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
          ) : (
            <span className="text-xs text-muted-foreground">done</span>
          )}
          {hasDetails && (
            <ChevronDown
              className={cn(
                'w-3.5 h-3.5 text-muted-foreground transition-transform',
                isOpen && 'rotate-180',
              )}
            />
          )}
        </span>
      </button>

      {isOpen && hasDetails && (
        <div className="border-t border-border/60 px-3 py-2 space-y-2 bg-muted/20">
          {args && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1">
                Arguments
              </p>
              <pre className="text-xs text-foreground/80 whitespace-pre-wrap break-words font-mono">
                {args}
              </pre>
            </div>
          )}
          {result && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1">
                Result
              </p>
              <pre className="text-xs text-foreground/80 whitespace-pre-wrap break-words font-mono">
                {result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolCalls({ toolCalls, className }: ToolCallsProps) {
  if (toolCalls.length === 0) return null;

  return (
    <div className={cn('max-w-3xl mx-auto w-full px-1', className)}>
      <div className="flex flex-col gap-1.5 py-2">
        {toolCalls.map((toolCall) => (
          <ToolCallCard key={toolCall.id} toolCall={toolCall} />
        ))}
      </div>
    </div>
  );
}
