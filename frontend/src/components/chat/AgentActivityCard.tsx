'use client';

import { useState, useEffect, useRef } from 'react';
import { logger } from '@/lib/logger';

export interface AgentActivity {
  type: 'idle' | 'thinking' | 'searching' | 'fetching' | 'processing' | 'embedding' | 'synthesizing' | 'complete' | 'error';
  message: string;
  detail?: string;
  apiCall?: string;
  articlesFound?: number;
  timestamp?: Date;
}

interface AgentActivityCardProps {
  activity: AgentActivity;
  recentActivities?: AgentActivity[];
}

// Fun idle messages that cycle through
const IDLE_MESSAGES = [
  { emoji: '🔬', message: "Ready to explore the scientific literature..." },
  { emoji: '📚', message: "Awaiting your research question..." },
  { emoji: '🧠', message: "Neural pathways standing by..." },
  { emoji: '🔍', message: "250M+ papers at your fingertips..." },
  { emoji: '✨', message: "What shall we discover today?" },
  { emoji: '🌟', message: "Science never sleeps, and neither do I..." },
  { emoji: '🎯', message: "Ask me anything about science..." },
  { emoji: '💡', message: "Every great discovery starts with a question..." },
  { emoji: '🚀', message: "Ready for launch. Where to?" },
  { emoji: '🧬', message: "From DNA to dark matter, I'm here to help..." },
  { emoji: '⚛️', message: "Quantum states initialized..." },
  { emoji: '🧪', message: "Beakers bubbling, hypotheses forming..." },
  { emoji: '🔭', message: "Telescope calibrated for discovery..." },
  { emoji: '🧮', message: "Algorithms humming, vectors aligning..." },
  { emoji: '🌌', message: "Exploring the universe of knowledge..." },
  { emoji: '💫', message: "Curiosity circuits activated..." },
  { emoji: '🎭', message: "The scientific method awaits..." },
  { emoji: '🌈', message: "Colors of discovery await..." },
];

// Typing animation hook
function useTypingAnimation(text: string, speed: number = 30, enabled: boolean = true) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setDisplayedText(text);
      return;
    }

    setDisplayedText('');
    setIsTyping(true);
    let index = 0;

    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        setIsTyping(false);
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, enabled]);

  return { displayedText, isTyping };
}

// Animated dots for loading states
function AnimatedDots() {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 400);
    return () => clearInterval(interval);
  }, []);

  return <span className="inline-block w-6 text-left">{dots}</span>;
}

// Thinking pulse animation
function ThinkingPulse() {
  return (
    <div className="flex items-center gap-1">
      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
      <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
    </div>
  );
}

// Pulsing orb for activity indicator
function ActivityOrb({ type }: { type: AgentActivity['type'] }) {
  const colors = {
    idle: 'bg-zinc-300',
    thinking: 'bg-purple-400',
    searching: 'bg-blue-400',
    fetching: 'bg-cyan-400',
    processing: 'bg-yellow-400',
    embedding: 'bg-orange-400',
    synthesizing: 'bg-pink-400',
    complete: 'bg-green-400',
    error: 'bg-red-400',
  };

  const isActive = type !== 'idle' && type !== 'complete' && type !== 'error';

  return (
    <div className="relative flex items-center justify-center">
      <div
        className={`w-3 h-3 rounded-full ${colors[type]} transition-colors duration-300`}
      />
      {isActive && (
        <>
          <div
            className={`absolute w-3 h-3 rounded-full ${colors[type]} animate-ping opacity-75`}
          />
          <div
            className={`absolute w-5 h-5 rounded-full ${colors[type]} opacity-20 animate-pulse`}
          />
        </>
      )}
    </div>
  );
}

// Activity log entry
function ActivityLogEntry({ activity, isLatest }: { activity: AgentActivity; isLatest: boolean }) {
  const getIcon = () => {
    switch (activity.type) {
      case 'thinking': return '🧠';
      case 'searching': return '🔍';
      case 'fetching': return '📡';
      case 'processing': return '⚙️';
      case 'embedding': return '🧮';
      case 'synthesizing': return '✨';
      case 'complete': return '✅';
      case 'error': return '❌';
      default: return '💭';
    }
  };

  return (
    <div className={`flex items-start gap-2 py-1.5 transition-opacity duration-300 ${isLatest ? 'opacity-100' : 'opacity-50'}`}>
      <span className="text-xs flex-shrink-0 mt-0.5">{getIcon()}</span>
      <span className="text-xs text-zinc-600 leading-relaxed">{activity.message}</span>
    </div>
  );
}

