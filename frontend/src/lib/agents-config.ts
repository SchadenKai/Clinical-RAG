import { Brain, Stethoscope, Bot, LucideIcon } from 'lucide-react';

/**
 * Agents are now created and managed at runtime (see `agents-api.ts`), so an
 * agent id is any string. The two seeded built-ins keep bespoke visuals; every
 * other agent falls back to a generic look.
 */
export type AgentId = string;

export interface AgentVisual {
  icon: LucideIcon;
  themeColor: string; // Tailwind text-color class
}

const KNOWN_VISUALS: Record<string, AgentVisual> = {
  general: { icon: Brain, themeColor: 'text-indigo-500' },
  clinical_rag: { icon: Stethoscope, themeColor: 'text-emerald-500' },
};

const DEFAULT_VISUAL: AgentVisual = { icon: Bot, themeColor: 'text-sky-500' };

export function getAgentVisual(id: string): AgentVisual {
  return KNOWN_VISUALS[id] ?? DEFAULT_VISUAL;
}
