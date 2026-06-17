'use client';

import * as React from 'react';
import { Pencil, Plus, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Agent } from '@/lib/agents-api';
import { useAgents, useDeleteAgent } from '@/hooks/use-agents';
import { getAgentVisual } from '@/lib/agents-config';
import { cn } from '@/lib/utils';
import { AgentFormSheet } from './agent-form-sheet';

export function AgentsManagement() {
  const { data: agents, isLoading, isError, error } = useAgents();
  const deleteAgent = useDeleteAgent();

  const [formOpen, setFormOpen] = React.useState(false);
  const [editingAgent, setEditingAgent] = React.useState<Agent | null>(null);
  const [deletingAgent, setDeletingAgent] = React.useState<Agent | null>(null);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);

  const openCreate = () => {
    setEditingAgent(null);
    setFormOpen(true);
  };

  const openEdit = (agent: Agent) => {
    setEditingAgent(agent);
    setFormOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deletingAgent) return;
    setDeleteError(null);
    try {
      await deleteAgent.mutateAsync(deletingAgent.id);
      setDeletingAgent(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete agent.');
    }
  };

  return (
    <div className="h-full w-full overflow-y-auto">
      <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 py-8 flex flex-col gap-8">
        <header className="flex items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-semibold tracking-tight">Chat Agents</h1>
            <p className="text-sm text-muted-foreground">
              Create and manage the agents available in the chat page.
            </p>
          </div>
          <Button onClick={openCreate} className="gap-2 shrink-0">
            <Plus className="h-4 w-4" />
            New Agent
          </Button>
        </header>

        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-40 rounded-xl" />
            ))}
          </div>
        )}

        {isError && (
          <div className="text-sm text-destructive bg-destructive/10 px-4 py-3 rounded-lg">
            Failed to load agents: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        )}

        {!isLoading && !isError && agents && agents.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border/70 py-16 text-center">
            <p className="text-sm text-muted-foreground">No agents yet.</p>
            <Button onClick={openCreate} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" />
              Create your first agent
            </Button>
          </div>
        )}

        {!isLoading && !isError && agents && agents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => {
              const visual = getAgentVisual(agent.id);
              const Icon = visual.icon;
              return (
                <div
                  key={agent.id}
                  className="flex flex-col gap-3 rounded-xl border border-border/60 bg-card p-5 shadow-sm transition-colors hover:border-border"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                        <Icon className={cn('h-5 w-5', visual.themeColor)} />
                      </span>
                      <div className="min-w-0">
                        <h3 className="font-medium truncate">{agent.name}</h3>
                        {agent.pipeline !== 'general' && (
                          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                            {agent.pipeline.replace('_', ' ')} pipeline
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => openEdit(agent)}
                        aria-label={`Edit ${agent.name}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => {
                          setDeleteError(null);
                          setDeletingAgent(agent);
                        }}
                        aria-label={`Delete ${agent.name}`}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {agent.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {agent.description}
                    </p>
                  )}

                  {agent.prompt && (
                    <pre className="text-xs text-muted-foreground/80 bg-muted/40 rounded-lg p-3 line-clamp-3 whitespace-pre-wrap font-mono">
                      {agent.prompt}
                    </pre>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <AgentFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        agent={editingAgent}
      />

      <Dialog
        open={Boolean(deletingAgent)}
        onOpenChange={(open) => {
          if (!open) setDeletingAgent(null);
        }}
      >
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>Delete agent</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete{' '}
              <span className="font-medium text-foreground">{deletingAgent?.name}</span>?
              This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {deleteError && (
            <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">
              {deleteError}
            </p>
          )}
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setDeletingAgent(null)}
              disabled={deleteAgent.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={deleteAgent.isPending}
            >
              {deleteAgent.isPending ? 'Deleting…' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