// Dynamic thinking messages
const THINKING_MESSAGES = [
  "Analyzing your query... 🔍",
  "Connecting concepts... 🧠",
  "Exploring research space... 🚀",
  "Evaluating evidence quality... 📊",
  "Cross-referencing sources... 📚",
  "Formulating hypothesis... 💡",
  "Building knowledge graph... 🌐",
  "Synthesizing insights... ✨",
  "Refining understanding... 🎯",
];

export function AgentActivityCard({ activity, recentActivities = [] }: AgentActivityCardProps) {
  const [idleMessageIndex, setIdleMessageIndex] = useState(0);
  const [thinkingMessageIndex, setThinkingMessageIndex] = useState(0);
  const [showHistory, setShowHistory] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Cycle through idle messages
  useEffect(() => {
    if (activity.type === 'idle') {
      logger.trackAgentActivity('idle_cycle_started', { messages: IDLE_MESSAGES.length });
      const interval = setInterval(() => {
        setIdleMessageIndex(prev => (prev + 1) % IDLE_MESSAGES.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [activity.type]);

  // Cycle through thinking messages
  useEffect(() => {
    if (activity.type === 'thinking') {
      logger.trackAgentActivity('thinking_cycle_started', { messages: THINKING_MESSAGES.length });
      const interval = setInterval(() => {
        setThinkingMessageIndex(prev => (prev + 1) % THINKING_MESSAGES.length);
      }, 2000);
      return () => clearInterval(interval);
    } else {
      setThinkingMessageIndex(0); // Reset when not thinking
    }
  }, [activity.type]);

  // Log activity changes
  useEffect(() => {
    logger.trackAgentActivity('activity_changed', {
      type: activity.type,
      message: activity.message,
      hasDetail: !!activity.detail,
      hasApiCall: !!activity.apiCall,
    });
  }, [activity.type, activity.message]);

  // Auto-scroll to bottom when new activity
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [recentActivities]);

  const currentIdleMessage = IDLE_MESSAGES[idleMessageIndex];
  const currentThinkingMessage = THINKING_MESSAGES[thinkingMessageIndex];

  const displayMessage = activity.type === 'idle' ? currentIdleMessage.message :
                         activity.type === 'thinking' ? currentThinkingMessage :
                         activity.message;
  const displayEmoji = activity.type === 'idle' ? currentIdleMessage.emoji : null;

  // Use typing animation for non-idle states
  const { displayedText, isTyping } = useTypingAnimation(
    displayMessage,
    activity.type === 'idle' ? 40 : 25,
    activity.type !== 'idle'
  );

  const getStatusLabel = () => {
    switch (activity.type) {
      case 'idle': return 'Standing By';
      case 'thinking': return 'Deep in Thought';
      case 'searching': return 'Querying Databases';
      case 'fetching': return 'Retrieving Papers';
      case 'processing': return 'Analyzing Content';
      case 'embedding': return 'Creating Vectors';
      case 'synthesizing': return 'Crafting Response';
      case 'complete': return 'Task Complete';
      case 'error': return 'Error Occurred';
      default: return 'Working';
    }
  };

  const isActive = activity.type !== 'idle' && activity.type !== 'complete' && activity.type !== 'error';

  return (
    <div
      className={`rounded-xl border overflow-hidden transition-all duration-300 ${
        isActive ? 'shadow-lg' : ''
      }`}
      style={{
        backgroundColor: 'var(--bg-card)',
        borderColor: isActive ? 'var(--accent-blue)' : 'var(--border-light)',
        boxShadow: isActive ? '0 0 20px rgba(59, 130, 246, 0.1)' : 'none',
        background: isActive ? 'linear-gradient(135deg, var(--bg-card) 0%, rgba(59, 130, 246, 0.02) 100%)' : 'var(--bg-card)',
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 flex items-center justify-between border-b"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <div className="flex items-center gap-2">
          <ActivityOrb type={activity.type} />
          <span
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-tertiary)' }}
          >
            Agent Activity
          </span>
        </div>
        <span
          className="text-xs px-2 py-0.5 rounded-full"
          style={{
            backgroundColor: isActive ? 'rgba(59, 130, 246, 0.1)' : 'var(--border-subtle)',
            color: isActive ? 'var(--accent-blue)' : 'var(--text-tertiary)',
          }}
        >
          {getStatusLabel()}
          {isActive && <AnimatedDots />}
        </span>
      </div>

      {/* Main Content */}
      <div className="px-4 py-4">
        {/* Current Activity Display */}
        <div className="min-h-[60px]">
          {activity.type === 'idle' ? (
            <div className="flex items-start gap-3">
              <span className="text-2xl breathe">
                {displayEmoji}
              </span>
              <p
                className="text-sm leading-relaxed transition-opacity duration-500"
                style={{ color: 'var(--text-secondary)' }}
              >
                {displayMessage}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-start gap-3">
                <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                  activity.type === 'thinking' ? 'bg-purple-100' :
                  activity.type === 'searching' ? 'bg-blue-100 animate-bounce' :
                  activity.type === 'fetching' ? 'bg-cyan-100 animate-ping' :
                  activity.type === 'processing' ? 'bg-yellow-100' :
                  activity.type === 'embedding' ? 'bg-orange-100' :
                  activity.type === 'synthesizing' ? 'bg-pink-100' :
                  'bg-gray-100'
                }`}>
                  {activity.type === 'thinking' && <ThinkingPulse />}
                  {activity.type === 'searching' && '🔍'}
                  {activity.type === 'fetching' && '📡'}
                  {activity.type === 'processing' && '⚙️'}
                  {activity.type === 'embedding' && '🧮'}
                  {activity.type === 'synthesizing' && '✨'}
                </div>
                <p
                  className="text-sm leading-relaxed flex-1"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {displayedText}
                  {isTyping && (
                    <span className="inline-block w-1.5 h-4 ml-0.5 bg-blue-500 animate-pulse" />
                  )}
                </p>
              </div>
              
              {/* Detail line */}
              {activity.detail && (
                <p
                  className="text-xs leading-relaxed"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  {activity.detail}
                </p>
              )}

              {/* API Call indicator */}
              {activity.apiCall && (
                <div
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs font-mono"
                  style={{ backgroundColor: 'var(--bg-page)' }}
                >
                  <span className="text-green-500">→</span>
                  <span style={{ color: 'var(--text-tertiary)' }}>{activity.apiCall}</span>
                </div>
              )}

              {/* Articles found indicator */}
              {activity.articlesFound !== undefined && activity.articlesFound > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm">📄</span>
                  <span
                    className="text-sm font-medium"
                    style={{ color: 'var(--accent-blue)' }}
                  >
                    {activity.articlesFound} papers found
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Activity History Toggle */}
        {recentActivities.length > 0 && (
          <div className="mt-3 pt-3 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center gap-1 text-xs transition-colors"
              style={{ color: 'var(--text-tertiary)' }}
            >
              <svg
                className={`w-3 h-3 transition-transform ${showHistory ? 'rotate-90' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              Recent activity ({recentActivities.length})
            </button>

            {showHistory && (
              <div
                ref={scrollRef}
                className="mt-2 max-h-32 overflow-y-auto custom-scrollbar space-y-0.5"
              >
                {recentActivities.slice(-10).map((act, i) => (
                  <ActivityLogEntry
                    key={i}
                    activity={act}
                    isLatest={i === recentActivities.length - 1}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Fun footer animation when active */}
      {isActive && (
        <div
          className="h-1 w-full overflow-hidden"
          style={{ backgroundColor: 'var(--border-subtle)' }}
        >
          <div
            className="h-full w-1/3 animate-shimmer"
            style={{
              background: 'linear-gradient(90deg, transparent, var(--accent-blue), transparent)',
              animation: 'shimmer 1.5s infinite',
            }}
          />
        </div>
      )}

      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(400%); }
        }

        @keyframes breathe {
          0%, 100% { transform: scale(1); opacity: 0.7; }
          50% { transform: scale(1.05); opacity: 1; }
        }

        .breathe {
          animation: breathe 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
