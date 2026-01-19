'use client';

import { useState, useEffect, useRef, useCallback, memo } from 'react';
import type { Message } from '@/app/page';

interface VirtualizedMessageListProps {
  messages: Message[];
  renderMessage: (message: Message, index: number) => React.ReactNode;
  itemHeight: number;
  containerHeight: number;
  className?: string;
}

interface MessageItem {
  message: Message;
  index: number;
  top: number;
}

export const VirtualizedMessageList = memo(function VirtualizedMessageList({
  messages,
  renderMessage,
  itemHeight,
  containerHeight,
  className = '',
}: VirtualizedMessageListProps) {
  const [scrollTop, setScrollTop] = useState(0);
  const [visibleItems, setVisibleItems] = useState<MessageItem[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const totalHeight = messages.length * itemHeight;

  const updateVisibleItems = useCallback(() => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight) + 2, // Add buffer
      messages.length
    );

    const items: MessageItem[] = [];
    for (let i = Math.max(0, startIndex - 1); i < endIndex; i++) { // Add buffer above
      if (messages[i]) {
        items.push({
          message: messages[i],
          index: i,
          top: i * itemHeight,
        });
      }
    }

    setVisibleItems(items);
  }, [scrollTop, messages, itemHeight, containerHeight]);

  useEffect(() => {
    updateVisibleItems();
  }, [updateVisibleItems]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      const container = containerRef.current;
      const isNearBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 100;

      if (isNearBottom || messages.length === visibleItems.length) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [messages.length, visibleItems.length]);

  return (
    <div
      ref={containerRef}
      className={`overflow-y-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map((item) => (
          <div
            key={item.message.id}
            style={{
              position: 'absolute',
              top: item.top,
              width: '100%',
              height: itemHeight,
            }}
          >
            {renderMessage(item.message, item.index)}
          </div>
        ))}
      </div>
    </div>
  );
});