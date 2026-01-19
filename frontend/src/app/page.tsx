'use client';

import { useState, useEffect, useRef, useCallback, useMemo, lazy, Suspense, memo } from 'react';
import { usePerformanceMonitor } from '@/hooks/usePerformanceMonitor';
import { useAgentActivityStream } from '@/hooks/useAgentActivityStream';
import {
  Header,
  FloatingInput,
  UserMessage,
  LoadingState,
  LiveStatsSidebar,
  SettingsPanel,
  ToastContainer,
  useToasts,
  type Source,
  type ProgressStep,
  type LiveStats,
  type AgentActivity,
} from '@/components/chat';
import { api, type IngestJobStatusResponse, type RAGResponse, ragCitationsToSources } from '@/lib/api';
import { MessageSkeleton } from '@/components/LoadingSkeleton';

// Lazy load components that are not immediately needed
const EmptyState = lazy(() => import('@/components/chat/EmptyState').then(module => ({ default: module.EmptyState })));
const AssistantResponse = lazy(() => import('@/components/chat/AssistantResponse').then(module => ({ default: module.AssistantResponse })));
const LoadingStateComponent = lazy(() => import('@/components/chat/LoadingState').then(module => ({ default: module.LoadingState })));
const LiveStatsSidebarComponent = lazy(() => import('@/components/chat/LiveStatsSidebar').then(module => ({ default: module.LiveStatsSidebar })));

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  papersAnalyzed?: number;
  keyFindings?: string[];
  consensus?: string[];
  openQuestions?: string[];
  toolActivity?: {
    openalexPapers: number;
    semanticScholarPapers: number;
    uniquePapers: number;
    chunksCreated: number;
    embeddingsGenerated: number;
  };
}

