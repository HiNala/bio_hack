'use client';

interface EmptyStateProps {
  onExampleClick: (query: string) => void;
}

const exampleQueries = [
  "What are the health effects of intermittent fasting?",
  "Compare CRISPR vs traditional gene therapy",
  "How does the double slit experiment work with molecules?",
  "Latest developments in room-temperature superconductors",
  "What causes antibiotic resistance?",
];

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] animate-fadeIn px-4">
      {/* Icon */}
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
        style={{ backgroundColor: 'var(--bg-secondary)' }}
      >
        <svg
          className="w-8 h-8"
          style={{ color: 'var(--accent-primary)' }}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
      </div>

      {/* Heading */}
      <h1
        className="text-3xl font-semibold text-center mb-3"
        style={{ color: 'var(--text-primary)' }}
      >
        Ask anything about science
      </h1>

      {/* Subtext */}
      <p
        className="text-center max-w-md mb-8 leading-relaxed"
        style={{ color: 'var(--text-secondary)' }}
      >
        Explore research across millions of papers.
        <br />
        Get synthesized answers with citations.
      </p>

      {/* Example queries */}
      <div className="w-full max-w-lg">
        <p
          className="text-sm mb-3 text-center"
          style={{ color: 'var(--text-muted)' }}
        >
          Try asking:
        </p>
        <div className="space-y-2">
          {exampleQueries.map((query, i) => (
            <button
              key={i}
              onClick={() => onExampleClick(query)}
              className="w-full text-left px-4 py-3 rounded-lg transition-colors text-sm"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-light)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              <span className="mr-2" style={{ color: 'var(--accent-primary)' }}>→</span>
              {query}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
