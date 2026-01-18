'use client';

import { RAGResponse, Citation } from '@/lib/api';

interface AnswerDisplayProps {
  response: RAGResponse;
  onCitationClick?: (citation: Citation) => void;
}

export function AnswerDisplay({ response, onCitationClick }: AnswerDisplayProps) {
  // Parse citation references in text like [1], [2]
  const renderTextWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationIndex = parseInt(match[1]) - 1;
        const citation = response.citations[citationIndex];
        if (citation) {
          return (
            <button
              key={i}
              onClick={() => onCitationClick?.(citation)}
              className="citation"
              title={citation.title}
            >
              [{match[1]}]
            </button>
          );
        }
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      {/* Summary */}
      <section>
        <h2
          className="text-xl font-semibold mb-3"
          style={{ fontFamily: 'var(--font-serif)' }}
        >
          Summary
        </h2>
        <p
          className="text-lg leading-relaxed"
          style={{ color: 'var(--color-text)', fontFamily: 'var(--font-serif)' }}
        >
          {renderTextWithCitations(response.summary)}
        </p>
      </section>

      {/* Key Findings */}
      {response.key_findings.length > 0 && (
        <section>
          <h2
            className="text-xl font-semibold mb-3"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            Key Findings
          </h2>
          <ul className="space-y-2">
            {response.key_findings.map((finding, i) => (
              <li
                key={i}
                className="flex gap-3"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                <span style={{ color: 'var(--color-accent)' }}>•</span>
                <span style={{ fontFamily: 'var(--font-serif)' }}>
                  {renderTextWithCitations(finding)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Consensus */}
      {response.consensus.length > 0 && (
        <section
          className="p-4 rounded-lg"
          style={{ backgroundColor: 'var(--color-bg-secondary)' }}
        >
          <h2
            className="text-lg font-semibold mb-2 flex items-center gap-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            <span style={{ color: 'var(--color-success)' }}>✓</span>
            Areas of Consensus
          </h2>
          <ul className="space-y-1">
            {response.consensus.map((item, i) => (
              <li
                key={i}
                className="text-sm"
                style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-serif)' }}
              >
                {renderTextWithCitations(item)}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Open Questions */}
      {response.open_questions.length > 0 && (
        <section
          className="p-4 rounded-lg"
          style={{ backgroundColor: 'var(--color-bg-secondary)' }}
        >
          <h2
            className="text-lg font-semibold mb-2 flex items-center gap-2"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            <span style={{ color: 'var(--color-warning)' }}>?</span>
            Open Questions
          </h2>
          <ul className="space-y-1">
            {response.open_questions.map((item, i) => (
              <li
                key={i}
                className="text-sm"
                style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-serif)' }}
              >
                {item}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Papers analyzed */}
      <p
        className="text-sm text-center pt-4 border-t"
        style={{
          color: 'var(--color-text-muted)',
          borderColor: 'var(--color-border)',
          fontFamily: 'var(--font-mono)',
        }}
      >
        Synthesized from {response.papers_analyzed} papers
      </p>
    </div>
  );
}
