'use client';

import { useState, useEffect } from 'react';
import { ClaimCard } from './ClaimCard';
import { ConsensusMeter } from './ConsensusMeter';
import { ContradictionCard } from './ContradictionCard';
import { ResearchSessionPanel } from './ResearchSessionPanel';
import type {
  Claim,
  ClaimEvidenceMap,
  ConsensusReport,
  Contradiction,
  ResearchSession,
  ResearchContext,
  TimelineEvent,
} from '@/lib/api';

interface IntelligencePanelProps {
  // Claims data
  claims?: Claim[];
  selectedClaimEvidence?: ClaimEvidenceMap;
  onClaimSelect?: (claimId: string) => void;

  // Consensus data
  consensusReport?: ConsensusReport;

  // Contradiction data
  contradictions?: Contradiction[];
  onContradictionSelect?: (contradictionId: string) => void;

  // Research session data
  currentSession?: ResearchSession;
  sessionContext?: ResearchContext;
  sessionTimeline?: { events: TimelineEvent[]; total_queries: number; total_insights: number };
  onViewTimeline?: () => void;

  // Loading states
  isLoading?: boolean;
  activeTab?: 'claims' | 'consensus' | 'memory';
  onTabChange?: (tab: 'claims' | 'consensus' | 'memory') => void;
}

