'use client';

interface EmptyStateProps {
  onExampleClick: (query: string) => void;
}

const EXAMPLE_QUERIES = [
  {
    query: "What is experimentally verified vs theoretical in quantum decoherence?",
    type: "verification",
  },
  {
    query: "What disagreements exist in CRISPR off-target effects research?",
    type: "disagreement",
  },
  {
    query: "Compare evidence for Copenhagen vs Many-Worlds interpretations",
    type: "comparison",
  },
  {
    query: "What evidence supports intermittent fasting for longevity?",
    type: "evidence",
  },
  {
    query: "What are the open questions in room-temperature superconductivity?",
    type: "gaps",
  },
];

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="max-w-xl mx-auto px-4 pt-12 pb-8 animate-fadeIn" role="main" aria-label="Welcome to ScienceRAG">
      {/* Hero Icon - Scientific/Research themed */}
      <div className="flex justify-center mb-8" aria-hidden="true">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center relative animate-pulse-subtle"
          style={{ backgroundColor: 'rgba(59, 130, 246, 0.08)' }}
        >
          {/* Microscope/Research icon */}
          <svg
            className="w-8 h-8 animate-orb-idle"
            style={{ color: 'var(--accent-blue)' }}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M12 2v4m0 12v4" />
            <path d="m4.93 4.93 2.83 2.83m8.48 8.48 2.83 2.83" />
            <path d="m19.07 4.93-2.83 2.83m-8.48 8.48-2.83 2.83" />
          </svg>
        </div>
      </div>

      {/* Hero Text - Scientific framing */}
      <div className="text-center mb-10">
        <h1 
          className="text-3xl font-semibold mb-4"
          style={{ color: 'var(--text-primary)' }}
        >
          Scientific Literature Intelligence
        </h1>
        <p 
          className="text-base leading-relaxed max-w-md mx-auto"
          style={{ color: 'var(--text-secondary)' }}
        >
          State a research question or hypothesis.
          <br />
          Get evidence-backed synthesis with full citations.
        </p>
      </div>

      {/* Method badges */}
      <div className="flex justify-center gap-2 mb-10 flex-wrap">
        <MethodBadge icon="🔍" label="Multi-source search" delay="200ms" />
        <MethodBadge icon="📊" label="Evidence ranking" delay="400ms" />
        <MethodBadge icon="🔗" label="Citation linking" delay="600ms" />
      </div>

      {/* Example queries label */}
      <p 
        className="text-xs font-semibold uppercase tracking-wider text-center mb-4"
        style={{ color: 'var(--text-tertiary)' }}
      >
        Example Research Questions
      </p>

      {/* Example Query Cards */}
      <div className="space-y-3" role="list" aria-label="Example research queries">
        {EXAMPLE_QUERIES.map((item, index) => (
          <button
            key={index}
            onClick={() => onExampleClick(item.query)}
            className="w-full text-left p-4 rounded-xl border transition-all duration-200 group flex items-start gap-3 animate-slideUp"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-light)',
              animationDelay: `${index * 100}ms`,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-medium)';
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-light)';
              e.currentTarget.style.boxShadow = 'none';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
            role="listitem"
            aria-label={`Try example query: ${item.query}`}
          >
            <QueryTypeIcon type={item.type} />
            <span 
              className="text-sm transition-colors duration-200 flex-1"
              style={{ color: 'var(--text-secondary)' }}
            >
              {item.query}
            </span>
            <svg 
              className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5"
              style={{ color: 'var(--text-tertiary)' }}
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        ))}
      </div>

      {/* Footer note */}
      <p 
        className="text-xs text-center mt-8 max-w-sm mx-auto"
        style={{ color: 'var(--text-tertiary)' }}
      >
        Papers sourced from OpenAlex & Semantic Scholar. 
        All claims are linked to original research.
      </p>
    </div>
  );
}

function MethodBadge({ icon, label, delay }: { icon: string; label: string; delay?: string }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs animate-fadeIn transition-all duration-200"
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        color: 'var(--text-secondary)',
        animationDelay: delay || '0ms',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'rgba(59, 130, 246, 0.05)';
        e.currentTarget.style.borderColor = 'var(--border-medium)';
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--bg-card)';
        e.currentTarget.style.borderColor = 'var(--border-light)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  );
}

function QueryTypeIcon({ type }: { type: string }) {
  const icons: Record<string, { emoji: string; color: string }> = {
    verification: { emoji: '✓', color: 'var(--accent-green)' },
    disagreement: { emoji: '⚡', color: 'var(--accent-purple)' },
    comparison: { emoji: '⚖', color: 'var(--accent-blue)' },
    evidence: { emoji: '📊', color: 'var(--accent-blue)' },
    gaps: { emoji: '?', color: '#F59E0B' },
  };
  
  const config = icons[type] || icons.evidence;
  
  return (
    <span 
      className="w-6 h-6 rounded-md flex items-center justify-center text-xs flex-shrink-0"
      style={{ 
        backgroundColor: `${config.color}15`,
        color: config.color,
      }}
    >
      {config.emoji}
    </span>
  );
}
