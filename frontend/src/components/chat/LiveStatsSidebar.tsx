'use client';

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
}

export function LiveStatsSidebar({ stats, isOpen }: LiveStatsSidebarProps) {
  if (!isOpen) return null;

  const embeddingPercent = stats.totalChunks > 0 
    ? Math.round((stats.embeddedChunks / stats.totalChunks) * 100) 
    : 0;

  return (
    <aside
      className="fixed right-0 top-16 bottom-0 w-80 z-40 overflow-hidden flex flex-col"
      style={{
        backgroundColor: 'var(--bg-card)',
        borderLeft: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-sidebar)',
      }}
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
        
        {/* STATUS Section */}
        <section>
          <SectionHeader title="STATUS" />
          <StatusIndicator status={stats.processingStatus} />
          
          {/* Active search progress */}
          {stats.currentSearch && stats.processingStatus !== 'idle' && (
            <div 
              className="mt-4 p-4 rounded-xl animate-fadeIn"
              style={{ backgroundColor: 'var(--bg-page)' }}
            >
              <div className="grid grid-cols-2 gap-3">
                <MiniStat label="OpenAlex" value={stats.currentSearch.openalexCount} />
                <MiniStat label="Semantic Scholar" value={stats.currentSearch.semanticScholarCount} />
                <MiniStat label="New Papers" value={stats.currentSearch.newPapers} highlight />
                <MiniStat label="Chunks" value={stats.currentSearch.chunksCreated} highlight />
              </div>
              
              {typeof stats.currentSearch.embeddingsTotal === 'number' && stats.currentSearch.embeddingsTotal > 0 && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span style={{ color: 'var(--text-tertiary)' }}>Embedding progress</span>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {stats.currentSearch.embeddingsCompleted || 0}/{stats.currentSearch.embeddingsTotal}
                    </span>
                  </div>
                  <ProgressBar 
                    percent={Math.round(((stats.currentSearch.embeddingsCompleted || 0) / stats.currentSearch.embeddingsTotal) * 100)} 
                  />
                </div>
              )}
              
              {typeof stats.currentSearch.elapsedMs === 'number' && (
                <p className="text-xs mt-3" style={{ color: 'var(--text-tertiary)' }}>
                  Elapsed: {(stats.currentSearch.elapsedMs / 1000).toFixed(1)}s
                </p>
              )}
            </div>
          )}
        </section>

        {/* DATABASE Section */}
        <section>
          <SectionHeader title="DATABASE" />
          <div className="space-y-5">
            <StatCard label="Total Papers" value={stats.totalPapers} />
            <StatCard label="Total Chunks" value={stats.totalChunks} />
            <div>
              <StatCard label="Embeddings" value={`${stats.embeddedChunks} / ${stats.totalChunks}`} />
              <div className="mt-2">
                <ProgressBar percent={embeddingPercent} />
              </div>
            </div>
            <StatCard label="Avg Tokens/Chunk" value={Math.round(stats.avgTokensPerChunk)} />
          </div>
        </section>

        {/* HOW IT WORKS Section */}
        <section>
          <SectionHeader title="HOW IT WORKS" />
          <p 
            className="text-sm leading-relaxed"
            style={{ color: 'var(--text-secondary)' }}
          >
            Papers are fetched from OpenAlex & Semantic Scholar, chunked for semantic search, then embedded using AI for similarity matching.
          </p>
        </section>
      </div>

      {/* Footer with timestamp */}
      {stats.lastUpdate && (
        <div 
          className="px-6 py-4 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <p className="text-xs text-center" style={{ color: 'var(--text-tertiary)' }}>
            Updated: {stats.lastUpdate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
          </p>
        </div>
      )}
    </aside>
  );
}

// Section header component
function SectionHeader({ title }: { title: string }) {
  return (
    <h3 
      className="text-xs font-semibold uppercase tracking-wider mb-4"
      style={{ color: 'var(--text-tertiary)' }}
    >
      {title}
    </h3>
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
      sublabel: 'Fetching from APIs...',
      animated: true 
    },
    processing: { 
      color: 'var(--accent-purple)', 
      label: 'Processing', 
      sublabel: 'Analyzing papers...',
      animated: true 
    },
    embedding: { 
      color: 'var(--accent-purple)', 
      label: 'Embedding', 
      sublabel: 'Creating vectors...',
      animated: true 
    },
    ready: { 
      color: 'var(--accent-green)', 
      label: 'Complete', 
      sublabel: 'Results ready',
      animated: false 
    },
  };

  const { color, label, sublabel, animated } = config[status];

  return (
    <div className="flex items-start gap-3">
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
function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-sm mb-1" style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </p>
      <p className="text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
    </div>
  );
}

// Mini stat for current search
function MiniStat({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{label}</p>
      <p 
        className="text-lg font-semibold"
        style={{ color: highlight ? 'var(--accent-blue)' : 'var(--text-primary)' }}
      >
        {value.toLocaleString()}
      </p>
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
