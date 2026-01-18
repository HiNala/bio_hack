'use client';

import { useState } from 'react';
import { CitationTooltip } from './CitationTooltip';

export interface Source {
  citationId: number;
  paperId: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
}

interface AssistantResponseProps {
  content: string;
  sources: Source[];
  papersAnalyzed: number;
  onSourceClick?: (source: Source) => void;
}

export function AssistantResponse({
  content,
  sources,
  papersAnalyzed,
  onSourceClick,
}: AssistantResponseProps) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  // Parse content with markdown-like formatting and citations
  const renderContent = (text: string) => {
    // Split by markdown elements while preserving them
    const parts = text.split(/(\*\*[^*]+\*\*|\[\d+\])/g);
    
    return parts.map((part, i) => {
      // Check for bold markdown
      const boldMatch = part.match(/^\*\*([^*]+)\*\*$/);
      if (boldMatch) {
        return (
          <strong key={i} style={{ fontWeight: 600 }}>
            {boldMatch[1]}
          </strong>
        );
      }

      // Check for citation
      const citationMatch = part.match(/^\[(\d+)\]$/);
      if (citationMatch) {
        const num = parseInt(citationMatch[1]);
        const source = sources.find(s => s.citationId === num);
        return (
          <CitationTooltip
            key={i}
            source={source || { citationId: num, paperId: '', title: '', authors: [], year: null, venue: null, doi: null, url: null }}
            onSourceClick={(s) => onSourceClick?.(s)}
          >
            <span className="citation" title={source?.title || `Citation ${num}`}>
              [{num}]
            </span>
          </CitationTooltip>
        );
      }

      return <span key={i}>{part}</span>;
    });
  };

  // Split content into sections
  const renderSection = (text: string, idx: number) => {
    const lines = text.split('\n');
    
    return (
      <div key={idx} className="mb-4">
        {lines.map((line, lineIdx) => {
          // Check for section header (starts with **)
          if (line.startsWith('**') && line.endsWith(':**')) {
            const title = line.slice(2, -3);
            return (
              <h3
                key={lineIdx}
                className="text-sm font-semibold mt-4 mb-2"
                style={{ color: 'var(--text-primary)' }}
              >
                {title}
              </h3>
            );
          }

          // Check for bullet point
          if (line.startsWith('• ') || line.startsWith('- ')) {
            return (
              <div
                key={lineIdx}
                className="flex gap-2 ml-2 mb-1"
              >
                <span style={{ color: 'var(--accent-primary)' }}>•</span>
                <span>{renderContent(line.slice(2))}</span>
              </div>
            );
          }

          // Regular paragraph
          if (line.trim()) {
            return (
              <p key={lineIdx} className="mb-2">
                {renderContent(line)}
              </p>
            );
          }

          return null;
        })}
      </div>
    );
  };

  const visibleSources = sourcesExpanded ? sources : sources.slice(0, 3);

  // Split content by double newlines for paragraphs
  const paragraphs = content.split('\n\n').filter(p => p.trim());

  return (
    <div className="mb-6 animate-fadeIn">
      {/* Main content */}
      <div
        className="text-base leading-relaxed mb-4"
        style={{ color: 'var(--text-primary)' }}
      >
        {paragraphs.map((paragraph, i) => renderSection(paragraph, i))}
      </div>

      {/* Only show sources section if we have sources */}
      {sources.length > 0 && (
        <>
          {/* Divider */}
          <hr
            className="my-6"
            style={{ borderColor: 'var(--border-light)', borderTopWidth: '1px' }}
          />

          {/* Sources section */}
          <div>
            {/* Header */}
            <button
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="flex items-center gap-2 mb-3 w-full text-left"
            >
              <svg
                className="w-4 h-4"
                style={{ color: 'var(--text-secondary)' }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
              <span
                className="text-sm font-medium"
                style={{ color: 'var(--text-secondary)' }}
              >
                Sources ({sources.length} papers)
              </span>
              <svg
                className={`w-4 h-4 transition-transform ${sourcesExpanded ? 'rotate-180' : ''}`}
                style={{ color: 'var(--text-tertiary)' }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Source cards */}
            <div className="space-y-2">
              {visibleSources.map((source) => (
                <div
                  key={source.citationId}
                  id={`source-${source.citationId}`}
                  onClick={() => onSourceClick?.(source)}
                  className="p-3 rounded-lg cursor-pointer transition-all duration-200"
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-light)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                  }}
                >
                  <div className="flex items-start gap-3">
                    {/* Citation badge */}
                    <span
                      className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold"
                      style={{
                        backgroundColor: 'var(--accent-primary)',
                        color: 'white',
                      }}
                    >
                      {source.citationId}
                    </span>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <h4
                        className="text-sm font-medium truncate"
                        style={{ color: 'var(--text-primary)' }}
                        title={source.title}
                      >
                        {source.title}
                      </h4>
                      <p
                        className="text-xs mt-1 truncate"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        {source.authors.slice(0, 2).join(', ')}
                        {source.authors.length > 2 && ' et al.'}
                        {source.year && ` • ${source.year}`}
                        {source.venue && ` • ${source.venue}`}
                      </p>
                    </div>

                    {/* External link */}
                    {(source.url || source.doi) && (
                      <a
                        href={source.url || (source.doi ? `https://doi.org/${source.doi}` : '#')}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex-shrink-0"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                          />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Show more button */}
            {sources.length > 3 && !sourcesExpanded && (
              <button
                onClick={() => setSourcesExpanded(true)}
                className="mt-2 text-sm"
                style={{ color: 'var(--accent-primary)' }}
              >
                Show {sources.length - 3} more sources
              </button>
            )}
          </div>
        </>
      )}

      {/* Papers analyzed note */}
      {papersAnalyzed > 0 && (
        <p
          className="text-xs mt-4 text-center"
          style={{ color: 'var(--text-muted)' }}
        >
          Synthesized from {papersAnalyzed} papers
        </p>
      )}
    </div>
  );
}
