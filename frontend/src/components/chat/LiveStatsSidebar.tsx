'use client';

import { memo } from 'react';
import { AgentActivityCard, type AgentActivity } from './AgentActivityCard';

export interface LiveStats {
  totalPapers: number;
  totalChunks: number;
  embeddedChunks: number;
  avgTokensPerChunk: number;
  recentQueries: number;
  processingStatus: 'idle' | 'searching' | 'processing' | 'embedding' | 'ready';
  lastUpdate: Date | null;
  // Extended stats
  papersWithAbstracts?: number;
  chunkedPapers?: number;
  embeddedPapers?: number;
  embeddingModel?: string;
  searchableChunks?: number;
  // Current search stats
  currentSearch?: {
    openalexCount: number;
    semanticScholarCount: number;
    newPapers: number;
    chunksCreated: number;
    duplicatesRemoved?: number;
    embeddingsCompleted?: number;
    embeddingsTotal?: number;
    elapsedMs?: number;
  };
}

interface LiveStatsSidebarProps {
  stats: LiveStats;
  isOpen: boolean;
  agentActivity?: AgentActivity;
  recentActivities?: AgentActivity[];
}

const LiveStatsSidebar = memo(function LiveStatsSidebar({ stats, isOpen, agentActivity, recentActivities }: LiveStatsSidebarProps) {
  if (!isOpen) return null;

  const embeddingPercent = stats.totalChunks > 0 
    ? Math.round((stats.embeddedChunks / stats.totalChunks) * 100) 
    : 0;

  const isProcessing = stats.processingStatus !== 'idle' && stats.processingStatus !== 'ready';

  // Default idle activity if none provided
  const currentActivity: AgentActivity = agentActivity || {
    type: 'idle',
    message: 'Ready to explore the scientific literature...',
  };

  return (
    <aside
      className="fixed right-0 top-16 bottom-0 w-80 z-40 overflow-hidden flex flex-col md:w-80 sm:w-full"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderLeft: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-sidebar)',
      }}
      role="complementary"
      aria-label="System status and knowledge base statistics"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
        
        {/* STATUS Section */}
        <section>
          <SectionHeader 
            title="System Status" 
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.348 14.652a3.75 3.75 0 0 1 0-5.304m5.304 0a3.75 3.75 0 0 1 0 5.304m-7.425 2.121a6.75 6.75 0 0 1 0-9.546m9.546 0a6.75 6.75 0 0 1 0 9.546M5.106 18.894c-3.808-3.807-3.808-9.98 0-13.788m13.788 0c3.808 3.807 3.808 9.98 0 13.788M12 12h.008v.008H12V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
            }
          />
          <StatusIndicator status={stats.processingStatus} />
          
          {/* Active search progress */}
          {stats.currentSearch && isProcessing && (
            <div 
              className="mt-4 p-4 rounded-xl animate-fadeIn space-y-4"
              style={{ backgroundColor: 'var(--bg-page)' }}
            >
              <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
                Current Query
              </div>
              
              {/* Tool activity list */}
              <div className="space-y-2">
                <ToolActivity 
                  label="OpenAlex" 
                  value={stats.currentSearch.openalexCount} 
                  status={stats.currentSearch.openalexCount > 0 ? 'done' : 'active'}
                />
                <ToolActivity 
                  label="Semantic Scholar" 
                  value={stats.currentSearch.semanticScholarCount} 
                  status={stats.currentSearch.semanticScholarCount > 0 ? 'done' : 'active'}
                />
                {stats.currentSearch.duplicatesRemoved !== undefined && (
                  <ToolActivity 
                    label="Deduplicated" 
                    value={stats.currentSearch.newPapers} 
                    status="done"
                    suffix="unique"
                  />
                )}
                <ToolActivity 
                  label="Text chunks" 
                  value={stats.currentSearch.chunksCreated} 
                  status={stats.currentSearch.chunksCreated > 0 ? 'done' : 'pending'}
                />
              </div>
              
              {/* Embedding progress */}
              {typeof stats.currentSearch.embeddingsTotal === 'number' && stats.currentSearch.embeddingsTotal > 0 && (
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span style={{ color: 'var(--text-tertiary)' }}>Embedding vectors</span>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {stats.currentSearch.embeddingsCompleted || 0} / {stats.currentSearch.embeddingsTotal}
                    </span>
                  </div>
                  <ProgressBar 
                    percent={Math.round(((stats.currentSearch.embeddingsCompleted || 0) / stats.currentSearch.embeddingsTotal) * 100)} 
                  />
                </div>
              )}
              
              {typeof stats.currentSearch.elapsedMs === 'number' && (
                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                  Elapsed: {(stats.currentSearch.elapsedMs / 1000).toFixed(1)}s
                </p>
              )}
            </div>
          )}
        </section>

        {/* KNOWLEDGE BASE Section */}
        <section>
          <SectionHeader
            title="Knowledge Base"
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
              </svg>
            }
          />
          <div className="grid grid-cols-2 gap-4 mt-4">
            <StatCard label="Papers" value={stats.totalPapers} isLoading={stats.lastUpdate === null} />
            <StatCard label="Chunks" value={stats.totalChunks} isLoading={stats.lastUpdate === null} />
          </div>
          
          {/* Embedding progress */}
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span style={{ color: 'var(--text-tertiary)' }}>Embeddings</span>
              <span style={{ color: 'var(--text-primary)' }}>
                {stats.embeddedChunks.toLocaleString()} / {stats.totalChunks.toLocaleString()}
              </span>
            </div>
            <ProgressBar percent={embeddingPercent} />
            <p className="text-xs mt-1.5" style={{ color: 'var(--text-tertiary)' }}>
              {embeddingPercent}% of chunks are searchable
            </p>
          </div>
        </section>

        {/* METHODOLOGY Section */}
        <section>
          <SectionHeader 
            title="Methodology"
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5" />
              </svg>
            }
          />
          <div className="space-y-3 mt-4">
            <MethodItem label="Data Sources" value="OpenAlex, Semantic Scholar" />
            <MethodItem label="Embedding Model" value="text-embedding-3-small" />
            <MethodItem label="Chunk Size" value={`~${stats.avgTokensPerChunk || 500} tokens`} />
            <MethodItem label="Similarity" value="Cosine distance (pgvector)" />
          </div>
        </section>

        {/* HOW IT WORKS Section */}
        <section>
          <SectionHeader 
            title="Evidence Pipeline"
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
              </svg>
            }
          />
          <div className="mt-4 space-y-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <PipelineStep number={1} text="Parse query into search terms" />
            <PipelineStep number={2} text="Fetch papers from literature APIs" />
            <PipelineStep number={3} text="Deduplicate by DOI and title" />
            <PipelineStep number={4} text="Chunk abstracts into segments" />
            <PipelineStep number={5} text="Generate vector embeddings" />
            <PipelineStep number={6} text="Retrieve relevant passages" />
            <PipelineStep number={7} text="Synthesize answer with citations" />
          </div>
        </section>

      </div>

      {/* Footer with timestamp */}
      {stats.lastUpdate && (
        <div
          className="px-6 py-3 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <p className="text-xs text-center" style={{ color: 'var(--text-tertiary)' }}>
            Updated: {stats.lastUpdate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
          </p>
        </div>
      )}

      {/* Agent Activity Card - Fixed at bottom */}
      <div className="flex-shrink-0 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
        <AgentActivityCard
          activity={currentActivity}
          recentActivities={recentActivities || []}
        />
      </div>
    </aside>
  );
});

