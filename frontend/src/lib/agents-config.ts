import { Brain, Stethoscope, TypeIcon as type, LucideIcon } from 'lucide-react';

export type AgentId = 'general' | 'clinical_rag';

export interface AgentConfig {
  id: AgentId;
  name: string;
  description: string;
  icon: LucideIcon;
  systemPrompt?: string;
  themeColor: string; // Tailwind class
}

export const AGENTS: Record<AgentId, AgentConfig> = {
  general: {
    id: 'general',
    name: 'General Chat',
    description: 'Versatile AI assistant for everyday tasks and general queries.',
    icon: Brain,
    themeColor: 'text-indigo-500',
  },
  clinical_rag: {
    id: 'clinical_rag',
    name: 'Clinical Guidelines Agent',
    description: 'Specialized healthcare assistant grounded in CDC and WHO guidelines.',
    icon: Stethoscope,
    themeColor: 'text-emerald-500',
  },
};

export function getAgentConfig(id: AgentId): AgentConfig {
  return AGENTS[id] || AGENTS.general;
}
