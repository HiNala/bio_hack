'use client';

import type { ConsensusReport, ConsensusItem, ContestedItem, ConditionalItem } from '@/lib/api';

interface ConsensusMeterProps {
  report: ConsensusReport;
  onClaimClick?: (claimId: string) => void;
  compact?: boolean;
}

export function ConsensusMeter({ report, onClaimClick, compact = false }: ConsensusMeterProps) {
  const score = report.overall_consensus_score;
  const percentage = Math.round(((score + 1) / 2) * 100); // Convert -1 to 1 scale to 0-100

  const getScoreLabel = () => {
    if (score >= 0.6) return { label: 'Strong Agreement', color: 'text-green-600' };
    if (score >= 0.2) return { label: 'Moderate Agreement', color: 'text-blue-600' };
    if (score >= -0.2) return { label: 'Mixed Evidence', color: 'text-amber-600' };
    return { label: 'Contested', color: 'text-red-600' };
  };

  const scoreConfig = getScoreLabel();

  return (
    <div
      className="rounded-xl border"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      {/* Header */}
      <div className="p-5 border-b" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center justify-between mb-4">
          <h3
            className="text-sm font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-tertiary)' }}
          >
            Consensus & Contradictions
          </h3>
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
            Topic: {report.topic}
          </span>
        </div>

        {/* Main Meter */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className={`font-medium ${scoreConfig.color}`}>{scoreConfig.label}</span>
            <span style={{ color: 'var(--text-secondary)' }}>{percentage}% Agreement</span>
          </div>
          <div
            className="h-3 rounded-full overflow-hidden"
            style={{ backgroundColor: 'var(--border-light)' }}
          >
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${percentage}%`,
                background: getGradientForScore(score),
              }}
            />
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-3">
          <StatBox
            count={report.consensus.length}
            label="Consensus"
            icon="✓"
            color="green"
          />
          <StatBox
            count={report.contested.length}
            label="Contested"
            icon="⚡"
            color="red"
          />
          <StatBox
            count={report.conditional.length}
            label="Conditional"
            icon="?"
            color="amber"
          />
        </div>
      </div>

      {!compact && (
        <>
          {/* Consensus Areas */}
          {report.consensus.length > 0 && (
            <Section
              title="Strong Consensus"
              icon="✓"
              iconColor="text-green-500"
            >
              {report.consensus.slice(0, 3).map((item, idx) => (
                <ConsensusItemCard
                  key={idx}
                  item={item}
                  onClick={() => onClaimClick?.(item.claim.id)}
                />
              ))}
            </Section>
          )}

          {/* Contested Areas */}
          {report.contested.length > 0 && (
            <Section
              title="Active Disagreements"
              icon="⚡"
              iconColor="text-red-500"
            >
              {report.contested.slice(0, 3).map((item, idx) => (
                <ContestedItemCard
                  key={idx}
                  item={item}
                  onClick={() => onClaimClick?.(item.claim.id)}
                />
              ))}
            </Section>
          )}

          {/* Conditional Findings */}
          {report.conditional.length > 0 && (
            <Section
              title="Conditional Findings"
              icon="📋"
              iconColor="text-amber-500"
            >
              {report.conditional.slice(0, 3).map((item, idx) => (
                <ConditionalItemCard
                  key={idx}
                  item={item}
                  onClick={() => onClaimClick?.(item.claim.id)}
                />
              ))}
            </Section>
          )}
        </>
      )}
    </div>
  );
}

// Helper function for gradient
function getGradientForScore(score: number): string {
  if (score >= 0.6) return 'linear-gradient(90deg, #22c55e, #16a34a)';
  if (score >= 0.2) return 'linear-gradient(90deg, #3b82f6, #2563eb)';
  if (score >= -0.2) return 'linear-gradient(90deg, #f59e0b, #d97706)';
  return 'linear-gradient(90deg, #ef4444, #dc2626)';
}

// Sub-components

function StatBox({ count, label, icon, color }: { count: number; label: string; icon: string; color: 'green' | 'red' | 'amber' }) {
  const bgColors = {
    green: 'bg-green-50',
    red: 'bg-red-50',
    amber: 'bg-amber-50',
  };

  return (
    <div
      className={`p-3 rounded-lg ${bgColors[color]}`}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-sm">{icon}</span>
        <span className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {count}
        </span>
      </div>
      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </span>
    </div>
  );
}

function Section({ title, icon, iconColor, children }: { title: string; icon: string; iconColor: string; children: React.ReactNode }) {
  return (
    <div className="p-5 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
      <div className="flex items-center gap-2 mb-3">
        <span className={iconColor}>{icon}</span>
        <h4 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
          {title}
        </h4>
      </div>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  );
}

function ConsensusItemCard({ item, onClick }: { item: ConsensusItem; onClick?: () => void }) {
  return (
    <div
      className="p-3 rounded-lg cursor-pointer transition-all hover:shadow-sm"
      style={{ backgroundColor: 'var(--bg-page)' }}
      onClick={onClick}
    >
      <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
        {item.claim.canonical_text.slice(0, 120)}
        {item.claim.canonical_text.length > 120 && '...'}
      </p>
      <div className="flex items-center gap-3 mt-2">
        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          Consensus: {Math.round(item.score * 100)}%
        </span>
        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          • {item.evidence_count} papers
        </span>
      </div>
    </div>
  );
}

function ContestedItemCard({ item, onClick }: { item: ContestedItem; onClick?: () => void }) {
  const severityLabel = item.severity >= 0.7 ? 'HIGH' : item.severity >= 0.4 ? 'MEDIUM' : 'LOW';
  const severityColor = item.severity >= 0.7 ? 'text-red-600 bg-red-50' : item.severity >= 0.4 ? 'text-amber-600 bg-amber-50' : 'text-blue-600 bg-blue-50';

  return (
    <div
      className="p-3 rounded-lg cursor-pointer transition-all hover:shadow-sm border-l-2 border-l-red-400"
      style={{ backgroundColor: 'var(--bg-page)' }}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm flex-1" style={{ color: 'var(--text-primary)' }}>
          {item.claim.canonical_text.slice(0, 100)}
          {item.claim.canonical_text.length > 100 && '...'}
        </p>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColor}`}>
          {severityLabel}
        </span>
      </div>
      <div className="flex items-center gap-3 mt-2">
        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          {item.contradictions.length} contradiction{item.contradictions.length !== 1 && 's'}
        </span>
        {item.contradictions[0] && (
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
            • Type: {item.contradictions[0].contradiction_type}
          </span>
        )}
      </div>
    </div>
  );
}

function ConditionalItemCard({ item, onClick }: { item: ConditionalItem; onClick?: () => void }) {
  return (
    <div
      className="p-3 rounded-lg cursor-pointer transition-all hover:shadow-sm border-l-2 border-l-amber-400"
      style={{ backgroundColor: 'var(--bg-page)' }}
      onClick={onClick}
    >
      <p className="text-sm" style={{ color: 'var(--text-primary)' }}>
        {item.claim.canonical_text.slice(0, 100)}
        {item.claim.canonical_text.length > 100 && '...'}
      </p>
      {item.conditions.length > 0 && (
        <div className="mt-2">
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
            Depends on: {item.conditions.slice(0, 3).join(', ')}
            {item.conditions.length > 3 && ` +${item.conditions.length - 3} more`}
          </span>
        </div>
      )}
    </div>
  );
}

export default ConsensusMeter;
