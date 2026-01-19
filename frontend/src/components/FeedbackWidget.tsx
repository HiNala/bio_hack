'use client';

import { useState } from 'react';
import { logger } from '@/lib/logger';

interface FeedbackWidgetProps {
  className?: string;
}

export function FeedbackWidget({ className = '' }: FeedbackWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!feedback.trim() && rating === null) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Log feedback for analysis
      logger.info('User feedback submitted', {
        rating,
        feedback: feedback.trim(),
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      });

      // In a real app, this would send to your feedback API
      // await api.submitFeedback({ rating, feedback: feedback.trim() });

      setSubmitted(true);
      setTimeout(() => {
        setIsOpen(false);
        setSubmitted(false);
        setFeedback('');
        setRating(null);
      }, 2000);

    } catch (error) {
      logger.trackError(error as Error, 'Feedback submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg transition-all duration-200 flex items-center justify-center z-50 ${className}`}
        aria-label="Give feedback"
      >
        💬
      </button>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 ${className}`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Share Your Feedback</h3>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close feedback"
          >
            ✕
          </button>
        </div>

        {submitted ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">🙏</div>
            <p className="text-gray-700 font-medium">Thank you for your feedback!</p>
            <p className="text-gray-500 text-sm mt-1">We appreciate your help in improving ScienceRAG.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                How would you rate your experience?
              </label>
              <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className={`text-2xl transition-colors ${
                      rating && star <= rating ? 'text-yellow-400' : 'text-gray-300'
                    }`}
                    aria-label={`Rate ${star} star${star !== 1 ? 's' : ''}`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <label htmlFor="feedback" className="block text-sm font-medium text-gray-700 mb-2">
                Tell us more (optional)
              </label>
              <textarea
                id="feedback"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="What's working well? What could be improved?"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || (!feedback.trim() && rating === null)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Sending...' : 'Send Feedback'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}