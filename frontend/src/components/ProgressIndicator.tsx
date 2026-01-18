'use client';

interface Step {
  label: string;
  description: string;
}

interface ProgressIndicatorProps {
  currentStep: number;
  steps?: Step[];
}

const DEFAULT_STEPS: Step[] = [
  { label: 'Parsing', description: 'Understanding your question' },
  { label: 'Searching', description: 'Fetching from literature databases' },
  { label: 'Processing', description: 'Chunking and embedding text' },
  { label: 'Analyzing', description: 'Finding relevant passages' },
  { label: 'Synthesizing', description: 'Generating answer with citations' },
];

export function ProgressIndicator({ currentStep, steps = DEFAULT_STEPS }: ProgressIndicatorProps) {
  return (
    <div className="w-full max-w-2xl mx-auto py-8">
      <div className="space-y-4">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isComplete = index < currentStep;
          
          return (
            <div
              key={index}
              className="flex items-center gap-4"
              style={{
                opacity: isActive ? 1 : isComplete ? 0.7 : 0.4,
              }}
            >
              {/* Step indicator */}
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium"
                style={{
                  backgroundColor: isComplete
                    ? 'var(--color-success)'
                    : isActive
                    ? 'var(--color-accent)'
                    : 'var(--color-border)',
                  color: isComplete || isActive ? 'white' : 'var(--color-text-muted)',
                }}
              >
                {isComplete ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>

              {/* Step content */}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span
                    className="font-medium"
                    style={{ color: isActive ? 'var(--color-text)' : 'var(--color-text-secondary)' }}
                  >
                    {step.label}
                  </span>
                  {isActive && (
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  )}
                </div>
                <p
                  className="text-sm"
                  style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}
                >
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
