'use client';

import { useEffect, useState } from 'react';

export interface LiveStats {
  totalPapers: number;
  totalChunks: number;
  embeddedChunks: number;
  avgTokensPerChunk: number;
  recentQueries: number;
  processingStatus: 'idle' | 'searching' | 'processing' | 'embedding' | 'ready';
  lastUpdate: Date | null;
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
  const [pulse, setPulse] = useState(false);

  // Pulse animation when stats update
  useEffect(() => {
    setPulse(true);
    const timer = setTimeout(() => setPulse(false), 500);
    return () => clearTimeout(timer);
  }, [stats.totalPapers, stats.totalChunks]);

  const getStatusColor = (status: LiveStats['processingStatus']) => {
    switch (status) {
      case 'searching': return 'var(--accent-primary)';
      case 'processing': return 'var(--accent-warning)';
      case 'embedding': return 'var(--accent-success)';
      case 'ready': return 'var(--accent-success)';
      default: return 'var(--text-muted)';
    }
  };

  const getStatusLabel = (status: LiveStats['processingStatus']) => {
    switch (status) {
      case 'searching': return 'Searching APIs...';
      case 'processing': return 'Processing papers...';
      case 'embedding': return 'Creating embeddings...';
      case 'ready': return 'Ready';
      default: return 'Idle';
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed right-0 top-0 h-full w-80 border-l overflow-y-auto z-40 transition-transform"
      style={{
        backgroundColor: 'var(--bg-primary)',
        borderColor: 'var(--border-light)',
      }}
    >
      {/* Header */}
      <div
        className="sticky top-0 p-4 border-b"
        style={{
          backgroundColor: 'var(--bg-primary)',
          borderColor: 'var(--border-light)',
        }}
      >
        <h2
          className="text-lg font-semibold flex items-center gap-2"
          style={{ color: 'var(--text-primary)' }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          Live Stats
        </h2>
        
        {/* Status indicator */}
        <div className="flex items-center gap-2 mt-2">
          <div
            className={`w-2 h-2 rounded-full ${stats.processingStatus !== 'idle' ? 'animate-pulse' : ''}`}
            style={{ backgroundColor: getStatusColor(stats.processingStatus) }}
          />
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {getStatusLabel(stats.processingStatus)}
          </span>
        </div>
      </div>

      {/* Stats content */}
      <div className="p-4 space-y-6">
        {/* Current search stats (when active) */}
        {stats.currentSearch && stats.processingStatus !== 'idle' && (
          <div
            className="p-4 rounded-lg animate-fadeIn"
            style={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-light)',
            }}
          >
            <h3
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--text-primary)' }}
            >
              Current Search
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <StatItem
                label="OpenAlex"
                value={stats.currentSearch.openalexCount}
                suffix="papers"
                pulse={pulse}
              />
              <StatItem
                label="Semantic Scholar"
                value={stats.currentSearch.semanticScholarCount}
                suffix="papers"
                pulse={pulse}
              />
              <StatItem
                label="New Papers"
                value={stats.currentSearch.newPapers}
                highlight
                pulse={pulse}
              />
              <StatItem
                label="Chunks Created"
                value={stats.currentSearch.chunksCreated}
                highlight
                pulse={pulse}
              />
              {typeof stats.currentSearch.duplicatesRemoved === 'number' && (
                <StatItem
                  label="Duplicates"
                  value={stats.currentSearch.duplicatesRemoved}
                  pulse={pulse}
                />
              )}
              {typeof stats.currentSearch.embeddingsTotal === 'number' && (
                <StatItem
                  label="Embeddings"
                  value={stats.currentSearch.embeddingsCompleted || 0}
                  suffix={`/${stats.currentSearch.embeddingsTotal}`}
                  highlight
                  pulse={pulse}
                />
              )}
            </div>
            {typeof stats.currentSearch.elapsedMs === 'number' && (
              <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
                Elapsed: {(stats.currentSearch.elapsedMs / 1000).toFixed(1)}s
              </p>
            )}
            {typeof stats.currentSearch.embeddingsTotal === 'number' && stats.currentSearch.embeddingsTotal > 0 && (
              <div className="mt-3">
                <div
                  className="h-2 rounded-full overflow-hidden"
                  style={{ backgroundColor: 'var(--border-light)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.round(
                          ((stats.currentSearch.embeddingsCompleted || 0) / stats.currentSearch.embeddingsTotal) * 100
                        )
                      )}%`,
                      backgroundColor: 'var(--accent-primary)',
                    }}
                  />
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  Embeddings {stats.currentSearch.embeddingsCompleted || 0}/{stats.currentSearch.embeddingsTotal}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Database stats */}
        <div>
          <h3
            className="text-sm font-medium mb-3 flex items-center gap-2"
            style={{ color: 'var(--text-secondary)' }}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
              />
            </svg>
            Database
          </h3>
          <div className="space-y-3">
            <StatRow
              label="Total Papers"
              value={stats.totalPapers.toLocaleString()}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              }
              pulse={pulse}
            />
            <StatRow
              label="Total Chunks"
              value={stats.totalChunks.toLocaleString()}
              icon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                  />
                </svg>
              }
              pulse={pulse}
            />
            <StatRow
              label="Embedded"
              value={`${stats.embeddedChunks.toLocaleString()} / ${stats.totalChunks.toLocaleString()}`}
              progress={(stats.totalChunks > 0 ? (stats.embeddedChunks / stats.totalChunks) * 100 : 0)}
              pulse={pulse}
            />
            <StatRow
              label="Avg Tokens/Chunk"
              value={stats.avgTokensPerChunk.toFixed(0)}
              pulse={pulse}
            />
          </div>
        </div>

        {/* Quick actions */}
        <div>
          <h3
            className="text-sm font-medium mb-3"
            style={{ color: 'var(--text-secondary)' }}
          >
            Quick Info
          </h3>
          <div
            className="p-3 rounded-lg text-xs space-y-2"
            style={{
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-muted)',
            }}
          >
            <p>• Papers are fetched from OpenAlex & Semantic Scholar</p>
            <p>• Text is chunked for semantic search</p>
            <p>• Embeddings enable similarity matching</p>
          </div>
        </div>

        {/* Last update */}
        {stats.lastUpdate && (
          <p
            className="text-xs text-center"
            style={{ color: 'var(--text-muted)' }}
          >
            Last updated: {stats.lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  );
}

function StatItem({
  label,
  value,
  suffix,
  highlight,
  pulse,
}: {
  label: string;
  value: number;
  suffix?: string;
  highlight?: boolean;
  pulse?: boolean;
}) {
  return (
    <div className={pulse ? 'animate-pulse' : ''}>
      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
        {label}
      </p>
      <p
        className="text-lg font-semibold"
        style={{ color: highlight ? 'var(--accent-primary)' : 'var(--text-primary)' }}
      >
        {value.toLocaleString()}
        {suffix && (
          <span className="text-xs font-normal ml-1" style={{ color: 'var(--text-muted)' }}>
            {suffix}
          </span>
        )}
      </p>
    </div>
  );
}

function StatRow({
  label,
  value,
  icon,
  progress,
  pulse,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  progress?: number;
  pulse?: boolean;
}) {
  return (
    <div className={pulse ? 'animate-pulse' : ''}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon && (
            <span style={{ color: 'var(--text-tertiary)' }}>{icon}</span>
          )}
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {label}
          </span>
        </div>
        <span
          className="text-sm font-medium"
          style={{ color: 'var(--text-primary)' }}
        >
          {value}
        </span>
      </div>
      {progress !== undefined && (
        <div
          className="mt-1 h-1.5 rounded-full overflow-hidden"
          style={{ backgroundColor: 'var(--border-light)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${progress}%`,
              backgroundColor: progress > 0 ? 'var(--accent-success)' : 'var(--border-medium)',
            }}
          />
        </div>
      )}
    </div>
  );
}
