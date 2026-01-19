'use client';

import { useState } from 'react';
import type { ResearchSession, ResearchContext, TimelineEvent } from '@/lib/api';

interface ResearchSessionPanelProps {
  session: ResearchSession | null;
  context?: ResearchContext;
  timeline?: { events: TimelineEvent[]; total_queries: number; total_insights: number };
  onSessionClick?: (sessionId: string) => void;
  onViewTimeline?: () => void;
  isActive?: boolean;
}

export function ResearchSessionPanel({
  session,
  context,
  timeline,
  onSessionClick,
  onViewTimeline,
  isActive = false,
}: ResearchSessionPanelProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (!session) {
    return (
      <div
        className="rounded-xl border p-5"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
        }}
      >
        <div className="text-center py-4">
          <span className="text-2xl mb-2 block">🔬</span>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            No active research session
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
            Start a query to begin tracking your research
          </p>
        </div>
      </div>
    );
  }

  const statusConfig = getStatusConfig(session.status);

  return (
    <div
      className={`rounded-xl border overflow-hidden transition-all duration-200 ${
        isActive ? 'ring-2 ring-blue-500/30' : ''
      }`}
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: isActive ? 'var(--accent-blue)' : 'var(--border-subtle)',
      }}
    >
      {/* Header */}
      <div
        className="p-4 border-b"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${statusConfig.dot}`} />
            <span
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: 'var(--text-tertiary)' }}
            >
              Research Session
            </span>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusConfig.badge}`}>
            {session.status}
          </span>
        </div>

        <h3
          className="text-sm font-medium mt-2"
          style={{ color: 'var(--text-primary)' }}
        >
          {session.name || session.primary_topic || 'Unnamed Session'}
        </h3>

        {session.description && (
          <p
            className="text-xs mt-1 line-clamp-2"
            style={{ color: 'var(--text-secondary)' }}
          >
            {session.description}
          </p>
        )}
      </div>

      {/* Stats */}
      <div
        className="grid grid-cols-3 gap-px"
        style={{ backgroundColor: 'var(--border-subtle)' }}
      >
        <StatCell
          value={timeline?.total_queries || 0}
          label="Queries"
          icon="🔍"
        />
        <StatCell
          value={timeline?.total_insights || 0}
          label="Insights"
          icon="💡"
        />
        <StatCell
          value={session.key_papers?.length || 0}
          label="Papers"
          icon="📄"
        />
      </div>

      {/* Context Info */}
      {context && context.context_text && (
        <div
          className="p-4 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <div className="flex items-center justify-between mb-2">
            <span
              className="text-xs font-semibold"
              style={{ color: 'var(--text-tertiary)' }}
            >
              Session Context Active
            </span>
            <span className="text-xs" style={{ color: 'var(--accent-blue)' }}>
              {context.token_count} tokens
            </span>
          </div>

          <div className="flex gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <span>{context.sources.insights} insights</span>
            <span>•</span>
            <span>{context.sources.summaries} summaries</span>
            <span>•</span>
            <span>{context.sources.recent_queries} recent queries</span>
          </div>

          <p
            className="text-xs mt-2 line-clamp-3"
            style={{ color: 'var(--text-tertiary)' }}
          >
            {context.context_text.slice(0, 200)}...
          </p>
        </div>
      )}

      {/* Key Topics */}
      {session.related_topics && session.related_topics.length > 0 && (
        <div
          className="px-4 py-3 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <span
            className="text-xs font-semibold"
            style={{ color: 'var(--text-tertiary)' }}
          >
            Related Topics:
          </span>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {session.related_topics.slice(0, 5).map((topic, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded-full text-xs"
                style={{
                  backgroundColor: 'var(--bg-page)',
                  color: 'var(--text-secondary)',
                }}
              >
                {topic}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity Preview */}
      {timeline && timeline.events.length > 0 && (
        <div
          className="p-4 border-t"
          style={{ borderColor: 'var(--border-subtle)', backgroundColor: 'var(--bg-page)' }}
        >
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center justify-between w-full text-left"
          >
            <span
              className="text-xs font-semibold"
              style={{ color: 'var(--text-tertiary)' }}
            >
              Recent Activity
            </span>
            <svg
              className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              style={{ color: 'var(--text-tertiary)' }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showDetails && (
            <div className="mt-3 space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
              {timeline.events.slice(-5).reverse().map((event, idx) => (
                <TimelineEventItem key={idx} event={event} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="p-4 border-t flex gap-2" style={{ borderColor: 'var(--border-subtle)' }}>
        {onViewTimeline && (
          <button
            onClick={onViewTimeline}
            className="flex-1 py-2 text-xs font-medium rounded-lg transition-colors"
            style={{
              backgroundColor: 'var(--accent-blue)',
              color: 'white',
            }}
          >
            View Full Timeline
          </button>
        )}
        {onSessionClick && (
          <button
            onClick={() => onSessionClick(session.id)}
            className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
            style={{
              backgroundColor: 'var(--bg-page)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-light)',
            }}
          >
            Details
          </button>
        )}
      </div>

      {/* Timestamps */}
      <div
        className="px-4 py-2 border-t text-center"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          Started: {formatDate(session.created_at)} • Last activity: {formatRelativeTime(session.last_activity_at)}
        </span>
      </div>
    </div>
  );
}

// Helper functions

function getStatusConfig(status: string) {
  switch (status) {
    case 'active':
      return {
        dot: 'bg-green-500 animate-pulse',
        badge: 'bg-green-100 text-green-700',
      };
    case 'paused':
      return {
        dot: 'bg-amber-500',
        badge: 'bg-amber-100 text-amber-700',
      };
    case 'completed':
      return {
        dot: 'bg-blue-500',
        badge: 'bg-blue-100 text-blue-700',
      };
    default:
      return {
        dot: 'bg-zinc-400',
        badge: 'bg-zinc-100 text-zinc-700',
      };
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return formatDate(dateStr);
}

// Sub-components

function StatCell({ value, label, icon }: { value: number; label: string; icon: string }) {
  return (
    <div
      className="p-3 text-center"
      style={{ backgroundColor: 'var(--bg-card)' }}
    >
      <div className="flex items-center justify-center gap-1">
        <span className="text-sm">{icon}</span>
        <span className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
          {value}
        </span>
      </div>
      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </span>
    </div>
  );
}

function TimelineEventItem({ event }: { event: TimelineEvent }) {
  const getEventIcon = () => {
    switch (event.type) {
      case 'query': return '🔍';
      case 'insight': return '💡';
      default: return '•';
    }
  };

  return (
    <div className="flex items-start gap-2 py-1.5">
      <span className="text-sm flex-shrink-0">{getEventIcon()}</span>
      <div className="flex-1 min-w-0">
        <p
          className="text-xs truncate"
          style={{ color: 'var(--text-secondary)' }}
        >
          {event.content.slice(0, 80)}...
        </p>
        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          {formatRelativeTime(event.timestamp)}
        </span>
      </div>
    </div>
  );
}

export default ResearchSessionPanel;
