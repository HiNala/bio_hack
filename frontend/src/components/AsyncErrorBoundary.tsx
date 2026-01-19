'use client';

import { Component, ReactNode } from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class AsyncErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Handle async errors and promise rejections
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Async error caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center min-h-[200px] p-6">
          <div className="text-center">
            <div className="text-2xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold mb-2 text-red-600">
              Something went wrong
            </h3>
            <p className="text-gray-600 mb-4">
              An error occurred while loading this content.
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return <ErrorBoundary>{this.props.children}</ErrorBoundary>;
  }
}

// Hook for handling async errors in functional components
export function useAsyncError() {
  return (error: Error) => {
    throw error;
  };
}