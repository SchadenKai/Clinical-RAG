'use client';

import * as React from 'react';
import { MessageInput } from './message-input';
import { Button } from '@/components/ui/button';
import db from '@/lib/dummy-db.json';
import type { AgentId } from '@/lib/agents-config';

interface ChatIntroProps {
  input: string;
  handleInputChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  activeAgent: AgentId;
  onAgentChange: (agent: AgentId) => void;
  onSuggestionClick: (prompt: string) => void;
  displayName: string;
}

export function ChatIntro({
  input,
  handleInputChange,
  onSubmit,
  isLoading,
  activeAgent,
  onAgentChange,
  onSuggestionClick,
  displayName,
}: ChatIntroProps) {
  return (
    <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
      <div className="flex flex-col p-4 max-w-3xl mx-auto w-full min-h-full justify-center pb-20 pt-[10vh]">
        <div className="w-full flex flex-col gap-2 mb-8 px-4">
          <h1 className="text-2xl sm:text-3xl font-medium text-foreground flex items-center gap-2">
            <span className="text-xl">🩺</span>
            {displayName}
          </h1>
          <h2 className="text-4xl sm:text-5xl font-semibold tracking-tight text-muted-foreground">
            How can I assist with your clinical queries?
          </h2>
        </div>

        <div className="w-full">
          <MessageInput
            input={input}
            handleInputChange={handleInputChange}
            onSubmit={onSubmit}
            isLoading={isLoading}
            activeAgent={activeAgent}
            onAgentChange={onAgentChange}
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
                    onSuggestionClick(suggestion.prompt || suggestion.label);
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
  );
}
