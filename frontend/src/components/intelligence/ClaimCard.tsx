'use client';

import { useState } from 'react';
import type { Claim, ClaimEvidenceMap, EvidenceItem } from '@/lib/api';

interface ClaimCardProps {
  claim: Claim;
  evidenceMap?: ClaimEvidenceMap;
  onExpand?: () => void;
  onViewEvidence?: (claimId: string) => void;
  compact?: boolean;
}

export function ClaimCard({ claim, evidenceMap, onExpand, onViewEvidence, compact = false }: ClaimCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getClaimTypeConfig = (type: string) => {
    switch (type) {
      case 'finding':
        return { label: 'Finding', color: 'bg-blue-100 text-blue-700 border-blue-200' };
      case 'methodology':
        return { label: 'Methodology', color: 'bg-purple-100 text-purple-700 border-purple-200' };
      case 'hypothesis':
        return { label: 'Hypothesis', color: 'bg-amber-100 text-amber-700 border-amber-200' };
      case 'definition':
        return { label: 'Definition', color: 'bg-green-100 text-green-700 border-green-200' };
      default:
        return { label: type, color: 'bg-zinc-100 text-zinc-700 border-zinc-200' };
    }
  };

  const typeConfig = getClaimTypeConfig(claim.claim_type);
  const consensusScore = evidenceMap?.consensus_score ?? claim.consensus_score ?? 0;
  const evidenceStrength = evidenceMap?.evidence_strength ?? claim.evidence_strength ?? 0;

  const supporting = evidenceMap?.supporting ?? [];
  const opposing = evidenceMap?.opposing ?? [];
  const conditional = evidenceMap?.conditional ?? [];

  return (
    <div
      className={`rounded-xl border transition-all duration-200 ${
        isExpanded ? 'shadow-lg' : 'hover:shadow-md'
      }`}
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      {/* Claim Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1">
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${typeConfig.color}`}>
              {typeConfig.label}
            </span>
            {claim.has_quantitative_data && (
              <span className="ml-2 inline-block px-2 py-0.5 rounded text-xs font-medium bg-cyan-100 text-cyan-700 border border-cyan-200">
                Quantitative
              </span>
            )}
          </div>
          <ConsensusIndicator score={consensusScore} />
        </div>

        <p
          className="text-sm font-medium leading-relaxed"
          style={{ color: 'var(--text-primary)' }}
        >
          {claim.canonical_text}
        </p>

        {claim.effect_magnitude && (
          <div className="mt-2 flex items-center gap-2">
            <EffectBadge direction={claim.effect_direction} magnitude={claim.effect_magnitude} />
          </div>
        )}

        {!compact && claim.domain_tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {claim.domain_tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 rounded-full text-xs"
                style={{
                  backgroundColor: 'var(--bg-page)',
                  color: 'var(--text-tertiary)',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Evidence Summary */}
      {!compact && (
        <div
          className="px-5 py-3 border-t"
          style={{ borderColor: 'var(--border-subtle)', backgroundColor: 'var(--bg-page)' }}
        >
          <div className="flex items-center gap-4 mb-3">
            <EvidenceCount count={claim.supporting_count || supporting.length} label="Supporting" color="green" />
            <EvidenceCount count={claim.opposing_count || opposing.length} label="Opposing" color="red" />
            <EvidenceCount count={claim.conditional_count || conditional.length} label="Conditional" color="amber" />
          </div>

          {/* Evidence Strength Bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs mb-1">
              <span style={{ color: 'var(--text-tertiary)' }}>Evidence Strength</span>
              <span style={{ color: 'var(--text-secondary)' }}>{Math.round(evidenceStrength * 100)}%</span>
            </div>
            <div
              className="h-1.5 rounded-full overflow-hidden"
              style={{ backgroundColor: 'var(--border-light)' }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${evidenceStrength * 100}%`,
                  background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))',
                }}
              />
            </div>
          </div>

          {/* Expand Button */}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setIsExpanded(!isExpanded);
                if (!isExpanded && onExpand) onExpand();
              }}
              className="flex-1 py-2 text-xs font-medium rounded-lg transition-colors"
              style={{
                backgroundColor: 'var(--bg-card)',
                color: 'var(--accent-blue)',
                border: '1px solid var(--border-light)',
              }}
            >
              {isExpanded ? 'Hide Details' : 'View Details'}
            </button>
            {onViewEvidence && (
              <button
                onClick={() => onViewEvidence(claim.id)}
                className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
                style={{
                  backgroundColor: 'var(--accent-blue)',
                  color: 'white',
                }}
              >
                All Evidence →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Expanded Evidence Preview */}
      {isExpanded && evidenceMap && (
        <div
          className="px-5 pb-5 space-y-4 border-t animate-fadeIn"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          {supporting.length > 0 && (
            <EvidenceSection title="Supporting Evidence" items={supporting.slice(0, 2)} color="green" />
          )}
          {opposing.length > 0 && (
            <EvidenceSection title="Opposing Evidence" items={opposing.slice(0, 2)} color="red" />
          )}
          {conditional.length > 0 && (
            <EvidenceSection title="Conditional Evidence" items={conditional.slice(0, 2)} color="amber" />
          )}
        </div>
      )}
    </div>
  );
}

// Sub-components

function ConsensusIndicator({ score }: { score: number }) {
  const getConfig = () => {
    if (score >= 0.6) return { label: 'Strong Consensus', color: 'bg-green-50 text-green-700 border-green-200' };
    if (score >= 0.2) return { label: 'Moderate', color: 'bg-blue-50 text-blue-700 border-blue-200' };
    if (score >= -0.2) return { label: 'Mixed', color: 'bg-amber-50 text-amber-700 border-amber-200' };
    return { label: 'Contested', color: 'bg-red-50 text-red-700 border-red-200' };
  };

  const config = getConfig();

  return (
    <div className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${config.color}`}>
      {config.label}
    </div>
  );
}

function EffectBadge({ direction, magnitude }: { direction: string | null; magnitude: string }) {
  const getIcon = () => {
    switch (direction) {
      case 'positive': return '↑';
      case 'negative': return '↓';
      case 'mixed': return '↕';
      default: return '→';
    }
  };

  const getColor = () => {
    switch (direction) {
      case 'positive': return 'text-green-600 bg-green-50';
      case 'negative': return 'text-red-600 bg-red-50';
      case 'mixed': return 'text-amber-600 bg-amber-50';
      default: return 'text-zinc-600 bg-zinc-50';
    }
  };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${getColor()}`}>
      <span>{getIcon()}</span>
      <span>{magnitude}</span>
    </span>
  );
}

