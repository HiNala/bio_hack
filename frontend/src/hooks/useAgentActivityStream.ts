'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type { AgentActivity } from '@/components/chat/AgentActivityCard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseAgentActivityStreamOptions {
  enabled?: boolean;
  onActivity?: (activity: AgentActivity) => void;
  onError?: (error: Error) => void;
}

interface UseAgentActivityStreamResult {
  activity: AgentActivity;
  recentActivities: AgentActivity[];
  isConnected: boolean;
  error: Error | null;
  reconnect: () => void;
}

/**
 * Hook to subscribe to real-time agent activity updates via SSE.
 * 
 * Connects to the /activity/stream endpoint and receives live updates
 * about what the agent is doing (thinking, searching, processing, etc.)
 */
export function useAgentActivityStream(
  options: UseAgentActivityStreamOptions = {}
): UseAgentActivityStreamResult {
  const { enabled = true, onActivity, onError } = options;

  const [activity, setActivity] = useState<AgentActivity>({
    type: 'idle',
    message: 'Ready to explore the scientific literature...',
  });
  const [recentActivities, setRecentActivities] = useState<AgentActivity[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000;

  const connect = useCallback(() => {
    if (!enabled) return;

    // Clean up existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const eventSource = new EventSource(`${API_BASE_URL}/activity/stream`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('[AgentActivityStream] Connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Transform API response to match our AgentActivity type
          const newActivity: AgentActivity = {
            type: data.type || 'idle',
            message: data.message || '',
            detail: data.detail,
            apiCall: data.apiCall,
            articlesFound: data.articlesFound,
            timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
          };

          setActivity(newActivity);
          
          // Add to history (skip idle messages)
          if (newActivity.type !== 'idle') {
            setRecentActivities(prev => [...prev.slice(-19), newActivity]);
          }

          // Call callback if provided
          onActivity?.(newActivity);
        } catch (e) {
          console.error('[AgentActivityStream] Failed to parse message:', e);
        }
      };

      // Handle history event (sent on connect)
      eventSource.addEventListener('history', (event: MessageEvent) => {
        try {
          const history = JSON.parse(event.data);
          const activities: AgentActivity[] = history.map((item: any) => ({
            type: item.type || 'idle',
            message: item.message || '',
            detail: item.detail,
            apiCall: item.apiCall,
            articlesFound: item.articlesFound,
            timestamp: item.timestamp ? new Date(item.timestamp) : new Date(),
          }));
          setRecentActivities(activities);
        } catch (e) {
          console.error('[AgentActivityStream] Failed to parse history:', e);
        }
      });

      eventSource.onerror = (e) => {
        console.error('[AgentActivityStream] Connection error:', e);
        setIsConnected(false);
        eventSource.close();

        // Attempt reconnection with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts.current);
          console.log(`[AgentActivityStream] Reconnecting in ${delay}ms...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else {
          const err = new Error('Failed to connect to activity stream after multiple attempts');
          setError(err);
          onError?.(err);
        }
      };
    } catch (e) {
      console.error('[AgentActivityStream] Failed to create EventSource:', e);
      const err = e instanceof Error ? e : new Error('Failed to create EventSource');
      setError(err);
      onError?.(err);
    }
  }, [enabled, onActivity, onError]);

  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    setError(null);
    connect();
  }, [connect]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [enabled, connect]);

  return {
    activity,
    recentActivities,
    isConnected,
    error,
    reconnect,
  };
}
