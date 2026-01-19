'use client';

import { useState, useRef, useEffect } from 'react';
import type { Source } from '@/lib/api';

interface CitationTooltipProps {
  source: Source;
  children: React.ReactNode;
  onSourceClick: (source: Source) => void;
}

export function CitationTooltip({ source, children, onSourceClick }: CitationTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        setPosition({
          top: rect.top - 10,
          left: rect.left + rect.width / 2,
        });
        setIsVisible(true);
      }
    }, 300);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <>
      <span
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onClick={() => onSourceClick(source)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onSourceClick(source);
          }
        }}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
        tabIndex={0}
        role="button"
        aria-label={`View source: ${source.title} by ${source.authors.slice(0, 2).join(', ')}`}
        aria-describedby="citation-tooltip"
      >
        {children}
      </span>

      {isVisible && (
        <div
          id="citation-tooltip"
          ref={tooltipRef}
          className="fixed z-[100] transform -translate-x-1/2 -translate-y-full pointer-events-none animate-fadeIn"
          style={{
            top: position.top,
            left: position.left,
          }}
          role="tooltip"
        >
          <div
            className="max-w-xs p-3 rounded-lg"
            style={{
              backgroundColor: 'var(--bg-pill)',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <p
              className="text-sm font-medium mb-1 line-clamp-2"
              style={{ color: 'var(--text-inverse)' }}
            >
              {source.title}
            </p>
            <p
              className="text-xs mb-1"
              style={{ color: 'var(--text-muted)' }}
            >
              {source.authors.slice(0, 2).join(', ')}
              {source.authors.length > 2 && ' et al.'}
              {source.year && ` • ${source.year}`}
            </p>
            <p
              className="text-xs"
              style={{ color: 'var(--text-tertiary)' }}
            >
              Click to view source
            </p>
          </div>
          {/* Arrow */}
          <div
            className="w-3 h-3 mx-auto transform rotate-45 -mt-1.5"
            style={{ backgroundColor: 'var(--bg-pill)' }}
          />
        </div>
      )}
    </>
  );
}
