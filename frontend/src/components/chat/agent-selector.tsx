import * as React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { AgentId, getAgentVisual } from '@/lib/agents-config';
import { useAgents } from '@/hooks/use-agents';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

interface AgentSelectorProps {
  value: AgentId;
  onChange: (value: AgentId) => void;
  className?: string;
}

export function AgentSelector({ value, onChange, className }: AgentSelectorProps) {
  const { data: agents, isLoading } = useAgents();

  const activeAgent = agents?.find((agent) => agent.id === value);
  const activeVisual = getAgentVisual(value);
  const ActiveIcon = activeVisual.icon;

  const triggerLabel = activeAgent?.name ?? (isLoading ? 'Loading agents…' : 'Select an agent');

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          'flex items-center justify-between gap-2 w-fit max-w-[240px] sm:max-w-[400px] h-10 px-3 py-2 border border-border/50 rounded-lg bg-background shadow-xs hover:bg-accent hover:text-accent-foreground font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring',
          className
        )}
      >
        <div className="flex items-center gap-2 truncate">
          <ActiveIcon className={cn('h-4 w-4 shrink-0', activeVisual.themeColor)} />
          <span className="truncate">{triggerLabel}</span>
        </div>
        <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[300px] rounded-xl shadow-md border-border/50 bg-background/95 backdrop-blur-sm z-[100]">
        {!agents || agents.length === 0 ? (
          <div className="px-3 py-4 text-sm text-muted-foreground">
            {isLoading ? 'Loading agents…' : 'No agents available'}
          </div>
        ) : (
          agents.map((agent) => {
            const visual = getAgentVisual(agent.id);
            const Icon = visual.icon;
            return (
              <DropdownMenuItem
                key={agent.id}
                onClick={() => onChange(agent.id)}
                className="cursor-pointer gap-3 p-3 items-start my-1 focus:bg-accent rounded-lg transition-colors"
              >
                <Icon className={cn('h-5 w-5 mt-0.5 shrink-0', visual.themeColor)} />
                <div className="flex flex-col gap-1">
                  <span className="font-medium text-sm leading-none">{agent.name}</span>
                  {agent.description && (
                    <span className="text-xs text-muted-foreground leading-snug">{agent.description}</span>
                  )}
                </div>
              </DropdownMenuItem>
            );
          })
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
