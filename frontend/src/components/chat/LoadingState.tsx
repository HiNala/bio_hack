'use client';

export interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  detail?: string;
}

interface LoadingStateProps {
  steps: ProgressStep[];
  currentMessage?: string;
}

export function LoadingState({ steps, currentMessage }: LoadingStateProps) {
  return (
    <div className="mb-6 animate-fadeIn">
      {/* Typing indicator */}
      <div className="flex items-center gap-3 mb-4">
        <div className="dot-loading flex gap-1">
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: 'var(--accent-primary)' }}
          />
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: 'var(--accent-primary)' }}
          />
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: 'var(--accent-primary)' }}
          />
        </div>
        <span
          className="text-sm"
          style={{ color: 'var(--text-secondary)' }}
        >
          {currentMessage || 'Processing...'}
        </span>
      </div>

      {/* Progress steps */}
      <div
        className="p-4 rounded-lg"
        style={{ backgroundColor: 'var(--bg-secondary)' }}
      >
        <div className="space-y-2">
          {steps.map((step) => (
            <div key={step.id} className="flex items-center gap-3">
              {/* Status icon */}
              <div className="w-5 h-5 flex items-center justify-center">
                {step.status === 'completed' && (
                  <svg
                    className="w-4 h-4"
                    style={{ color: 'var(--accent-success)' }}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {step.status === 'active' && (
                  <div
                    className="w-3 h-3 rounded-full animate-pulse"
                    style={{ backgroundColor: 'var(--accent-primary)' }}
                  />
                )}
                {step.status === 'pending' && (
                  <div
                    className="w-3 h-3 rounded-full border-2"
                    style={{ borderColor: 'var(--border-medium)' }}
                  />
                )}
                {step.status === 'error' && (
                  <svg
                    className="w-4 h-4"
                    style={{ color: 'var(--accent-error)' }}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </div>

              {/* Step text */}
              <div className="flex-1">
                <span
                  className="text-sm"
                  style={{
                    color: step.status === 'completed'
                      ? 'var(--text-secondary)'
                      : step.status === 'active'
                      ? 'var(--text-primary)'
                      : 'var(--text-muted)',
                  }}
                >
                  {step.label}
                </span>
                {step.detail && (
                  <span
                    className="text-xs ml-2"
                    style={{ color: 'var(--accent-success)' }}
                  >
                    {step.detail}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
