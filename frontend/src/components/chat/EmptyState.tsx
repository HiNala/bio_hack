'use client';

interface EmptyStateProps {
  onExampleClick: (query: string) => void;
}

const EXAMPLE_QUERIES = [
  "What are the health effects of intermittent fasting?",
  "Compare CRISPR vs traditional gene therapy",
  "How does the double slit experiment work with molecules?",
  "Latest developments in room-temperature superconductors",
  "What causes antibiotic resistance?",
];

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="max-w-xl mx-auto px-4 pt-16 pb-8 animate-fadeIn">
      {/* Hero Icon */}
      <div className="flex justify-center mb-8">
        <div 
          className="w-16 h-16 rounded-2xl flex items-center justify-center"
          style={{ backgroundColor: 'rgba(59, 130, 246, 0.08)' }}
        >
          <svg 
            className="w-8 h-8"
            style={{ color: 'var(--accent-blue)' }}
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="1.5"
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            {/* Sparkle/star icon */}
            <path d="M12 3v2m0 14v2M3 12h2m14 0h2" />
            <path d="M5.636 5.636l1.414 1.414m9.9 9.9l1.414 1.414M5.636 18.364l1.414-1.414m9.9-9.9l1.414-1.414" />
            <circle cx="12" cy="12" r="4" />
          </svg>
        </div>
      </div>

      {/* Hero Text */}
      <div className="text-center mb-12">
        <h1 
          className="text-3xl font-semibold mb-4"
          style={{ color: 'var(--text-primary)' }}
        >
          Ask anything about science
        </h1>
        <p 
          className="text-base leading-relaxed max-w-md mx-auto"
          style={{ color: 'var(--text-secondary)' }}
        >
          Explore research across millions of papers.
          <br />
          Get synthesized answers with citations.
        </p>
      </div>

      {/* Try asking label */}
      <p 
        className="text-sm text-center mb-4"
        style={{ color: 'var(--text-tertiary)' }}
      >
        Try asking:
      </p>

      {/* Example Query Cards */}
      <div className="space-y-3">
        {EXAMPLE_QUERIES.map((query, index) => (
          <button
            key={index}
            onClick={() => onExampleClick(query)}
            className="w-full text-left p-4 rounded-xl border transition-all duration-200 group"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-light)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-medium)';
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-light)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <span 
              className="text-sm transition-colors duration-200"
              style={{ color: 'var(--text-secondary)' }}
            >
              {query}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
