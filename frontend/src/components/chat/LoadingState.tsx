'use client';

export interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

interface LoadingStateProps {
  steps: ProgressStep[];
  currentMessage?: string;
}

export function LoadingState({ steps, currentMessage }: LoadingStateProps) {
  return (
    <div className="animate-fadeIn">
      {/* Animated orb */}
      <div className="flex justify-center mb-8">
        <div
          className="w-20 h-20 rounded-full animate-orb-active"
          style={{
            background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)',
            boxShadow: '0 0 40px rgba(59, 130, 246, 0.4), 0 0 80px rgba(139, 92, 246, 0.2)',
          }}
        />
      </div>

      {/* Current message */}
      {currentMessage && (
        <p 
          className="text-center text-base font-medium mb-8"
          style={{ color: 'var(--text-primary)' }}
        >
          {currentMessage}
        </p>
      )}

      {/* Progress steps */}
      <div className="max-w-xs mx-auto space-y-3">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-3">
            <StepIcon status={step.status} />
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
          </div>
        ))}
      </div>
    </div>
  );
}

function StepIcon({ status }: { status: ProgressStep['status'] }) {
  if (status === 'completed') {
    return (
      <div 
        className="w-5 h-5 rounded-full flex items-center justify-center"
        style={{ backgroundColor: 'var(--accent-green)' }}
      >
        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }

  if (status === 'active') {
    return (
      <div 
        className="w-5 h-5 rounded-full flex items-center justify-center animate-spin"
        style={{ 
          border: '2px solid var(--border-light)',
          borderTopColor: 'var(--accent-blue)',
        }}
      />
    );
  }

  if (status === 'error') {
    return (
      <div 
        className="w-5 h-5 rounded-full flex items-center justify-center"
        style={{ backgroundColor: 'var(--accent-red)' }}
      >
        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }

  // Pending
  return (
    <div 
      className="w-5 h-5 rounded-full"
      style={{ 
        border: '2px solid var(--border-light)',
      }}
    />
  );
}
