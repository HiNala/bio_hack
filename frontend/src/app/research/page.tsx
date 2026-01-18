'use client';

import { useState, useCallback } from 'react';
import {
  QueryInput,
  ProgressIndicator,
  AnswerDisplay,
  SourcePanel,
  PaperModal,
} from '@/components';
import {
  RAGResponse,
  Citation,
  Paper,
  processQuery,
  getHealth,
} from '@/lib/api';

type AppState = 'idle' | 'loading' | 'results' | 'error';

interface ResearchState {
  status: AppState;
  step: number;
  query: string;
  response: RAGResponse | null;
  error: string | null;
  selectedPaper: Paper | null;
}

export default function ResearchPage() {
  const [state, setState] = useState<ResearchState>({
    status: 'idle',
    step: 0,
    query: '',
    response: null,
    error: null,
    selectedPaper: null,
  });

  const handleSubmit = useCallback(async (query: string) => {
    setState((s) => ({
      ...s,
      status: 'loading',
      step: 0,
      query,
      error: null,
    }));

    try {
      // Check backend health first
      setState((s) => ({ ...s, step: 0 }));
      await getHealth();

      // Process query (this is a simplified flow)
      setState((s) => ({ ...s, step: 1 }));
      
      // For demo, we'll call the RAG endpoint directly
      // In production, you'd call process → embed → rag/ask
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/rag/ask?question=${encodeURIComponent(query)}&top_k=10`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      setState((s) => ({ ...s, step: 4 }));
      const data: RAGResponse = await response.json();

      setState((s) => ({
        ...s,
        status: 'results',
        response: data,
      }));
    } catch (err) {
      setState((s) => ({
        ...s,
        status: 'error',
        error: err instanceof Error ? err.message : 'An error occurred',
      }));
    }
  }, []);

  const handleCitationClick = useCallback((citation: Citation) => {
    // In a full implementation, we'd fetch paper details
    // For now, create a mock paper from citation data
    setState((s) => ({
      ...s,
      selectedPaper: {
        id: citation.paper_id,
        title: citation.title,
        authors: citation.authors,
        year: citation.year,
        abstract: null,
        venue: null,
        source: 'unknown',
        citation_count: 0,
        doi: null,
        url: null,
      },
    }));
  }, []);

  const handleCloseModal = useCallback(() => {
    setState((s) => ({ ...s, selectedPaper: null }));
  }, []);

  const handleNewQuery = useCallback(() => {
    setState({
      status: 'idle',
      step: 0,
      query: '',
      response: null,
      error: null,
      selectedPaper: null,
    });
  }, []);

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--color-bg)' }}>
      {/* Header */}
      <header className="border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2">
            <h1 className="text-xl font-semibold" style={{ fontFamily: 'var(--font-serif)' }}>
              ScienceRAG
            </h1>
          </a>
          {state.status === 'results' && (
            <button
              onClick={handleNewQuery}
              className="text-sm px-4 py-2 rounded border transition-colors"
              style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-secondary)' }}
            >
              New Query
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 py-8 px-6">
        {/* Idle State - Query Input */}
        {state.status === 'idle' && (
          <div className="max-w-3xl mx-auto pt-16">
            <div className="text-center mb-12">
              <h2
                className="text-4xl font-semibold mb-4"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                Query the Scientific Literature
              </h2>
              <p style={{ color: 'var(--color-text-secondary)' }}>
                Ask a research question and get a synthesized answer with citations
              </p>
            </div>
            <QueryInput onSubmit={handleSubmit} />
          </div>
        )}

        {/* Loading State */}
        {state.status === 'loading' && (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <h2
                className="text-2xl font-semibold mb-2"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                Analyzing Your Query
              </h2>
              <p
                className="text-lg"
                style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-serif)' }}
              >
                &ldquo;{state.query}&rdquo;
              </p>
            </div>
            <ProgressIndicator currentStep={state.step} />
          </div>
        )}

        {/* Error State */}
        {state.status === 'error' && (
          <div className="max-w-3xl mx-auto text-center pt-16">
            <div
              className="p-6 rounded-lg mb-6"
              style={{ backgroundColor: 'var(--color-bg-secondary)' }}
            >
              <p className="text-lg mb-2" style={{ color: 'var(--color-warning)' }}>
                Something went wrong
              </p>
              <p style={{ color: 'var(--color-text-muted)' }}>{state.error}</p>
            </div>
            <button
              onClick={handleNewQuery}
              className="px-6 py-3 rounded font-medium"
              style={{ backgroundColor: 'var(--color-accent)', color: 'white' }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Results State */}
        {state.status === 'results' && state.response && (
          <div className="max-w-6xl mx-auto">
            {/* Query reminder */}
            <div className="text-center mb-8">
              <p
                className="text-sm"
                style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}
              >
                Results for
              </p>
              <p
                className="text-xl"
                style={{ fontFamily: 'var(--font-serif)' }}
              >
                &ldquo;{state.query}&rdquo;
              </p>
            </div>

            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main answer */}
              <div className="lg:col-span-2">
                <AnswerDisplay
                  response={state.response}
                  onCitationClick={handleCitationClick}
                />
              </div>

              {/* Sources sidebar */}
              <div className="lg:col-span-1">
                <SourcePanel
                  citations={state.response.citations}
                  onCitationSelect={handleCitationClick}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer
        className="border-t py-4"
        style={{ borderColor: 'var(--color-border)' }}
      >
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p
            className="text-sm"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}
          >
            Powered by OpenAlex, Semantic Scholar, and Claude
          </p>
        </div>
      </footer>

      {/* Paper Modal */}
      <PaperModal paper={state.selectedPaper} onClose={handleCloseModal} />
    </div>
  );
}
