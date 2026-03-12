import { CheckCircle2, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface StepProgress {
  name: string;
  status: 'active' | 'completed';
}

interface AgentStepsProps {
  steps: StepProgress[];
  className?: string;
}

export function AgentSteps({ steps, className }: AgentStepsProps) {
  if (steps.length === 0) return null;

  return (
    <div className={cn('max-w-3xl mx-auto w-full px-1', className)}>
      <div className="flex flex-col gap-1.5 py-2">
        {steps.map((step, idx) => (
          <div
            key={`${step.name}-${idx}`}
            className={cn(
              'flex items-center gap-2 text-sm transition-all duration-300',
              step.status === 'active'
                ? 'text-primary font-medium'
                : 'text-muted-foreground',
            )}
          >
            {step.status === 'active' ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            )}
            <span>{step.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
