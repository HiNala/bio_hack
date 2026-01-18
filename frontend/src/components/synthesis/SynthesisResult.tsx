'use client';

import { useState } from 'react';
import {
  SynthesisResponse,
  SynthesizeContent,
  CompareContent,
  PlanContent,
  ExploreContent,
  SourceReference,
  Finding,
} from '@/lib/api';

interface SynthesisResultProps {
  synthesis: SynthesisResponse;
  onSourceClick?: (source: SourceReference) => void;
  onFollowUp?: (question: string) => void;
}

// Citation component
function Citation({
  id,
  sources,
  onSourceClick,
}: {
  id: number;
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  const source = sources.find((s) => s.citation_id === id);
  if (!source) return <span className="text-blue-500">[{id}]</span>;

  return (
    <button
      onClick={() => onSourceClick?.(source)}
      className="text-blue-500 hover:text-blue-700 hover:underline transition-colors"
      title={source.title}
    >
      [{id}]
    </button>
  );
}

// Render citations in text
function RenderWithCitations({
  text,
  citations,
  sources,
  onSourceClick,
}: {
  text: string;
  citations: number[];
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  return (
    <span>
      {text}
      {citations.length > 0 && (
        <span className="ml-1">
          {citations.map((id, i) => (
            <span key={id}>
              {i > 0 && ', '}
              <Citation id={id} sources={sources} onSourceClick={onSourceClick} />
            </span>
          ))}
        </span>
      )}
    </span>
  );
}

// Finding with confidence badge
function FindingItem({
  finding,
  sources,
  onSourceClick,
}: {
  finding: Finding;
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  const confidenceColors = {
    high: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-zinc-100 text-zinc-600',
  };

  return (
    <li className="flex items-start gap-2">
      <span className="text-blue-500 mt-1">•</span>
      <div className="flex-1">
        <RenderWithCitations
          text={finding.finding}
          citations={finding.citations}
          sources={sources}
          onSourceClick={onSourceClick}
        />
        <span
          className={`ml-2 text-xs px-2 py-0.5 rounded-full ${confidenceColors[finding.confidence]}`}
        >
          {finding.confidence} confidence
        </span>
      </div>
    </li>
  );
}

// Synthesize mode content
function SynthesizeResult({
  content,
  sources,
  onSourceClick,
}: {
  content: SynthesizeContent;
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <section>
        <h3 className="text-lg font-semibold text-zinc-900 mb-2">Executive Summary</h3>
        <p className="text-zinc-700 leading-relaxed">{content.executive_summary}</p>
      </section>

      {/* Key Findings */}
      {content.key_findings && content.key_findings.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Key Findings</h3>
          <ul className="space-y-2">
            {content.key_findings.map((finding, i) => (
              <FindingItem
                key={i}
                finding={finding}
                sources={sources}
                onSourceClick={onSourceClick}
              />
            ))}
          </ul>
        </section>
      )}

      {/* Scientific Consensus */}
      {content.consensus && content.consensus.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Scientific Consensus</h3>
          <ul className="space-y-2">
            {content.consensus.map((point, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-green-500 mt-1">✓</span>
                <RenderWithCitations
                  text={point.point}
                  citations={point.citations}
                  sources={sources}
                  onSourceClick={onSourceClick}
                />
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Contested Findings */}
      {content.contested && content.contested.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Contested Findings</h3>
          <div className="space-y-4">
            {content.contested.map((topic, i) => (
              <div key={i} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="font-medium text-zinc-900 mb-2 flex items-center gap-2">
                  <span className="text-yellow-600">⚡</span>
                  {topic.topic}
                </div>
                <ul className="space-y-2">
                  {topic.positions.map((pos, j) => (
                    <li key={j} className="text-sm text-zinc-700 ml-6">
                      <RenderWithCitations
                        text={pos.position}
                        citations={pos.citations}
                        sources={sources}
                        onSourceClick={onSourceClick}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Limitations */}
      {content.limitations && content.limitations.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Limitations & Gaps</h3>
          <ul className="space-y-1">
            {content.limitations.map((limitation, i) => (
              <li key={i} className="flex items-start gap-2 text-zinc-600">
                <span className="text-zinc-400">•</span>
                {limitation}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

// Compare mode content
function CompareResult({
  content,
  sources,
  onSourceClick,
}: {
  content: CompareContent;
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Overview */}
      <section>
        <h3 className="text-lg font-semibold text-zinc-900 mb-2">Overview</h3>
        <p className="text-zinc-700 leading-relaxed">{content.overview}</p>
      </section>

      {/* Comparison Table */}
      {content.comparison_table && content.comparison_table.rows && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-zinc-100">
                  <th className="text-left p-3 text-sm font-semibold text-zinc-700 border">Category</th>
                  {content.approaches?.map((approach) => (
                    <th key={approach.name} className="text-left p-3 text-sm font-semibold text-zinc-700 border">
                      {approach.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {content.comparison_table.rows.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-zinc-50'}>
                    <td className="p-3 text-sm font-medium text-zinc-700 border">{row.category}</td>
                    {row.comparisons?.map((comp, j) => (
                      <td key={j} className="p-3 text-sm text-zinc-600 border">
                        <RenderWithCitations
                          text={comp.assessment}
                          citations={comp.citations}
                          sources={sources}
                          onSourceClick={onSourceClick}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Recommendations */}
      {content.recommendations && content.recommendations.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Recommendations</h3>
          <div className="space-y-3">
            {content.recommendations.map((rec, i) => (
              <div key={i} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="font-medium text-zinc-900 mb-1">
                  For {rec.use_case}: <span className="text-blue-600">{rec.recommended}</span>
                </div>
                <div className="text-sm text-zinc-600">{rec.rationale}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// Plan mode content
function PlanResult({
  content,
  sources,
  onSourceClick,
}: {
  content: PlanContent;
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Field Overview */}
      <section>
        <h3 className="text-lg font-semibold text-zinc-900 mb-2">Field Overview</h3>
        <p className="text-zinc-700 leading-relaxed">{content.field_overview}</p>
      </section>

      {/* Research Gaps */}
      {content.research_gaps && content.research_gaps.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Research Gaps</h3>
          <div className="space-y-3">
            {content.research_gaps.map((gap, i) => (
              <div key={i} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="font-medium text-zinc-900 mb-2">{gap.gap}</div>
                <div className="text-sm text-zinc-600 mb-2">{gap.evidence}</div>
                <div className="flex gap-4 text-xs">
                  <span className={`px-2 py-0.5 rounded ${
                    gap.impact_potential === 'high' ? 'bg-green-100 text-green-700' :
                    gap.impact_potential === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-zinc-100 text-zinc-600'
                  }`}>
                    Impact: {gap.impact_potential}
                  </span>
                  <span className={`px-2 py-0.5 rounded ${
                    gap.difficulty === 'low' ? 'bg-green-100 text-green-700' :
                    gap.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    Difficulty: {gap.difficulty}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Promising Directions */}
      {content.promising_directions && content.promising_directions.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Promising Directions</h3>
          <div className="space-y-3">
            {content.promising_directions.map((dir, i) => (
              <div key={i} className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="font-medium text-zinc-900 mb-2">{dir.direction}</div>
                <div className="text-sm text-zinc-600 mb-2">{dir.rationale}</div>
                <div className="text-sm text-zinc-500">
                  <strong>Suggested approach:</strong> {dir.suggested_approach}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Suggested Questions */}
      {content.suggested_research_questions && content.suggested_research_questions.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Research Questions to Explore</h3>
          <ul className="space-y-2">
            {content.suggested_research_questions.map((q, i) => (
              <li key={i} className="flex items-start gap-2 text-zinc-700">
                <span className="text-purple-500 mt-1">?</span>
                {q}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

// Explore mode content
function ExploreResult({
  content,
  sources,
  onSourceClick,
}: {
  content: ExploreContent;
  sources: SourceReference[];
  onSourceClick?: (source: SourceReference) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Topic Focus */}
      <section>
        <h3 className="text-lg font-semibold text-zinc-900 mb-2">{content.topic_focus}</h3>
        <p className="text-zinc-700 leading-relaxed whitespace-pre-line">{content.detailed_explanation}</p>
      </section>

      {/* Key Points */}
      {content.key_points && content.key_points.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Key Points</h3>
          <ul className="space-y-2">
            {content.key_points.map((point, i) => (
              <FindingItem
                key={i}
                finding={point}
                sources={sources}
                onSourceClick={onSourceClick}
              />
            ))}
          </ul>
        </section>
      )}

      {/* Technical Details */}
      {content.technical_details && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Technical Details</h3>
          <p className="text-zinc-700 leading-relaxed whitespace-pre-line bg-zinc-50 p-4 rounded-lg">
            {content.technical_details}
          </p>
        </section>
      )}

      {/* Related Concepts */}
      {content.related_concepts && content.related_concepts.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-zinc-900 mb-2">Related Concepts</h3>
          <div className="flex flex-wrap gap-2">
            {content.related_concepts.map((concept, i) => (
              <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {concept}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// Main component
export function SynthesisResult({ synthesis, onSourceClick, onFollowUp }: SynthesisResultProps) {
  const [showSources, setShowSources] = useState(false);
  const [followUpQuestion, setFollowUpQuestion] = useState('');

  const renderContent = () => {
    const content = synthesis.content;
    const sources = synthesis.sources;

    switch (synthesis.mode) {
      case 'synthesize':
        return <SynthesizeResult content={content as SynthesizeContent} sources={sources} onSourceClick={onSourceClick} />;
      case 'compare':
        return <CompareResult content={content as CompareContent} sources={sources} onSourceClick={onSourceClick} />;
      case 'plan':
        return <PlanResult content={content as PlanContent} sources={sources} onSourceClick={onSourceClick} />;
      case 'explore':
        return <ExploreResult content={content as ExploreContent} sources={sources} onSourceClick={onSourceClick} />;
      default:
        return <pre className="text-xs">{JSON.stringify(content, null, 2)}</pre>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between">
        <div>
          <div className="text-sm text-zinc-500 mb-1">
            {synthesis.mode.charAt(0).toUpperCase() + synthesis.mode.slice(1)} • {synthesis.total_papers_analyzed} papers analyzed
          </div>
          <div className="font-medium text-zinc-900">{synthesis.query}</div>
        </div>
        <div className="flex items-center gap-3">
          {synthesis.confidence_score !== null && (
            <div className={`text-xs px-2 py-1 rounded ${
              synthesis.confidence_score >= 0.7 ? 'bg-green-100 text-green-700' :
              synthesis.confidence_score >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
              'bg-zinc-100 text-zinc-600'
            }`}>
              {Math.round(synthesis.confidence_score * 100)}% confidence
            </div>
          )}
          <button
            onClick={() => setShowSources(!showSources)}
            className="text-sm text-blue-500 hover:text-blue-700"
          >
            {showSources ? 'Hide' : 'Show'} Sources ({synthesis.sources.length})
          </button>
        </div>
      </div>

      {/* Warning */}
      {synthesis.coverage_warning && (
        <div className="px-6 py-3 bg-yellow-50 border-b border-yellow-100 text-sm text-yellow-800">
          ⚠️ {synthesis.coverage_warning}
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {renderContent()}
      </div>

      {/* Sources Panel */}
      {showSources && (
        <div className="border-t border-zinc-100 bg-zinc-50 p-6">
          <h3 className="font-semibold text-zinc-900 mb-4">Sources ({synthesis.sources.length} papers)</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {synthesis.sources.map((source) => (
              <div
                key={source.paper_id}
                className="bg-white rounded-lg p-4 border border-zinc-200 hover:border-zinc-300 cursor-pointer transition-colors"
                onClick={() => onSourceClick?.(source)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="text-sm text-blue-500 mb-1">[{source.citation_id}]</div>
                    <div className="font-medium text-zinc-900 text-sm">{source.title}</div>
                    {source.authors.length > 0 && (
                      <div className="text-xs text-zinc-500 mt-1">
                        {source.authors.slice(0, 3).join(', ')}
                        {source.authors.length > 3 && ` +${source.authors.length - 3} more`}
                      </div>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-zinc-500">
                      {source.year && <span>{source.year}</span>}
                      <span>{source.citation_count} citations</span>
                      <span className="text-blue-500">
                        {Math.round(source.relevance_score * 100)}% relevance
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Follow-up */}
      {onFollowUp && (
        <div className="border-t border-zinc-100 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={followUpQuestion}
              onChange={(e) => setFollowUpQuestion(e.target.value)}
              placeholder="Ask a follow-up question..."
              className="flex-1 px-4 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && followUpQuestion.trim()) {
                  onFollowUp(followUpQuestion);
                  setFollowUpQuestion('');
                }
              }}
            />
            <button
              onClick={() => {
                if (followUpQuestion.trim()) {
                  onFollowUp(followUpQuestion);
                  setFollowUpQuestion('');
                }
              }}
              disabled={!followUpQuestion.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Ask
            </button>
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="border-t border-zinc-100 px-6 py-3 bg-zinc-50 flex items-center justify-between text-xs text-zinc-500">
        <span>Generated in {synthesis.generation_time_ms}ms • {synthesis.tokens_used} tokens</span>
        <span>Model: {synthesis.model}</span>
      </div>
    </div>
  );
}