LiveStatsSidebar.displayName = 'LiveStatsSidebar';

export { LiveStatsSidebar };

// Section header component
function SectionHeader({ title, icon }: { title: string; icon?: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      {icon && (
        <span style={{ color: 'var(--text-tertiary)' }}>
          {icon}
        </span>
      )}
      <h3 
        className="text-xs font-semibold uppercase tracking-wider"
        style={{ color: 'var(--text-tertiary)' }}
      >
        {title}
      </h3>
    </div>
  );
}

// Status indicator component
function StatusIndicator({ status }: { status: LiveStats['processingStatus'] }) {
  const config = {
    idle: { 
      color: 'var(--text-tertiary)', 
      label: 'Idle', 
      sublabel: 'Ready to process queries',
      animated: false 
    },
    searching: { 
      color: 'var(--accent-blue)', 
      label: 'Searching', 
      sublabel: 'Querying literature APIs...',
      animated: true 
    },
    processing: { 
      color: 'var(--accent-purple)', 
      label: 'Processing', 
      sublabel: 'Chunking and embedding...',
      animated: true 
    },
    embedding: { 
      color: 'var(--accent-purple)', 
      label: 'Embedding', 
      sublabel: 'Generating vectors...',
      animated: true 
    },
    ready: { 
      color: 'var(--accent-green)', 
      label: 'Complete', 
      sublabel: 'Results synthesized',
      animated: false 
    },
  };

  const { color, label, sublabel, animated } = config[status];

  return (
    <div className="flex items-start gap-3 mt-4">
      <div
        className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${animated ? 'status-dot-animated' : ''}`}
        style={{ backgroundColor: color }}
      />
      <div>
        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {label}
        </p>
        <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          {sublabel}
        </p>
      </div>
    </div>
  );
}

// Stat card component
function StatCard({ label, value, isLoading = false }: { label: string; value: number; isLoading?: boolean }) {
  return (
    <div
      className="p-3 rounded-xl relative overflow-hidden"
      style={{ backgroundColor: 'var(--bg-page)' }}
    >
      {isLoading && (
        <div
          className="absolute inset-0 animate-shimmer"
          style={{
            background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
          }}
        />
      )}
      <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </p>
      <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--text-primary)' }}>
        {value.toLocaleString()}
      </p>
    </div>
  );
}

// Tool activity item
function ToolActivity({ 
  label, 
  value, 
  status,
  suffix = 'papers',
}: { 
  label: string; 
  value: number; 
  status: 'done' | 'active' | 'pending';
  suffix?: string;
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      {status === 'done' && (
        <span style={{ color: 'var(--accent-green)' }}>✓</span>
      )}
      {status === 'active' && (
        <span className="w-3 h-3 border-2 rounded-full animate-spin" style={{ borderColor: 'var(--border-light)', borderTopColor: 'var(--accent-blue)' }} />
      )}
      {status === 'pending' && (
        <span style={{ color: 'var(--text-tertiary)' }}>○</span>
      )}
      <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ color: 'var(--text-tertiary)' }}>({value} {suffix})</span>
    </div>
  );
}

// Method item
function MethodItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span style={{ color: 'var(--text-tertiary)' }}>{label}</span>
      <span style={{ color: 'var(--text-secondary)' }}>{value}</span>
    </div>
  );
}

// Pipeline step
function PipelineStep({ number, text }: { number: number; text: string }) {
  return (
    <div className="flex items-center gap-2">
      <span 
        className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0"
        style={{ 
          backgroundColor: 'var(--bg-page)',
          border: '1px solid var(--border-light)',
          color: 'var(--text-tertiary)',
        }}
      >
        {number}
      </span>
      <span>{text}</span>
    </div>
  );
}

// Progress bar component
function ProgressBar({ percent }: { percent: number }) {
  return (
    <div
      className="h-1.5 rounded-full overflow-hidden"
      style={{ backgroundColor: 'var(--border-light)' }}
    >
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{
          width: `${percent}%`,
          backgroundColor: 'var(--accent-blue)',
        }}
      />
    </div>
  );
}
