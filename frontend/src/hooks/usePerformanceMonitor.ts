import { useEffect, useRef } from 'react';

// Performance monitoring hook for tracking component performance
export function usePerformanceMonitor(componentName: string) {
  const renderStart = useRef<number>();
  const renderCount = useRef(0);

  useEffect(() => {
    renderStart.current = performance.now();
    renderCount.current += 1;
  });

  useEffect(() => {
    if (renderStart.current) {
      const renderTime = performance.now() - renderStart.current;

      // Log slow renders in development
      if (process.env.NODE_ENV === 'development' && renderTime > 16) {
        console.warn(`${componentName} render took ${renderTime.toFixed(2)}ms (frame drop risk)`);
      }

      // Track render metrics
      if (typeof window !== 'undefined' && 'gtag' in window) {
        // Send to Google Analytics if available
        (window as any).gtag('event', 'component_render', {
          component_name: componentName,
          render_time: Math.round(renderTime),
          render_count: renderCount.current,
        });
      }
    }
  });

  // Track interactions
  const trackInteraction = (action: string, data?: any) => {
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'component_interaction', {
        component_name: componentName,
        action,
        ...data,
      });
    }
  };

  return { trackInteraction };
}