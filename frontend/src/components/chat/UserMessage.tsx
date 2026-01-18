'use client';

interface UserMessageProps {
  content: string;
  timestamp: Date;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="flex justify-end animate-fadeIn">
      <div
        className="max-w-md px-4 py-3 rounded-2xl rounded-br-md"
        style={{
          backgroundColor: 'var(--accent-blue)',
          color: 'white',
        }}
      >
        <p className="text-[15px] leading-relaxed">{content}</p>
        <p 
          className="text-xs mt-2 text-right"
          style={{ opacity: 0.7 }}
        >
          {timestamp.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}
