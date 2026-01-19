'use client';

import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';

interface FloatingInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const FloatingInput = forwardRef<{ focus: () => void }, FloatingInputProps>(
  function FloatingInput({ onSubmit, isLoading = false, placeholder = "State a research question or hypothesis..." }, ref) {
    const [value, setValue] = useState('');
    const [isFocused, setIsFocused] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
      focus: () => textareaRef.current?.focus(),
    }));

    // Auto-resize textarea
    useEffect(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = 'auto';
        const newHeight = Math.min(textarea.scrollHeight, 120); // Max 4 lines approx
        textarea.style.height = `${newHeight}px`;
      }
    }, [value]);

    const handleSubmit = () => {
      const trimmed = value.trim();
      if (trimmed && !isLoading) {
        onSubmit(trimmed);
        setValue('');
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    };

    return (
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 w-full px-6" style={{ maxWidth: '720px' }}>
        {/* Main pill container */}
        <div
          className="relative transition-all duration-300"
          style={{
            backgroundColor: 'rgba(28, 28, 30, 0.95)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderRadius: 'var(--radius-pill)',
            border: isFocused 
              ? '1px solid rgba(255, 255, 255, 0.15)' 
              : '1px solid rgba(255, 255, 255, 0.08)',
            boxShadow: isFocused
              ? '0 8px 32px rgba(0, 0, 0, 0.16), 0 0 0 1px rgba(59, 130, 246, 0.1)'
              : 'var(--shadow-pill)',
          }}
        >
          <div className="flex items-center gap-3 px-5 py-3">
            {/* Search icon */}
            <svg
              className="w-5 h-5 flex-shrink-0 transition-colors duration-200"
              style={{ color: isFocused ? 'rgba(255, 255, 255, 0.6)' : 'rgba(255, 255, 255, 0.4)' }}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
              />
            </svg>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder}
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-transparent text-white placeholder-zinc-500 resize-none outline-none text-[15px] leading-relaxed scrollbar-hide"
              style={{
                minHeight: '24px',
                maxHeight: '120px',
              }}
              aria-label="Research query input"
              aria-describedby="input-help"
              aria-expanded={isFocused}
              role="textbox"
              aria-multiline={true}
            />

            {/* Orb indicator */}
            <div className="flex items-center gap-2">
              <OrbIndicator isActive={isLoading} isFocused={isFocused} />
              
              {/* Submit button */}
              <button
                onClick={handleSubmit}
                disabled={!value.trim() || isLoading}
                className="w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 flex-shrink-0"
                style={{
                  backgroundColor: value.trim() && !isLoading 
                    ? 'var(--accent-blue)' 
                    : 'rgba(255, 255, 255, 0.1)',
                  cursor: value.trim() && !isLoading ? 'pointer' : 'default',
                }}
              >
                {isLoading ? (
                  <svg className="w-4 h-4 text-white animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                ) : (
                  <svg
                    className="w-4 h-4"
                    style={{ color: value.trim() ? 'white' : 'rgba(255, 255, 255, 0.3)' }}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Helper text */}
        <p
          id="input-help"
          className="text-center mt-3 text-xs transition-opacity duration-200"
          style={{
            color: 'var(--text-tertiary)',
            opacity: isFocused ? 1 : 0.6,
          }}
        >
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    );
  }
);

// Orb indicator component
function OrbIndicator({ isActive, isFocused }: { isActive: boolean; isFocused: boolean }) {
  return (
    <div
      className={`w-8 h-8 rounded-full flex-shrink-0 transition-all duration-500 ${
        isActive ? 'animate-orb-active' : isFocused ? 'animate-orb-idle' : ''
      }`}
      style={{
        background: isActive
          ? 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)'
          : isFocused
          ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.6) 0%, rgba(139, 92, 246, 0.6) 100%)'
          : 'linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%)',
        opacity: isActive ? 1 : isFocused ? 0.8 : 0.5,
        boxShadow: isActive
          ? '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(139, 92, 246, 0.3)'
          : isFocused
          ? '0 0 12px rgba(59, 130, 246, 0.3)'
          : 'none',
      }}
    />
  );
}
