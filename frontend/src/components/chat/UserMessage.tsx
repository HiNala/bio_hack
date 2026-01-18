'use client';

interface UserMessageProps {
  content: string;
  timestamp?: Date;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="flex justify-end mb-4 animate-fadeIn">
      <div
        className="max-w-[80%] px-4 py-3 rounded-2xl rounded-br-sm"
        style={{
          backgroundColor: 'var(--bg-tertiary)',
        }}
      >
        <p
          className="text-base leading-relaxed whitespace-pre-wrap"
          style={{ color: 'var(--text-primary)' }}
        >
          {content}
        </p>
        {timestamp && (
          <p
            className="text-xs mt-1 text-right"
            style={{ color: 'var(--text-muted)' }}
          >
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  );
}
