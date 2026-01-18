'use client';

import { SynthesisMode } from '@/lib/api';

interface ModeSelectorProps {
  selectedMode: SynthesisMode;
  onModeChange: (mode: SynthesisMode) => void;
  disabled?: boolean;
}

const modes = [
  {
    id: 'synthesize' as SynthesisMode,
    icon: '📊',
    name: 'Synthesize',
    description: 'Summarize what research says about a topic',
    example: '"What do we know about X?"',
  },
  {
    id: 'compare' as SynthesisMode,
    icon: '⚖️',
    name: 'Compare',
    description: 'Compare different approaches or methodologies',
    example: '"CRISPR vs traditional gene therapy"',
  },
  {
    id: 'plan' as SynthesisMode,
    icon: '🗺️',
    name: 'Plan',
    description: 'Find research gaps and plan next steps',
    example: '"What questions are still open?"',
  },
  {
    id: 'explore' as SynthesisMode,
    icon: '🔬',
    name: 'Explore',
    description: 'Deep dive into specific aspects of your topic',
    example: '"Tell me more about [aspect]"',
  },
];

export function ModeSelector({ selectedMode, onModeChange, disabled }: ModeSelectorProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {modes.map((mode) => (
        <button
          key={mode.id}
          onClick={() => onModeChange(mode.id)}
          disabled={disabled}
          className={`
            p-4 rounded-xl border-2 text-left transition-all duration-200
            ${selectedMode === mode.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-zinc-200 bg-white hover:border-zinc-300'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <div className="text-2xl mb-2">{mode.icon}</div>
          <div className="text-sm font-semibold text-zinc-900 mb-1">{mode.name}</div>
          <div className="text-xs text-zinc-500 leading-tight">{mode.description}</div>
        </button>
      ))}
    </div>
  );
}

export function ModeSelectorCompact({ selectedMode, onModeChange, disabled }: ModeSelectorProps) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {modes.map((mode) => (
        <button
          key={mode.id}
          onClick={() => onModeChange(mode.id)}
          disabled={disabled}
          className={`
            px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200
            ${selectedMode === mode.id
              ? 'bg-blue-500 text-white'
              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <span className="mr-1">{mode.icon}</span>
          {mode.name}
        </button>
      ))}
    </div>
  );
}
