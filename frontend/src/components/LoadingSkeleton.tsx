'use client';

interface LoadingSkeletonProps {
  className?: string;
  lines?: number;
  showAvatar?: boolean;
}

export function LoadingSkeleton({ className = "", lines = 3, showAvatar = false }: LoadingSkeletonProps) {
  return (
    <div className={`animate-fadeIn space-y-4 ${className}`}>
      <div className="flex items-start gap-3">
        {showAvatar && (
          <div className="w-8 h-8 rounded-full bg-gray-200 animate-pulse flex-shrink-0" />
        )}
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded animate-pulse" />
          <div className="space-y-2">
            {Array.from({ length: lines }, (_, i) => (
              <div
                key={i}
                className="h-3 bg-gray-200 rounded animate-pulse"
                style={{
                  width: `${Math.random() * 40 + 60}%`, // Random width between 60-100%
                  animationDelay: `${i * 100}ms`,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function MessageSkeleton() {
  return (
    <div className="space-y-6">
      {/* User message skeleton */}
      <div className="flex justify-end">
        <LoadingSkeleton className="max-w-md" lines={2} />
      </div>

      {/* Assistant message skeleton */}
      <div className="flex justify-start">
        <LoadingSkeleton className="max-w-2xl" lines={4} showAvatar />
      </div>
    </div>
  );
}