const Home = memo(function Home() {
  const { trackInteraction } = usePerformanceMonitor('HomePage');

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Start with sidebar open to show agent activity
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [liveStats, setLiveStats] = useState<LiveStats>({
    totalPapers: 0,
    totalChunks: 0,
    embeddedChunks: 0,
    avgTokensPerChunk: 0,
    recentQueries: 0,
    processingStatus: 'idle',
    lastUpdate: null,
  });
  
  // Use SSE stream for real-time agent activity updates
  const {
    activity: streamActivity,
    recentActivities: streamRecentActivities,
    isConnected: isActivityStreamConnected,
  } = useAgentActivityStream({
    enabled: true,
    onActivity: (activity) => {
      // Update local activity state from stream
      console.log('[AgentActivity] Received:', activity.type, activity.message);
    },
  });
  
  // Local activity state for manual updates (fallback when stream is not available)
  const [localAgentActivity, setLocalAgentActivity] = useState<AgentActivity>({
    type: 'idle',
    message: 'Ready to explore the scientific literature...',
  });
  const [localRecentActivities, setLocalRecentActivities] = useState<AgentActivity[]>([]);
  
  // Use stream activity if connected, otherwise use local state
  const agentActivity = isActivityStreamConnected ? streamActivity : localAgentActivity;
  const recentActivities = isActivityStreamConnected ? streamRecentActivities : localRecentActivities;
  
  const conversationRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<{ focus: () => void } | null>(null);
  const statsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const jobPollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { toasts, dismissToast, error: showError, success: showSuccess, info: showInfo } = useToasts();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K: Focus input
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Escape: Close settings or sidebar
      if (e.key === 'Escape') {
        if (isSettingsOpen) {
          setIsSettingsOpen(false);
        } else if (isSidebarOpen) {
          setIsSidebarOpen(false);
        }
      }

      // Cmd/Ctrl + B: Toggle sidebar
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        setIsSidebarOpen(prev => !prev);
      }

      // Cmd/Ctrl + ,: Open settings
      if ((e.metaKey || e.ctrlKey) && e.key === ',') {
        e.preventDefault();
        setIsSettingsOpen(prev => !prev);
      }

      // Tab navigation improvements
      if (e.key === 'Tab') {
        const activeElement = document.activeElement as Element | null;
        const focusableElements = document.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (activeElement) {
          if (e.shiftKey) {
            // Shift+Tab: move to previous
            const currentIndex = Array.from(focusableElements).indexOf(activeElement);
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : focusableElements.length - 1;
            (focusableElements[prevIndex] as HTMLElement)?.focus();
          } else {
            // Tab: move to next
            const currentIndex = Array.from(focusableElements).indexOf(activeElement);
            const nextIndex = currentIndex < focusableElements.length - 1 ? currentIndex + 1 : 0;
            (focusableElements[nextIndex] as HTMLElement)?.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, isSidebarOpen]);

  // Helper to update agent activity with history tracking (local fallback)
  const updateAgentActivity = useCallback((activity: AgentActivity) => {
    setLocalAgentActivity(activity);
    if (activity.type !== 'idle') {
      setLocalRecentActivities(prev => [...prev.slice(-19), { ...activity, timestamp: new Date() }]);
    }
  }, []);

  // Memoize expensive computations
  const hasMessages = useMemo(() => messages.length > 0, [messages.length]);
  const isProcessing = useMemo(() =>
    liveStats.processingStatus !== 'idle' && liveStats.processingStatus !== 'ready',
    [liveStats.processingStatus]
  );

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const [chunkStats, docResponse] = await Promise.all([
        api.getChunkingStats(),
        api.getDocuments(undefined, 1, 1),
      ]);

      setLiveStats(prev => ({
        ...prev,
        totalPapers: docResponse.total,
        totalChunks: chunkStats.total_chunks,
        embeddedChunks: chunkStats.embedded_chunks,
        avgTokensPerChunk: chunkStats.avg_tokens_per_chunk,
        lastUpdate: new Date(),
      }));
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchStats();
    statsIntervalRef.current = setInterval(fetchStats, 5000);
    return () => {
      if (statsIntervalRef.current) clearInterval(statsIntervalRef.current);
    };
  }, [fetchStats]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Generate RAG synthesis after ingestion
  const generateRAGSynthesis = useCallback(async (question: string, sources: Source[]): Promise<Message> => {
    try {
      setCurrentMessage('Synthesizing answer from papers...');
      setProgressSteps(prev => [...prev, { id: 'synthesis', label: 'Synthesizing answer', status: 'active' }]);

      updateAgentActivity({
        type: 'synthesizing',
        message: '🧠 Synthesizing comprehensive answer from retrieved papers...',
        detail: `Analyzing ${sources.length} relevant sources for insights and consensus`,
        apiCall: 'POST /api/rag/ask',
        articlesFound: sources.length,
      });

      const ragResponse: RAGResponse = await api.askRAG(question, 10);

      setProgressSteps(prev => prev.map(s => s.id === 'synthesis' ? { ...s, status: 'completed' } : s));
      
      updateAgentActivity({
        type: 'complete',
        message: '✅ Analysis complete! Here\'s what I discovered in the literature.',
        detail: `Synthesized insights from ${ragResponse.papers_analyzed || sources.length} papers with evidence-based conclusions`,
      });

      let content = ragResponse.summary || '';
      
      if (ragResponse.key_findings && ragResponse.key_findings.length > 0) {
        content += '\n\n**Key Findings:**\n';
        ragResponse.key_findings.forEach((finding) => {
          content += `• ${finding}\n`;
        });
      }

      if (ragResponse.consensus && ragResponse.consensus.length > 0) {
        content += '\n**Scientific Consensus:**\n';
        ragResponse.consensus.forEach(item => {
          content += `• ${item}\n`;
        });
      }

      if (ragResponse.open_questions && ragResponse.open_questions.length > 0) {
        content += '\n**Open Questions:**\n';
        ragResponse.open_questions.forEach(item => {
          content += `• ${item}\n`;
        });
      }

      const ragSources: Source[] = ragResponse.citations.map((citation, idx) => ({
        citationId: idx + 1,
        paperId: citation.paper_id,
        title: citation.title,
        authors: citation.authors,
        year: citation.year,
        venue: null,
        doi: null,
        url: null,
      }));

      return {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content,
        timestamp: new Date(),
        sources: ragSources.length > 0 ? ragSources : sources,
        papersAnalyzed: ragResponse.papers_analyzed || sources.length,
        keyFindings: ragResponse.key_findings,
        consensus: ragResponse.consensus,
        openQuestions: ragResponse.open_questions,
      };
    } catch (err) {
      console.error('RAG synthesis failed:', err);
      setProgressSteps(prev => prev.map(s => s.id === 'synthesis' ? { ...s, status: 'error' } : s));
      
      updateAgentActivity({
        type: 'error',
        message: 'Synthesis temporarily unavailable',
        detail: 'Papers are stored and searchable. Try exploring them directly.',
      });
      
      return {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I found ${sources.length} relevant papers on "${question}". The papers have been stored in your knowledge base and are now searchable.\n\nNote: AI synthesis is currently unavailable. You can explore the sources below.`,
        timestamp: new Date(),
        sources,
        papersAnalyzed: sources.length,
      };
    }
  }, []);

  // Process a query
  const handleSubmit = async (query: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setCurrentQuery(query);

    setIsLoading(true);
    setCurrentMessage('Starting search...');
    setProgressSteps([
      { id: 'parsing', label: 'Parsing research query', status: 'active' },
      { id: 'fetching', label: 'Querying literature APIs', status: 'pending' },
      { id: 'storing', label: 'Deduplicating & storing', status: 'pending' },
      { id: 'chunking', label: 'Segmenting text', status: 'pending' },
      { id: 'embedding', label: 'Generating vectors', status: 'pending' },
    ]);

    // Start agent activity tracking
    updateAgentActivity({
      type: 'thinking',
      message: `🔍 Analyzing your query: "${query.slice(0, 60)}${query.length > 60 ? '...' : ''}"`,
      detail: 'Breaking down research concepts and keywords...',
    });

    setLiveStats(prev => ({
      ...prev,
      processingStatus: 'searching',
      currentSearch: {
        openalexCount: 0,
        semanticScholarCount: 0,
        newPapers: 0,
        chunksCreated: 0,
      },
    }));

    try {
      const savedSettings = localStorage.getItem('sciencerag-settings');
      const settings = savedSettings ? JSON.parse(savedSettings) : { papersPerQuery: 30, openalexEnabled: true, semanticScholarEnabled: true };
      const sources: string[] = [];
      if (settings.openalexEnabled !== false) sources.push('openalex');
      if (settings.semanticScholarEnabled !== false) sources.push('semantic_scholar');

      const startResponse = await api.startIngestJob({
        query,
        sources: sources.length > 0 ? sources : undefined,
        max_results_per_source: settings.papersPerQuery || 30,
      });

      setCurrentJobId(startResponse.job_id);
      setCurrentMessage('Searching literature databases...');
      setLiveStats(prev => ({ ...prev, processingStatus: 'searching' }));
      
      updateAgentActivity({
        type: 'searching',
        message: '🔎 Searching academic literature databases...',
        detail: 'Querying OpenAlex and Semantic Scholar for relevant papers',
        apiCall: 'GET /api/openalex, GET /api/semantic_scholar',
      });
    } catch (err) {
      console.error('Error processing query:', err);
      
      showError('Search failed', err instanceof Error ? err.message : 'Unknown error occurred');

      updateAgentActivity({
        type: 'error',
        message: 'Search failed to start',
        detail: err instanceof Error ? err.message : 'Unknown error occurred',
      });

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I encountered an error while searching: ${err instanceof Error ? err.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
        sources: [],
        papersAnalyzed: 0,
      };
      setMessages(prev => [...prev, errorMessage]);

      setProgressSteps(steps => steps.map(s => 
        s.status === 'active' ? { ...s, status: 'error' } : s
      ));
      setIsLoading(false);
      setLiveStats(prev => ({ ...prev, processingStatus: 'idle', currentSearch: undefined }));
    }
  };

  // Poll ingest job status
  useEffect(() => {
    if (!currentJobId) return;

    const pollJob = async () => {
      try {
        const status: IngestJobStatusResponse = await api.getIngestJobStatus(currentJobId);
        setCurrentMessage(`${status.status.charAt(0).toUpperCase() + status.status.slice(1)}...`);

        if (status.progress?.stages) {
          setProgressSteps([
            { id: 'parsing', label: 'Parsing research query', status: mapStage(status.progress.stages.parsing?.status) },
            { id: 'fetching', label: 'Querying literature APIs', status: mapStage(status.progress.stages.fetching?.status) },
            { id: 'storing', label: 'Deduplicating & storing', status: mapStage(status.progress.stages.storing?.status) },
            { id: 'chunking', label: 'Segmenting text', status: mapStage(status.progress.stages.chunking?.status) },
            { id: 'embedding', label: 'Generating vectors', status: mapStage(status.progress.stages.embedding?.status) },
          ]);
        }

        const progress = status.progress;
        if (progress) {
          setLiveStats(prev => ({
            ...prev,
            processingStatus: status.status === 'embedding' ? 'embedding' : status.status === 'completed' ? 'ready' : 'processing',
            currentSearch: {
              openalexCount: progress.papers.openalex_found,
              semanticScholarCount: progress.papers.semantic_scholar_found,
              newPapers: progress.papers.papers_stored,
              chunksCreated: progress.chunks.total_created,
              duplicatesRemoved: progress.papers.duplicates_removed,
              embeddingsCompleted: progress.embeddings.completed,
              embeddingsTotal: progress.embeddings.total,
              elapsedMs: status.elapsed_time_ms,
            },
          }));

          // Update agent activity based on current stage
          const stages = status.progress?.stages;
          if (stages?.fetching?.status === 'in_progress') {
            updateAgentActivity({
              type: 'fetching',
              message: `Found ${progress.papers.openalex_found} papers from OpenAlex, ${progress.papers.semantic_scholar_found} from Semantic Scholar...`,
              detail: 'Retrieving paper metadata and abstracts',
              apiCall: 'GET /api/literature/search',
              articlesFound: progress.papers.openalex_found + progress.papers.semantic_scholar_found,
            });
          } else if (stages?.storing?.status === 'in_progress') {
            updateAgentActivity({
              type: 'processing',
              message: `🧹 Deduplicating and storing ${progress.papers.papers_stored} unique papers...`,
              detail: `Removed ${progress.papers.duplicates_removed || 0} duplicate entries`,
              apiCall: 'POST /api/papers/batch',
            });
          } else if (stages?.chunking?.status === 'in_progress') {
            updateAgentActivity({
              type: 'processing',
              message: `✂️ Chunking paper abstracts into semantic segments...`,
              detail: `Created ${progress.chunks.total_created} text chunks so far`,
              apiCall: 'POST /api/chunk/all',
            });
          } else if (stages?.embedding?.status === 'in_progress') {
            const embeddingProgress = progress.embeddings.total > 0
              ? Math.round((progress.embeddings.completed / progress.embeddings.total) * 100)
              : 0;
            updateAgentActivity({
              type: 'embedding',
              message: `🧠 Generating vector embeddings... ${embeddingProgress}%`,
              detail: `${progress.embeddings.completed} of ${progress.embeddings.total} chunks embedded`,
              apiCall: 'POST /api/embed/batch (text-embedding-3-small)',
            });
          }
        }

        if (status.status === 'completed' || status.status === 'failed') {
          if (jobPollIntervalRef.current) {
            clearInterval(jobPollIntervalRef.current);
          }

          if (status.status === 'completed') {
            const papersResponse = await api.getIngestJobPapers(currentJobId, 10, 0);
            const sources: Source[] = papersResponse.papers.map((paper, index) => ({
              citationId: index + 1,
              paperId: paper.id,
              title: paper.title,
              authors: paper.authors,
              year: paper.year || null,
              venue: paper.venue || null,
              doi: paper.doi || null,
              url: paper.url || null,
            }));

            // Capture tool activity for display
            const toolActivity = {
              openalexPapers: progress?.papers.openalex_found || 0,
              semanticScholarPapers: progress?.papers.semantic_scholar_found || 0,
              uniquePapers: progress?.papers.papers_stored || 0,
              chunksCreated: progress?.chunks.total_created || 0,
              embeddingsGenerated: progress?.embeddings.completed || 0,
            };

            showInfo('Papers ingested', `Found ${progress?.papers.papers_stored || 0} papers. Synthesizing answer...`);
            
            const assistantMessage = await generateRAGSynthesis(currentQuery, sources);
            assistantMessage.toolActivity = toolActivity;
            setMessages(prev => [...prev, assistantMessage]);

            showSuccess('Analysis complete', `Analyzed ${assistantMessage.papersAnalyzed || 0} papers`);
          } else {
            showError('Ingestion failed', status.error?.message || 'Unknown error');
            
            updateAgentActivity({
              type: 'error',
              message: 'Pipeline encountered an error',
              detail: status.error?.message || 'Unknown error occurred',
            });
            
            const errorMessage: Message = {
              id: (Date.now() + 1).toString(),
              type: 'assistant',
              content: `I encountered an error: ${status.error?.message || 'Unknown error'}. Please try again with a different query.`,
              timestamp: new Date(),
              sources: [],
              papersAnalyzed: 0,
            };
            setMessages(prev => [...prev, errorMessage]);
          }

          setIsLoading(false);
          setCurrentJobId(null);
          setCurrentQuery('');
          setLiveStats(prev => ({ ...prev, processingStatus: 'idle', currentSearch: undefined }));
          fetchStats();
          
          // Reset agent activity to idle after a brief delay
          setTimeout(() => {
            setLocalAgentActivity({
              type: 'idle',
              message: 'Ready to explore the scientific literature...',
            });
          }, 3000);
        }
      } catch (err) {
        console.error('Polling failed:', err);
      }
    };

    pollJob();
    jobPollIntervalRef.current = setInterval(pollJob, 1000);

    return () => {
      if (jobPollIntervalRef.current) clearInterval(jobPollIntervalRef.current);
    };
  }, [currentJobId, currentQuery, generateRAGSynthesis, showError, showSuccess, showInfo, fetchStats, updateAgentActivity]);

  const handleExampleClick = (query: string) => {
    handleSubmit(query);
  };

  const handleSourceClick = (source: Source) => {
    const sourceElement = document.getElementById(`source-${source.citationId}`);
    if (sourceElement) {
      sourceElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      sourceElement.classList.add('ring-2', 'ring-blue-500');
      setTimeout(() => {
        sourceElement.classList.remove('ring-2', 'ring-blue-500');
      }, 2000);
    }
    
    if (source.url) {
      window.open(source.url, '_blank');
    } else if (source.doi) {
      window.open(`https://doi.org/${source.doi}`, '_blank');
    }
  };

  const handleToggleSettings = () => {
    setIsSettingsOpen(!isSettingsOpen);
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-page)' }}>
      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <Header
        onToggleSidebar={() => {}}
        isSidebarOpen={isSidebarOpen}
        onToggleSettings={handleToggleSettings}
      />

      {/* Settings Panel */}
      <SettingsPanel
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Main content area */}
      <main
        id="main-content"
        className="pt-16 pb-40 transition-all duration-300 relative md:mr-0"
        style={{
          marginRight: isSidebarOpen ? '320px' : '0',
        }}
        role="main"
        aria-label="Research conversation and results"
      >
        <div
          ref={conversationRef}
          className="max-w-2xl mx-auto px-4 sm:px-6 py-8 overflow-y-auto"
          style={{ maxHeight: 'calc(100vh - 200px)' }}
        >
          {!hasMessages && !isLoading ? (
            <EmptyState onExampleClick={handleExampleClick} />
          ) : (
            <div className="space-y-6">
              {messages.map((message) => (
                message.type === 'user' ? (
                  <UserMessage
                    key={message.id}
                    content={message.content}
                    timestamp={message.timestamp}
                  />
                ) : (
                  <AssistantResponse
                    key={message.id}
                    content={message.content}
                    sources={message.sources || []}
                    papersAnalyzed={message.papersAnalyzed || 0}
                    onSourceClick={handleSourceClick}
                    toolActivity={message.toolActivity}
                  />
                )
              ))}

              {isLoading && (
                <Suspense fallback={<MessageSkeleton />}>
                  <LoadingStateComponent
                    steps={progressSteps}
                    currentMessage={currentMessage}
                  />
                </Suspense>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Floating input */}
      <FloatingInput
        ref={inputRef}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        placeholder={hasMessages ? "Ask a follow-up question or refine your hypothesis..." : "State a research question or hypothesis..."}
      />

      {/* Live stats sidebar */}
      <Suspense fallback={null}>
        <LiveStatsSidebarComponent
          stats={liveStats}
          isOpen={isSidebarOpen}
          agentActivity={agentActivity}
          recentActivities={recentActivities}
        />
      </Suspense>
    </div>
  );
});

Home.displayName = 'Home';

export default Home;

function mapStage(status?: string): 'pending' | 'active' | 'completed' | 'error' {
  switch (status) {
    case 'completed':
      return 'completed';
    case 'in_progress':
      return 'active';
    case 'failed':
      return 'error';
    default:
      return 'pending';
  }
}
