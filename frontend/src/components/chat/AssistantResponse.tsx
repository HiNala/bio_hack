'use client';

import { useState } from 'react';
import { CitationTooltip } from './CitationTooltip';
import type { Source } from '@/lib/api';

interface AssistantResponseProps {
  content: string;
  sources: Source[];
  papersAnalyzed: number;
  onSourceClick?: (source: Source) => void;
  toolActivity?: {
    openalexPapers: number;
    semanticScholarPapers: number;
    uniquePapers: number;
    chunksCreated: number;
    embeddingsGenerated: number;
  };
}

export function AssistantResponse({
  content,
  sources,
  papersAnalyzed,
  onSourceClick,
  toolActivity,
}: AssistantResponseProps) {
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [evidenceExpanded, setEvidenceExpanded] = useState(false);

  // Parse structured content
  const sections = parseStructuredContent(content);

  return (
    <div className="animate-fadeIn space-y-6">
      {/* Tool Activity Panel (Research Trace) */}
      {toolActivity && (
        <div
          className="p-4 rounded-xl border"
          style={{
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-light)',
          }}
          role="region"
          aria-label="Research activity summary"
        >
          <h4 
            className="text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2"
            style={{ color: 'var(--text-tertiary)' }}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
            </svg>
            Research Trace
          </h4>
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <ToolStep 
              icon="✓" 
              label={`Queried OpenAlex`}
              value={`${toolActivity.openalexPapers} papers`}
              complete
            />
            <ToolStep 
              icon="✓" 
              label={`Queried Semantic Scholar`}
              value={`${toolActivity.semanticScholarPapers} papers`}
              complete
            />
            <ToolStep 
              icon="✓" 
              label="Deduplicated results"
              value={`→ ${toolActivity.uniquePapers} unique`}
              complete
            />
            <ToolStep 
              icon="✓" 
              label="Created text chunks"
              value={`${toolActivity.chunksCreated} chunks`}
              complete
            />
            <ToolStep 
              icon="✓" 
              label="Generated embeddings"
              value={`${toolActivity.embeddingsGenerated} vectors`}
              complete
            />
            <ToolStep 
              icon="✓" 
              label="Synthesized answer"
              value={`${papersAnalyzed} sources`}
              complete
            />
          </div>
        </div>
      )}

      {/* Structured Answer Sections */}
      <div className="space-y-4">
        {sections.summary && (
          <AnswerSection
            title="Summary"
            icon="📋"
            isOpen={activeSection === 'summary' || activeSection === null}
            onToggle={() => setActiveSection(activeSection === 'summary' ? null : 'summary')}
          >
            <div className="text-[15px] leading-relaxed" style={{ color: 'var(--text-primary)' }}>
              {renderContentWithCitations(sections.summary, sources, onSourceClick)}
            </div>
          </AnswerSection>
        )}

        {sections.keyFindings.length > 0 && (
          <AnswerSection
            title="Key Findings"
            icon="🔬"
            badge={`${sections.keyFindings.length} findings`}
            isOpen={activeSection === 'findings'}
            onToggle={() => setActiveSection(activeSection === 'findings' ? null : 'findings')}
          >
            <ul className="space-y-2">
              {sections.keyFindings.map((finding, i) => (
                <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  <span style={{ color: 'var(--accent-blue)' }}>•</span>
                  <span>{renderContentWithCitations(finding, sources, onSourceClick)}</span>
                </li>
              ))}
            </ul>
          </AnswerSection>
        )}

        {sections.conflicts.length > 0 && (
          <AnswerSection
            title="Conflicting Evidence"
            icon="⚡"
            badge={`${sections.conflicts.length} conflicts`}
            isOpen={activeSection === 'conflicts'}
            onToggle={() => setActiveSection(activeSection === 'conflicts' ? null : 'conflicts')}
            accentColor="var(--accent-purple)"
          >
            <ul className="space-y-2">
              {sections.conflicts.map((conflict, i) => (
                <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  <span style={{ color: 'var(--accent-purple)' }}>⚠</span>
                  <span>{renderContentWithCitations(conflict, sources, onSourceClick)}</span>
                </li>
              ))}
            </ul>
          </AnswerSection>
        )}

        {sections.openQuestions.length > 0 && (
          <AnswerSection
            title="Open Questions"
            icon="❓"
            badge={`${sections.openQuestions.length} gaps`}
            isOpen={activeSection === 'questions'}
            onToggle={() => setActiveSection(activeSection === 'questions' ? null : 'questions')}
            accentColor="#F59E0B"
          >
            <ul className="space-y-2">
              {sections.openQuestions.map((question, i) => (
                <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  <span style={{ color: '#F59E0B' }}>?</span>
                  <span>{renderContentWithCitations(question, sources, onSourceClick)}</span>
                </li>
              ))}
            </ul>
          </AnswerSection>
        )}

        {/* Fallback for unstructured content */}
        {!sections.summary && sections.raw && (
          <div className="text-[15px] leading-relaxed" style={{ color: 'var(--text-primary)' }}>
            {renderContentWithCitations(sections.raw, sources, onSourceClick)}
          </div>
        )}
      </div>

      {/* Evidence Panel */}
      {sources.length > 0 && (
        <div 
          className="border rounded-xl overflow-hidden"
          style={{ borderColor: 'var(--border-light)' }}
        >
          {/* Evidence header */}
          <button
            onClick={() => setEvidenceExpanded(!evidenceExpanded)}
            className="w-full flex items-center justify-between p-4 transition-colors"
            style={{ backgroundColor: 'var(--bg-card)' }}
          >
            <div className="flex items-center gap-3">
              <svg 
                className="w-5 h-5"
                style={{ color: 'var(--text-tertiary)' }}
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
              </svg>
              <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                Evidence Sources
              </span>
              <span 
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ 
                  backgroundColor: 'var(--accent-blue)',
                  color: 'white',
                }}
              >
                {sources.length} papers
              </span>
            </div>
            <svg 
              className={`w-5 h-5 transition-transform ${evidenceExpanded ? 'rotate-180' : ''}`}
              style={{ color: 'var(--text-tertiary)' }}
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Evidence table */}
          {evidenceExpanded && (
            <div className="border-t" style={{ borderColor: 'var(--border-light)' }}>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ backgroundColor: 'var(--bg-page)' }}>
                    <th className="text-left p-3 font-medium" style={{ color: 'var(--text-tertiary)' }}>#</th>
                    <th className="text-left p-3 font-medium" style={{ color: 'var(--text-tertiary)' }}>Title</th>
                    <th className="text-left p-3 font-medium" style={{ color: 'var(--text-tertiary)' }}>Authors</th>
                    <th className="text-left p-3 font-medium" style={{ color: 'var(--text-tertiary)' }}>Year</th>
                    <th className="text-left p-3 font-medium" style={{ color: 'var(--text-tertiary)' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((source) => (
                    <tr 
                      key={source.citationId}
                      id={`source-${source.citationId}`}
                      className="border-t cursor-pointer transition-colors"
                      style={{ borderColor: 'var(--border-subtle)' }}
                      onClick={() => onSourceClick?.(source)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--bg-page)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <td className="p-3">
                        <span 
                          className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold"
                          style={{ backgroundColor: 'var(--accent-blue)', color: 'white' }}
                        >
                          {source.citationId}
                        </span>
                      </td>
                      <td 
                        className="p-3 max-w-xs truncate" 
                        style={{ color: 'var(--text-primary)' }}
                        title={source.title}
                      >
                        {source.title}
                      </td>
                      <td className="p-3" style={{ color: 'var(--text-secondary)' }}>
                        {source.authors.slice(0, 2).join(', ')}
                        {source.authors.length > 2 && ' et al.'}
                      </td>
                      <td className="p-3" style={{ color: 'var(--text-tertiary)' }}>
                        {source.year || '—'}
                      </td>
                      <td className="p-3">
                        {(source.url || source.doi) && (
                          <a
                            href={source.url || `https://doi.org/${source.doi}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-1.5 rounded-lg inline-flex transition-colors"
                            style={{ color: 'var(--text-tertiary)' }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = 'var(--border-light)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = 'transparent';
                            }}
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Methodology note */}
      <p 
        className="text-xs text-center pt-2"
        style={{ color: 'var(--text-tertiary)' }}
      >
        Synthesized from {papersAnalyzed} papers • All claims linked to sources
      </p>
    </div>
  );
}

// Answer section component with collapsible behavior
function AnswerSection({
  title,
  icon,
  badge,
  children,
  isOpen,
  onToggle,
  accentColor = 'var(--accent-blue)',
}: {
  title: string;
  icon: string;
  badge?: string;
  children: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  accentColor?: string;
}) {
  return (
    <div 
      className="border rounded-xl overflow-hidden"
      style={{ borderColor: 'var(--border-light)' }}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 transition-colors"
        style={{ backgroundColor: 'var(--bg-card)' }}
      >
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            {title}
          </span>
          {badge && (
            <span 
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ 
                backgroundColor: `${accentColor}15`,
                color: accentColor,
              }}
            >
              {badge}
            </span>
          )}
        </div>
        <svg 
          className={`w-5 h-5 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          style={{ color: 'var(--text-tertiary)' }}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <div 
          className="p-4 border-t"
          style={{ 
            backgroundColor: 'var(--bg-page)',
            borderColor: 'var(--border-subtle)',
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
}

// Tool step component
function ToolStep({ 
  icon, 
  label, 
  value, 
  complete 
}: { 
  icon: string; 
  label: string; 
  value: string; 
  complete: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <span style={{ color: complete ? 'var(--accent-green)' : 'var(--text-tertiary)' }}>
        {icon}
      </span>
      <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ color: 'var(--text-tertiary)' }}>({value})</span>
    </div>
  );
}

// Parse structured content from markdown-like format
function parseStructuredContent(content: string) {
  const sections = {
    summary: '',
    keyFindings: [] as string[],
    conflicts: [] as string[],
    openQuestions: [] as string[],
    raw: content,
  };

  // Try to extract summary
  const summaryMatch = content.match(/^(.+?)(?=\n\n\*\*|$)/s);
  if (summaryMatch) {
    sections.summary = summaryMatch[1].trim();
  }

  // Extract key findings
  const findingsMatch = content.match(/\*\*Key Findings:?\*\*\n([\s\S]*?)(?=\n\n\*\*|$)/i);
  if (findingsMatch) {
    sections.keyFindings = findingsMatch[1]
      .split('\n')
      .filter(line => line.trim().startsWith('•') || line.trim().startsWith('-'))
      .map(line => line.replace(/^[•-]\s*/, '').trim());
  }

  // Extract conflicts/consensus (treating consensus as potential conflicts)
  const conflictsMatch = content.match(/\*\*(?:Scientific Consensus|Conflicting Evidence|Consensus):?\*\*\n([\s\S]*?)(?=\n\n\*\*|$)/i);
  if (conflictsMatch) {
    sections.conflicts = conflictsMatch[1]
      .split('\n')
      .filter(line => line.trim().startsWith('•') || line.trim().startsWith('-'))
      .map(line => line.replace(/^[•-]\s*/, '').trim());
  }

  // Extract open questions
  const questionsMatch = content.match(/\*\*Open Questions:?\*\*\n([\s\S]*?)(?=\n\n\*\*|$)/i);
  if (questionsMatch) {
    sections.openQuestions = questionsMatch[1]
      .split('\n')
      .filter(line => line.trim().startsWith('•') || line.trim().startsWith('-'))
      .map(line => line.replace(/^[•-]\s*/, '').trim());
  }

  return sections;
}

// Render content with clickable citation pills
function renderContentWithCitations(
  text: string, 
  sources: Source[], 
  onSourceClick?: (source: Source) => void
) {
  const parts = text.split(/(\[\d+\])/g);
  
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1]);
      const source = sources.find(s => s.citationId === num);
      return (
        <CitationTooltip
          key={i}
          source={source || { citationId: num, paperId: '', title: '', authors: [], year: null, venue: null, doi: null, url: null }}
          onSourceClick={(s) => onSourceClick?.(s)}
        >
          <span 
            className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-semibold cursor-pointer mx-0.5 transition-colors"
            style={{ 
              backgroundColor: 'var(--accent-blue)',
              color: 'white',
            }}
            title={source?.title || `Citation ${num}`}
          >
            {num}
          </span>
        </CitationTooltip>
      );
    }
    return <span key={i}>{part}</span>;
  });
}