export function IntelligencePanel({
  claims = [],
  selectedClaimEvidence,
  onClaimSelect,
  consensusReport,
  contradictions = [],
  onContradictionSelect,
  currentSession,
  sessionContext,
  sessionTimeline,
  onViewTimeline,
  isLoading = false,
  activeTab = 'claims',
  onTabChange,
}: IntelligencePanelProps) {
  const [localTab, setLocalTab] = useState<'claims' | 'consensus' | 'memory'>(activeTab);
  
  useEffect(() => {
    setLocalTab(activeTab);
  }, [activeTab]);

  const handleTabChange = (tab: 'claims' | 'consensus' | 'memory') => {
    setLocalTab(tab);
    onTabChange?.(tab);
  };

  const hasClaimsData = claims.length > 0;
  const hasConsensusData = consensusReport != null;
  const hasMemoryData = currentSession != null;

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 border-b"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🧠</span>
          <h3
            className="text-sm font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >
            Intelligence Layer
          </h3>
        </div>
      </div>

      {/* Tab Navigation */}
      <div
        className="flex border-b"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <TabButton
          active={localTab === 'claims'}
          onClick={() => handleTabChange('claims')}
          icon="📋"
          label="Claims"
          badge={claims.length || undefined}
        />
        <TabButton
          active={localTab === 'consensus'}
          onClick={() => handleTabChange('consensus')}
          icon="⚖️"
          label="Consensus"
          badge={consensusReport ? contradictions.length : undefined}
        />
        <TabButton
          active={localTab === 'memory'}
          onClick={() => handleTabChange('memory')}
          icon="🔬"
          label="Session"
          badge={sessionTimeline?.total_insights || undefined}
        />
      </div>

      {/* Content */}
      <div className="p-4 max-h-[500px] overflow-y-auto custom-scrollbar">
        {isLoading ? (
          <LoadingState />
        ) : (
          <>
            {localTab === 'claims' && (
              <ClaimsTab
                claims={claims}
                selectedEvidence={selectedClaimEvidence}
                onClaimSelect={onClaimSelect}
                hasData={hasClaimsData}
              />
            )}
            {localTab === 'consensus' && (
              <ConsensusTab
                report={consensusReport}
                contradictions={contradictions}
                onContradictionSelect={onContradictionSelect}
                hasData={hasConsensusData}
              />
            )}
            {localTab === 'memory' && (
              <MemoryTab
                session={currentSession}
                context={sessionContext}
                timeline={sessionTimeline}
                onViewTimeline={onViewTimeline}
                hasData={hasMemoryData}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

// Sub-components

function TabButton({
  active,
  onClick,
  icon,
  label,
  badge,
}: {
  active: boolean;
  onClick: () => void;
  icon: string;
  label: string;
  badge?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
        active
          ? 'border-b-2 border-blue-500'
          : 'hover:bg-zinc-50'
      }`}
      style={{
        color: active ? 'var(--accent-blue)' : 'var(--text-tertiary)',
        backgroundColor: active ? 'transparent' : 'transparent',
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span
          className="px-1.5 py-0.5 rounded-full text-xs"
          style={{
            backgroundColor: active ? 'var(--accent-blue)' : 'var(--border-light)',
            color: active ? 'white' : 'var(--text-tertiary)',
          }}
        >
          {badge}
        </span>
      )}
    </button>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-center">
        <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
        <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
          Analyzing intelligence...
        </p>
      </div>
    </div>
  );
}

function EmptyState({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="text-center py-8">
      <span className="text-3xl mb-3 block">{icon}</span>
      <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
        {title}
      </p>
      <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
        {description}
      </p>
    </div>
  );
}

function ClaimsTab({
  claims,
  selectedEvidence,
  onClaimSelect,
  hasData,
}: {
  claims: Claim[];
  selectedEvidence?: ClaimEvidenceMap;
  onClaimSelect?: (claimId: string) => void;
  hasData: boolean;
}) {
  if (!hasData) {
    return (
      <EmptyState
        icon="📋"
        title="No claims extracted yet"
        description="Claims will appear here as papers are analyzed"
      />
    );
  }

  return (
    <div className="space-y-3">
      {claims.slice(0, 5).map((claim) => (
        <ClaimCard
          key={claim.id}
          claim={claim}
          evidenceMap={selectedEvidence?.claim.id === claim.id ? selectedEvidence : undefined}
          onExpand={() => onClaimSelect?.(claim.id)}
          compact
        />
      ))}
      {claims.length > 5 && (
        <button
          className="w-full py-2 text-xs font-medium text-center rounded-lg"
          style={{
            backgroundColor: 'var(--bg-page)',
            color: 'var(--accent-blue)',
          }}
        >
          View all {claims.length} claims →
        </button>
      )}
    </div>
  );
}

function ConsensusTab({
  report,
  contradictions,
  onContradictionSelect,
  hasData,
}: {
  report?: ConsensusReport;
  contradictions: Contradiction[];
  onContradictionSelect?: (id: string) => void;
  hasData: boolean;
}) {
  if (!hasData || !report) {
    return (
      <EmptyState
        icon="⚖️"
        title="No consensus data available"
        description="Consensus analysis requires extracted claims"
      />
    );
  }

  return (
    <div className="space-y-4">
      <ConsensusMeter report={report} compact />
      
      {contradictions.length > 0 && (
        <div className="pt-4 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
          <h4
            className="text-xs font-semibold mb-3"
            style={{ color: 'var(--text-tertiary)' }}
          >
            Key Contradictions ({contradictions.length})
          </h4>
          <div className="space-y-2">
            {contradictions.slice(0, 2).map((c) => (
              <ContradictionCard
                key={c.id}
                contradiction={c}
                onViewDetails={() => onContradictionSelect?.(c.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MemoryTab({
  session,
  context,
  timeline,
  onViewTimeline,
  hasData,
}: {
  session?: ResearchSession;
  context?: ResearchContext;
  timeline?: { events: TimelineEvent[]; total_queries: number; total_insights: number };
  onViewTimeline?: () => void;
  hasData: boolean;
}) {
  if (!hasData || !session) {
    return (
      <EmptyState
        icon="🔬"
        title="No active research session"
        description="Start a query to begin tracking your research"
      />
    );
  }

  return (
    <ResearchSessionPanel
      session={session}
      context={context}
      timeline={timeline}
      onViewTimeline={onViewTimeline}
      isActive
    />
  );
}

export default IntelligencePanel;
