'use client';

import { Citation } from '@/lib/api';

interface SourcePanelProps {
  citations: Citation[];
  selectedCitation?: Citation;
  onCitationSelect?: (citation: Citation) => void;
}

export function SourcePanel({ citations, selectedCitation, onCitationSelect }: SourcePanelProps) {
  if (citations.length === 0) {
    return null;
  }

  return (
    <div
      className="w-full rounded-lg border overflow-hidden"
      style={{ borderColor: 'var(--color-border)' }}
    >
      <div
        className="px-4 py-3 border-b"
        style={{
          backgroundColor: 'var(--color-bg-secondary)',
          borderColor: 'var(--color-border)',
        }}
      >
        <h3
          className="font-semibold"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Sources ({citations.length})
        </h3>
      </div>

      <div className="divide-y" style={{ divideColor: 'var(--color-border)' }}>
        {citations.map((citation) => (
          <button
            key={citation.index}
            onClick={() => onCitationSelect?.(citation)}
            className="w-full text-left p-4 transition-colors hover:bg-opacity-50"
            style={{
              backgroundColor:
                selectedCitation?.index === citation.index
                  ? 'var(--color-bg-secondary)'
                  : 'transparent',
            }}
          >
            <div className="flex gap-3">
              {/* Citation number */}
              <div
                className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium"
                style={{
                  backgroundColor: 'var(--color-accent)',
                  color: 'white',
                }}
              >
                {citation.index}
              </div>

              {/* Citation details */}
              <div className="flex-1 min-w-0">
                <h4
                  className="font-medium text-sm leading-tight truncate"
                  style={{
                    color: 'var(--color-text)',
                    fontFamily: 'var(--font-serif)',
                  }}
                  title={citation.title}
                >
                  {citation.title}
                </h4>
                <p
                  className="text-xs mt-1 truncate"
                  style={{
                    color: 'var(--color-text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {citation.authors.slice(0, 2).join(', ')}
                  {citation.authors.length > 2 && ' et al.'}
                  {citation.year && ` (${citation.year})`}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
