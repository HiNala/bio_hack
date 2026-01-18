'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Header,
  FloatingInput,
  EmptyState,
  UserMessage,
  AssistantResponse,
  LoadingState,
  LiveStatsSidebar,
  SettingsPanel,
  ToastContainer,
  useToasts,
  type Source,
  type ProgressStep,
  type LiveStats,
} from '@/components/chat';
import { api, type Paper, type IngestJobStatusResponse } from '@/lib/api';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  papersAnalyzed?: number;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [currentJobStatus, setCurrentJobStatus] = useState<IngestJobStatusResponse | null>(null);
  const [liveStats, setLiveStats] = useState<LiveStats>({
    totalPapers: 0,
    totalChunks: 0,
    embeddedChunks: 0,
    avgTokensPerChunk: 0,
    recentQueries: 0,
    processingStatus: 'idle',
    lastUpdate: null,
  });
  
  const conversationRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<{ focus: () => void } | null>(null);
  const statsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const jobPollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { toasts, dismissToast, error: showError, success: showSuccess } = useToasts();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to focus input
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      // Escape to close settings
      if (e.key === 'Escape' && isSettingsOpen) {
        setIsSettingsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen]);

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

  // Process a query
  const handleSubmit = async (query: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Start loading
    setIsLoading(true);
    setCurrentMessage('Starting ingestion job...');
    setProgressSteps([
      { id: 'parsing', label: 'Parsing query', status: 'active' },
      { id: 'fetching', label: 'Fetching papers', status: 'pending' },
      { id: 'storing', label: 'Storing papers', status: 'pending' },
      { id: 'chunking', label: 'Chunking abstracts', status: 'pending' },
      { id: 'embedding', label: 'Creating embeddings', status: 'pending' },
    ]);

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
      // Get settings from localStorage
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
      setCurrentMessage('Ingestion job started...');
      setLiveStats(prev => ({ ...prev, processingStatus: 'searching' }));
    } catch (err) {
      console.error('Error processing query:', err);
      
      // Show error toast
      showError('Search failed', err instanceof Error ? err.message : 'Unknown error occurred');

      // Add error message
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
        const status = await api.getIngestJobStatus(currentJobId);
        setCurrentJobStatus(status);
        setCurrentMessage(`Stage: ${status.status}`);

        // Map to progress steps
        if (status.progress?.stages) {
          setProgressSteps([
            { id: 'parsing', label: 'Parsing query', status: mapStage(status.progress.stages.parsing?.status) },
            { id: 'fetching', label: 'Fetching papers', status: mapStage(status.progress.stages.fetching?.status) },
            { id: 'storing', label: 'Storing papers', status: mapStage(status.progress.stages.storing?.status) },
            { id: 'chunking', label: 'Chunking abstracts', status: mapStage(status.progress.stages.chunking?.status) },
            { id: 'embedding', label: 'Creating embeddings', status: mapStage(status.progress.stages.embedding?.status) },
          ]);
        }

        // Update live stats
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
        }

        if (status.status === 'completed' || status.status === 'failed') {
          if (jobPollIntervalRef.current) {
            clearInterval(jobPollIntervalRef.current);
          }

          setIsLoading(false);

          if (status.status === 'completed') {
            // Fetch papers for sources
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

            const responseContent = generateSummaryResponse(
              status.original_query,
              [],
              sources
            );

            setMessages(prev => [
              ...prev,
              {
                id: (Date.now() + 1).toString(),
                type: 'assistant',
                content: responseContent,
                timestamp: new Date(),
                sources,
                papersAnalyzed: progress?.papers.papers_stored || 0,
              },
            ]);

            showSuccess('Search complete', `Found ${progress?.papers.papers_stored || 0} papers and created ${progress?.chunks.total_created || 0} chunks.`);
          } else {
            showError('Ingestion failed', status.error?.message || 'Unknown error');
          }

          setCurrentJobId(null);
          setLiveStats(prev => ({ ...prev, processingStatus: 'idle', currentSearch: undefined }));
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
  }, [currentJobId, showError, showSuccess]);

  // Handle example query click
  const handleExampleClick = (query: string) => {
    handleSubmit(query);
  };

  // Handle source click - scroll to source and open link
  const handleSourceClick = (source: Source) => {
    // First, scroll to the source in the conversation
    const sourceElement = document.getElementById(`source-${source.citationId}`);
    if (sourceElement) {
      sourceElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      sourceElement.classList.add('ring-2', 'ring-blue-500');
      setTimeout(() => {
        sourceElement.classList.remove('ring-2', 'ring-blue-500');
      }, 2000);
    }
    
    // Open the paper link
    if (source.url) {
      window.open(source.url, '_blank');
    } else if (source.doi) {
      window.open(`https://doi.org/${source.doi}`, '_blank');
    }
  };

  // Toggle settings
  const handleToggleSettings = () => {
    setIsSettingsOpen(!isSettingsOpen);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <Header
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
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
        className="pt-16 pb-32 transition-all duration-300"
        style={{
          marginRight: isSidebarOpen ? '320px' : '0',
        }}
      >
        <div
          ref={conversationRef}
          className="max-w-3xl mx-auto px-4 py-8 overflow-y-auto"
          style={{ maxHeight: 'calc(100vh - 180px)' }}
        >
          {!hasMessages && !isLoading ? (
            <EmptyState onExampleClick={handleExampleClick} />
          ) : (
            <div className="space-y-4">
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
                  />
                )
              ))}

              {isLoading && (
                <LoadingState
                  steps={progressSteps}
                  currentMessage={currentMessage}
                />
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
        placeholder={hasMessages ? "Ask a follow-up question..." : "Ask a research question..."}
      />

      {/* Live stats sidebar */}
      <LiveStatsSidebar
        stats={liveStats}
        isOpen={isSidebarOpen}
      />
    </div>
  );
}

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

  // Helper function to generate a response
function generateSummaryResponse(query: string, papers: Paper[], sources: Source[]): string {
  if (papers.length === 0) {
    return `I searched for papers related to "${query}" but couldn't find any results. Try refining your search terms or broadening your query.`;
  }

  const papersWithAbstracts = papers.filter(p => p.abstract);
  const years = papers.map(p => p.publication_year).filter(Boolean) as number[];
  const minYear = years.length > 0 ? Math.min(...years) : null;
  const maxYear = years.length > 0 ? Math.max(...years) : null;

  let response = `I found ${papers.length} relevant papers on "${query}"`;
  
  if (minYear && maxYear) {
    response += `, spanning from ${minYear} to ${maxYear}`;
  }
  response += '.\n\n';

  // Add context from top papers
  if (sources.length > 0) {
    response += `The most relevant findings include work by ${sources[0].authors[0] || 'various researchers'}`;
    if (sources[0].year) response += ` (${sources[0].year})`;
    response += ` [1]`;
    
    if (sources.length > 1) {
      response += `, and related research`;
      if (sources[1].authors[0]) response += ` from ${sources[1].authors[0]}`;
      if (sources[1].year) response += ` (${sources[1].year})`;
      response += ` [2]`;
    }
    response += '.\n\n';
  }

  // Add abstract snippets if available
  if (papersWithAbstracts.length > 0) {
    const topPaper = papersWithAbstracts[0];
    const snippet = topPaper.abstract?.substring(0, 300);
    if (snippet) {
      response += `Key findings suggest: "${snippet}..." [1]\n\n`;
    }
  }

  response += `These papers have been stored in your knowledge base and are now searchable. You can explore the sources below or ask follow-up questions to dive deeper into specific aspects.`;

  return response;
}
