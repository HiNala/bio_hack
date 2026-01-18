'use client';

import { useState } from 'react';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

const EXAMPLE_QUERIES = [
  "What are the leading interpretations of quantum mechanics since 2010?",
  "How does CRISPR compare to earlier gene editing techniques?",
  "What is the current consensus on dark matter candidates?",
  "What are the main approaches to solving protein folding?",
];

export function QueryInput({ onSubmit, isLoading, placeholder }: QueryInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main input */}
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder || "Enter a research question..."}
            disabled={isLoading}
            rows={3}
            className="w-full px-4 py-3 text-lg rounded-lg border-2 resize-none transition-colors"
            style={{
              fontFamily: 'var(--font-serif)',
              backgroundColor: 'var(--color-bg)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--color-accent)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--color-border)';
            }}
          />
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="w-full py-3 px-6 rounded-lg font-medium transition-all"
          style={{
            backgroundColor: query.trim() && !isLoading ? 'var(--color-accent)' : 'var(--color-border)',
            color: query.trim() && !isLoading ? 'white' : 'var(--color-text-muted)',
            cursor: query.trim() && !isLoading ? 'pointer' : 'not-allowed',
          }}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Analyzing Literature...
            </span>
          ) : (
            'Analyze Literature'
          )}
        </button>
      </form>

      {/* Example queries */}
      <div className="mt-6">
        <p
          className="text-sm mb-3"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}
        >
          Example queries:
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example, i) => (
            <button
              key={i}
              onClick={() => handleExampleClick(example)}
              className="text-sm px-3 py-1.5 rounded-full border transition-colors hover:border-current"
              style={{
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-secondary)',
                fontFamily: 'var(--font-serif)',
              }}
            >
              {example.length > 50 ? example.substring(0, 50) + '...' : example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
