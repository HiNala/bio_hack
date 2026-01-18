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
  const completedCount = steps.filter(s => s.status === 'completed').length;
  const progressPercent = Math.round((completedCount / steps.length) * 100);

  return (
    <div className="animate-fadeIn">
      {/* Header with animated orb */}
      <div className="flex items-center gap-4 mb-6">
        <div
          className="w-12 h-12 rounded-xl animate-orb-active flex-shrink-0"
          style={{
            background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)',
            boxShadow: '0 0 24px rgba(59, 130, 246, 0.3), 0 0 48px rgba(139, 92, 246, 0.15)',
          }}
        />
        <div className="flex-1">
          <p 
            className="text-base font-medium"
            style={{ color: 'var(--text-primary)' }}
          >
            {currentMessage || 'Processing research query...'}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <div 
              className="flex-1 h-1.5 rounded-full overflow-hidden"
              style={{ backgroundColor: 'var(--border-light)' }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${progressPercent}%`,
                  backgroundColor: 'var(--accent-blue)',
                }}
              />
            </div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
              {progressPercent}%
            </span>
          </div>
        </div>
      </div>

      {/* Research Trace Panel */}
      <div 
        className="p-4 rounded-xl border"
        style={{ 
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-light)',
        }}
      >
        <h4 
          className="text-xs font-semibold uppercase tracking-wider mb-4 flex items-center gap-2"
          style={{ color: 'var(--text-tertiary)' }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
          Research Trace
        </h4>
        
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-start gap-3">
              {/* Step indicator */}
              <div className="flex flex-col items-center">
                <StepIcon status={step.status} />
                {index < steps.length - 1 && (
                  <div 
                    className="w-0.5 h-6 mt-1"
                    style={{ 
                      backgroundColor: step.status === 'completed' 
                        ? 'var(--accent-green)' 
                        : 'var(--border-light)' 
                    }}
                  />
                )}
              </div>
              
              {/* Step content */}
              <div className="flex-1 pb-2">
                <div className="flex items-center gap-2">
                  <span
                    className="text-sm"
                    style={{
                      color: step.status === 'active' 
                        ? 'var(--text-primary)' 
                        : step.status === 'completed'
                        ? 'var(--text-secondary)'
                        : 'var(--text-tertiary)',
                      fontWeight: step.status === 'active' ? 500 : 400,
                    }}
                  >
                    {step.label}
                  </span>
                  {step.status === 'active' && (
                    <span 
                      className="text-xs px-1.5 py-0.5 rounded animate-pulse"
                      style={{ 
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        color: 'var(--accent-blue)',
                      }}
                    >
                      In progress
                    </span>
                  )}
                </div>
                {step.detail && (
                  <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                    {step.detail}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Methodology note */}
      <p 
        className="text-xs text-center mt-4"
        style={{ color: 'var(--text-tertiary)' }}
      >
        Querying OpenAlex & Semantic Scholar • Embedding with AI • All sources tracked
      </p>
    </div>
  );
}

function StepIcon({ status }: { status: ProgressStep['status'] }) {
  if (status === 'completed') {
    return (
      <div 
        className="w-6 h-6 rounded-full flex items-center justify-center"
        style={{ backgroundColor: 'var(--accent-green)' }}
      >
        <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }

  if (status === 'active') {
    return (
      <div 
        className="w-6 h-6 rounded-full flex items-center justify-center"
        style={{ 
          border: '2px solid var(--accent-blue)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
        }}
      >
        <div 
          className="w-6 h-6 rounded-full border-2 border-transparent animate-spin"
          style={{ 
            borderTopColor: 'var(--accent-blue)',
          }}
        />
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div 
        className="w-6 h-6 rounded-full flex items-center justify-center"
        style={{ backgroundColor: 'var(--accent-red)' }}
      >
        <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }

  // Pending
  return (
    <div 
      className="w-6 h-6 rounded-full flex items-center justify-center"
      style={{ 
        border: '2px solid var(--border-light)',
        backgroundColor: 'transparent',
      }}
    >
      <div 
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: 'var(--border-medium)' }}
      />
    </div>
  );
}
