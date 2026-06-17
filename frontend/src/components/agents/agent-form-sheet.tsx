'use client';

import * as React from 'react';

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Agent } from '@/lib/agents-api';
import { useCreateAgent, useUpdateAgent } from '@/hooks/use-agents';

interface AgentFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When provided, the sheet edits this agent; otherwise it creates a new one. */
  agent?: Agent | null;
}

export function AgentFormSheet({ open, onOpenChange, agent }: AgentFormSheetProps) {
  const isEdit = Boolean(agent);
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();
  const isPending = createAgent.isPending || updateAgent.isPending;

  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [prompt, setPrompt] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);

  // Sync local fields whenever the sheet opens or the edited agent changes, and
  // clear them on close so a reopen never flashes the previous agent's values.
  React.useEffect(() => {
    setName(open ? (agent?.name ?? '') : '');
    setDescription(open ? (agent?.description ?? '') : '');
    setPrompt(open ? (agent?.prompt ?? '') : '');
    setError(null);
  }, [open, agent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Name is required.');
      return;
    }
    setError(null);

    const input = { name: trimmedName, description, prompt };
    try {
      if (isEdit && agent) {
        await updateAgent.mutateAsync({ id: agent.id, input });
      } else {
        await createAgent.mutateAsync(input);
      }
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg p-0">
        <SheetHeader>
          <SheetTitle>{isEdit ? 'Edit agent' : 'Create agent'}</SheetTitle>
          <SheetDescription>
            {isEdit
              ? 'Update this agent’s name, description, and prompt.'
              : 'Define a new chat agent available in the chat page.'}
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="flex flex-1 min-h-0 flex-col">
          <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-5 px-4 pb-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="agent-name" className="text-sm font-medium">
                Name
              </label>
              <Input
                id="agent-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Triage Assistant"
                autoFocus
              />
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="agent-description" className="text-sm font-medium">
                Description
              </label>
              <Textarea
                id="agent-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="A short summary shown in the agent selector."
                className="min-h-[72px] resize-none"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label htmlFor="agent-prompt" className="text-sm font-medium">
                System prompt
              </label>
              <Textarea
                id="agent-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Instructions that define how this agent behaves."
                className="min-h-[200px] font-mono text-sm"
              />
            </div>

            {error && (
              <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">
                {error}
              </p>
            )}
          </div>

          <SheetFooter className="flex-row justify-end gap-2 border-t border-border/60">
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Saving…' : isEdit ? 'Save changes' : 'Create agent'}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
