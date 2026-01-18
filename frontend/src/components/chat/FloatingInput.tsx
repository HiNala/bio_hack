'use client';

import { useState, useRef, useEffect, KeyboardEvent, forwardRef, useImperativeHandle } from 'react';

interface FloatingInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export interface FloatingInputRef {
  focus: () => void;
}

export const FloatingInput = forwardRef<FloatingInputRef, FloatingInputProps>(
  function FloatingInput({ onSubmit, isLoading = false, placeholder }, ref) {
    const [value, setValue] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Expose focus method to parent
    useImperativeHandle(ref, () => ({
      focus: () => {
        textareaRef.current?.focus();
      },
    }));

    // Auto-resize textarea
    useEffect(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
      }
    }, [value]);

    const handleSubmit = () => {
      if (value.trim() && !isLoading) {
        onSubmit(value.trim());
        setValue('');
      }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    };

    const canSubmit = value.trim().length > 0 && !isLoading;

    return (
      <div className="fixed bottom-0 left-0 right-0 p-4 pb-6 pointer-events-none z-50">
        <div className="max-w-2xl mx-auto pointer-events-auto">
          <div
            className="flex items-end gap-2 rounded-full px-4 py-2"
            style={{
              backgroundColor: 'var(--bg-pill)',
              boxShadow: 'var(--shadow-pill)',
            }}
          >
            {/* Search icon */}
            <div className="flex-shrink-0 pb-2">
              <svg
                className="w-5 h-5"
                style={{ color: 'var(--text-tertiary)' }}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>

            {/* Text input */}
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder || "Ask a research question..."}
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-transparent border-none outline-none resize-none py-2 text-base leading-normal"
              style={{
                color: 'var(--text-inverse)',
                minHeight: '24px',
                maxHeight: '120px',
              }}
            />

            {/* Keyboard hint */}
            <div className="flex-shrink-0 pb-2 hidden sm:block">
              <kbd
                className="px-1.5 py-0.5 text-xs rounded"
                style={{
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  color: 'var(--text-tertiary)',
                }}
              >
                ⌘K
              </kbd>
            </div>

            {/* Submit button */}
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-all mb-0.5"
              style={{
                backgroundColor: canSubmit ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                opacity: canSubmit ? 1 : 0.5,
                cursor: canSubmit ? 'pointer' : 'not-allowed',
              }}
            >
              {isLoading ? (
                <svg className="w-4 h-4 animate-spin" style={{ color: 'white' }} fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" style={{ color: 'white' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
              )}
            </button>
          </div>

          {/* Hint text */}
          <p
            className="text-center mt-2 text-xs"
            style={{ color: 'var(--text-muted)' }}
          >
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    );
  }
);
