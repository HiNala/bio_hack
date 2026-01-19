'use client';

import type { Contradiction } from '@/lib/api';

interface ContradictionCardProps {
  contradiction: Contradiction;
  paperATitle?: string;
  paperBTitle?: string;
  claimText?: string;
  onViewDetails?: () => void;
}

export function ContradictionCard({
  contradiction,
  paperATitle,
  paperBTitle,
  claimText,
  onViewDetails,
}: ContradictionCardProps) {
  const getSeverityConfig = (severity: number) => {
    if (severity >= 0.7) return { label: 'HIGH', color: 'bg-red-100 text-red-700 border-red-200', barColor: 'bg-red-500' };
    if (severity >= 0.4) return { label: 'MEDIUM', color: 'bg-amber-100 text-amber-700 border-amber-200', barColor: 'bg-amber-500' };
    return { label: 'LOW', color: 'bg-blue-100 text-blue-700 border-blue-200', barColor: 'bg-blue-500' };
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      methodological: '🔬',
      population: '👥',
      temporal: '⏱️',
      definitional: '📖',
      statistical: '📊',
      scope: '🎯',
    };
    return icons[type] || '⚡';
  };

  const getTypeDescription = (type: string) => {
    const descriptions: Record<string, string> = {
      methodological: 'Different methods yield different results',
      population: 'Results vary by population characteristics',
      temporal: 'Results changed over time',
      definitional: 'Different definitions of key terms',
      statistical: 'Same data, different interpretations',
      scope: 'Claims apply to different contexts',
    };
    return descriptions[type] || 'Scientific disagreement detected';
  };

  const severityConfig = getSeverityConfig(contradiction.severity);

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      {/* Severity Bar */}
      <div
        className={`h-1 ${severityConfig.barColor}`}
        style={{ width: `${contradiction.severity * 100}%` }}
      />

      {/* Header */}
      <div className="p-4 pb-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">{getTypeIcon(contradiction.contradiction_type)}</span>
            <div>
              <span
                className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: 'var(--text-tertiary)' }}
              >
                {contradiction.contradiction_type.replace('_', ' ')} Contradiction
              </span>
            </div>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${severityConfig.color}`}>
            {severityConfig.label} SEVERITY
          </span>
        </div>
        
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
          {getTypeDescription(contradiction.contradiction_type)}
        </p>
      </div>

      {/* Claim Context */}
      {claimText && (
        <div
          className="px-4 py-3 border-t border-b"
          style={{ borderColor: 'var(--border-subtle)', backgroundColor: 'var(--bg-page)' }}
        >
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
            Contested Claim:
          </span>
          <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>
            "{claimText}"
          </p>
        </div>
      )}

      {/* Conflicting Sources */}
      <div className="p-4">
        <div className="grid grid-cols-2 gap-3">
          {/* Paper A */}
          <div
            className="p-3 rounded-lg border-l-2 border-l-green-400"
            style={{ backgroundColor: 'var(--bg-page)' }}
          >
            <span className="text-xs font-medium text-green-600">Supporting</span>
            <p className="text-xs mt-1" style={{ color: 'var(--text-primary)' }}>
              {paperATitle || 'Paper A'}
            </p>
          </div>

          {/* Paper B */}
          <div
            className="p-3 rounded-lg border-l-2 border-l-red-400"
            style={{ backgroundColor: 'var(--bg-page)' }}
          >
            <span className="text-xs font-medium text-red-600">Opposing</span>
            <p className="text-xs mt-1" style={{ color: 'var(--text-primary)' }}>
              {paperBTitle || 'Paper B'}
            </p>
          </div>
        </div>

        {/* Explanation */}
        {contradiction.explanation && (
          <div className="mt-4">
            <span className="text-xs font-semibold" style={{ color: 'var(--text-tertiary)' }}>
              Analysis:
            </span>
            <p className="text-sm mt-1 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {contradiction.explanation}
            </p>
          </div>
        )}

        {/* Resolution Suggestion */}
        {contradiction.resolution_suggestion && (
          <div
            className="mt-4 p-3 rounded-lg"
            style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)' }}
          >
            <div className="flex items-start gap-2">
              <span className="text-blue-500">💡</span>
              <div>
                <span className="text-xs font-semibold text-blue-600">Resolution Path:</span>
                <p className="text-xs mt-1 text-blue-700">
                  {contradiction.resolution_suggestion}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* View Details Button */}
        {onViewDetails && (
          <button
            onClick={onViewDetails}
            className="w-full mt-4 py-2 text-xs font-medium rounded-lg transition-colors"
            style={{
              backgroundColor: 'var(--bg-page)',
              color: 'var(--accent-blue)',
              border: '1px solid var(--border-light)',
            }}
          >
            View Full Analysis →
          </button>
        )}
      </div>
    </div>
  );
}

export default ContradictionCard;