function EvidenceCount({ count, label, color }: { count: number; label: string; color: 'green' | 'red' | 'amber' }) {
  const colorClasses = {
    green: 'text-green-600',
    red: 'text-red-600',
    amber: 'text-amber-600',
  };

  return (
    <div className="flex items-center gap-1.5">
      <span className={`text-lg font-semibold ${colorClasses[color]}`}>{count}</span>
      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </span>
    </div>
  );
}

function EvidenceSection({ title, items, color }: { title: string; items: EvidenceItem[]; color: 'green' | 'red' | 'amber' }) {
  const borderColors = {
    green: 'border-l-green-400',
    red: 'border-l-red-400',
    amber: 'border-l-amber-400',
  };

  return (
    <div className="pt-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-tertiary)' }}>
        {title}
      </h4>
      <div className="space-y-2">
        {items.map((item, idx) => (
          <div
            key={idx}
            className={`pl-3 py-2 border-l-2 ${borderColors[color]}`}
            style={{ backgroundColor: 'var(--bg-card)' }}
          >
            <p className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
              {item.paper_title} {item.paper_year && `(${item.paper_year})`}
            </p>
            {item.quote && (
              <p className="text-xs mt-1 italic" style={{ color: 'var(--text-secondary)' }}>
                "{item.quote.slice(0, 150)}..."
              </p>
            )}
            {item.conditions.length > 0 && (
              <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
                Conditions: {item.conditions.join(', ')}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ClaimCard;
