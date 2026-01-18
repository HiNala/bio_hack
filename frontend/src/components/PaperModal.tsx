'use client';

import { Paper } from '@/lib/api';

interface PaperModalProps {
  paper: Paper | null;
  onClose: () => void;
}

export function PaperModal({ paper, onClose }: PaperModalProps) {
  if (!paper) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="relative w-full max-w-2xl max-h-[80vh] overflow-auto rounded-lg shadow-xl"
        style={{ backgroundColor: 'var(--color-bg)' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="sticky top-0 flex items-start justify-between p-4 border-b"
          style={{
            backgroundColor: 'var(--color-bg)',
            borderColor: 'var(--color-border)',
          }}
        >
          <h2
            className="text-xl font-semibold pr-8 leading-tight"
            style={{ fontFamily: 'var(--font-serif)' }}
          >
            {paper.title}
          </h2>
          <button
            onClick={onClose}
            className="flex-shrink-0 p-1 rounded hover:bg-opacity-10"
            style={{ color: 'var(--color-text-muted)' }}
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Metadata */}
          <div
            className="flex flex-wrap gap-4 text-sm"
            style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}
          >
            {paper.year && (
              <span>📅 {paper.year}</span>
            )}
            {paper.venue && (
              <span>📚 {paper.venue}</span>
            )}
            <span>📊 {paper.citation_count} citations</span>
            <span className="capitalize">🔗 {paper.source}</span>
          </div>

          {/* Authors */}
          {paper.authors.length > 0 && (
            <div>
              <h3
                className="text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-muted)' }}
              >
                Authors
              </h3>
              <p style={{ fontFamily: 'var(--font-serif)' }}>
                {paper.authors.join(', ')}
              </p>
            </div>
          )}

          {/* Abstract */}
          {paper.abstract && (
            <div>
              <h3
                className="text-sm font-medium mb-2"
                style={{ color: 'var(--color-text-muted)' }}
              >
                Abstract
              </h3>
              <p
                className="leading-relaxed"
                style={{
                  fontFamily: 'var(--font-serif)',
                  color: 'var(--color-text-secondary)',
                }}
              >
                {paper.abstract}
              </p>
            </div>
          )}

          {/* Links */}
          <div className="flex gap-3 pt-4">
            {paper.doi && (
              <a
                href={`https://doi.org/${paper.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded text-sm font-medium transition-colors"
                style={{
                  backgroundColor: 'var(--color-accent)',
                  color: 'white',
                }}
              >
                View on DOI →
              </a>
            )}
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded text-sm font-medium border transition-colors"
                style={{
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text)',
                }}
              >
                View Source →
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
