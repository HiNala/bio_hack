'use client';

import { useState, useEffect } from 'react';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Settings {
  // Data Sources
  openalexEnabled: boolean;
  semanticScholarEnabled: boolean;
  
  // Search Strategy
  papersPerQuery: number;
  minCitations: number;
  yearFrom: number | null;
  yearTo: number | null;
  
  // Reasoning Mode
  reasoningMode: 'exploratory' | 'conservative' | 'contrarian';
  
  // Evidence Handling
  chunkSize: number;
  maxSourcesPerClaim: number;
}

const DEFAULT_SETTINGS: Settings = {
  openalexEnabled: true,
  semanticScholarEnabled: true,
  papersPerQuery: 30,
  minCitations: 0,
  yearFrom: null,
  yearTo: null,
  reasoningMode: 'exploratory',
  chunkSize: 500,
  maxSourcesPerClaim: 5,
};

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  // Load settings from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sciencerag-settings');
    if (saved) {
      try {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(saved) });
      } catch {
        // Use defaults
      }
    }
  }, []);

  // Save settings
  const saveSettings = (newSettings: Settings) => {
    setSettings(newSettings);
    localStorage.setItem('sciencerag-settings', JSON.stringify(newSettings));
  };

  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    saveSettings({ ...settings, [key]: value });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="fixed right-0 top-0 bottom-0 w-96 z-50 overflow-y-auto animate-slideInRight"
        style={{
          backgroundColor: 'var(--bg-card)',
          boxShadow: '-8px 0 32px rgba(0, 0, 0, 0.1)',
        }}
      >
        {/* Header */}
        <div 
          className="sticky top-0 z-10 flex items-center justify-between p-6 border-b"
          style={{ 
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-light)',
          }}
        >
          <div>
            <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
              Research Controls
            </h2>
            <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
              Configure methodology parameters
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors"
            style={{ color: 'var(--text-tertiary)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--border-subtle)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Settings Content */}
        <div className="p-6 space-y-8">
          {/* Data Sources */}
          <section>
            <SectionHeader 
              title="Data Sources" 
              description="Select literature databases to query"
            />
            <div className="space-y-3 mt-4">
              <SourceToggle
                label="OpenAlex"
                description="250M+ works • Broad coverage across all disciplines"
                checked={settings.openalexEnabled}
                onChange={(v) => updateSetting('openalexEnabled', v)}
              />
              <SourceToggle
                label="Semantic Scholar"
                description="200M+ papers • Strong CS/AI/Bio coverage"
                checked={settings.semanticScholarEnabled}
                onChange={(v) => updateSetting('semanticScholarEnabled', v)}
              />
              <SourceToggle
                label="PubMed"
                description="Biomedical literature • Coming soon"
                checked={false}
                onChange={() => {}}
                disabled
              />
            </div>
          </section>

          {/* Search Strategy */}
          <section>
            <SectionHeader 
              title="Search Strategy" 
              description="Control how papers are retrieved"
            />
            <div className="space-y-4 mt-4">
              <RangeInput
                label="Papers per query"
                value={settings.papersPerQuery}
                min={10}
                max={100}
                step={10}
                onChange={(v) => updateSetting('papersPerQuery', v)}
                suffix="papers"
              />
              <RangeInput
                label="Minimum citations"
                value={settings.minCitations}
                min={0}
                max={100}
                step={5}
                onChange={(v) => updateSetting('minCitations', v)}
                suffix="citations"
              />
              <div className="grid grid-cols-2 gap-3">
                <NumberInput
                  label="Year from"
                  value={settings.yearFrom}
                  placeholder="Any"
                  min={1900}
                  max={2026}
                  onChange={(v) => updateSetting('yearFrom', v)}
                />
                <NumberInput
                  label="Year to"
                  value={settings.yearTo}
                  placeholder="Any"
                  min={1900}
                  max={2026}
                  onChange={(v) => updateSetting('yearTo', v)}
                />
              </div>
            </div>
          </section>

          {/* Reasoning Mode */}
          <section>
            <SectionHeader 
              title="Reasoning Mode" 
              description="Adjust synthesis behavior"
            />
            <div className="space-y-2 mt-4">
              <ReasoningOption
                value="exploratory"
                label="Exploratory"
                description="Broad, diverse findings • Surface multiple perspectives"
                selected={settings.reasoningMode === 'exploratory'}
                onChange={() => updateSetting('reasoningMode', 'exploratory')}
              />
              <ReasoningOption
                value="conservative"
                label="Conservative"
                description="High-confidence only • Favor well-cited consensus"
                selected={settings.reasoningMode === 'conservative'}
                onChange={() => updateSetting('reasoningMode', 'conservative')}
              />
              <ReasoningOption
                value="contrarian"
                label="Contrarian"
                description="Surface disagreements • Highlight conflicting evidence"
                selected={settings.reasoningMode === 'contrarian'}
                onChange={() => updateSetting('reasoningMode', 'contrarian')}
              />
            </div>
          </section>

          {/* Evidence Handling */}
          <section>
            <SectionHeader 
              title="Evidence Handling" 
              description="Configure text processing"
            />
            <div className="space-y-4 mt-4">
              <RangeInput
                label="Chunk size"
                value={settings.chunkSize}
                min={200}
                max={1000}
                step={100}
                onChange={(v) => updateSetting('chunkSize', v)}
                suffix="tokens"
              />
              <RangeInput
                label="Max sources per claim"
                value={settings.maxSourcesPerClaim}
                min={1}
                max={10}
                step={1}
                onChange={(v) => updateSetting('maxSourcesPerClaim', v)}
                suffix="sources"
              />
            </div>
          </section>

          {/* Reset */}
          <button
            onClick={() => saveSettings(DEFAULT_SETTINGS)}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors"
            style={{
              backgroundColor: 'var(--bg-page)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-light)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--border-subtle)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-page)';
            }}
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </>
  );
}

function SectionHeader({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <h3 
        className="text-xs font-semibold uppercase tracking-wider"
        style={{ color: 'var(--text-tertiary)' }}
      >
        {title}
      </h3>
      <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
        {description}
      </p>
    </div>
  );
}

function SourceToggle({
  label,
  description,
  checked,
  onChange,
  disabled = false,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label 
      className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      style={{
        backgroundColor: checked ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
        borderColor: checked ? 'var(--accent-blue)' : 'var(--border-light)',
      }}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => !disabled && onChange(e.target.checked)}
        disabled={disabled}
        className="sr-only"
      />
      <div 
        className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors`}
        style={{
          borderColor: checked ? 'var(--accent-blue)' : 'var(--border-medium)',
          backgroundColor: checked ? 'var(--accent-blue)' : 'transparent',
        }}
      >
        {checked && (
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        )}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {label}
          {disabled && (
            <span 
              className="ml-2 text-xs px-1.5 py-0.5 rounded"
              style={{ backgroundColor: 'var(--border-light)', color: 'var(--text-tertiary)' }}
            >
              Soon
            </span>
          )}
        </p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
          {description}
        </p>
      </div>
    </label>
  );
}

function RangeInput({
  label,
  value,
  min,
  max,
  step,
  onChange,
  suffix,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  suffix: string;
}) {
  return (
    <div>
      <div className="flex justify-between mb-2">
        <label className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          {label}
        </label>
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {value} {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{
          backgroundColor: 'var(--border-light)',
          accentColor: 'var(--accent-blue)',
        }}
      />
    </div>
  );
}

function NumberInput({
  label,
  value,
  placeholder,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number | null;
  placeholder: string;
  min: number;
  max: number;
  onChange: (value: number | null) => void;
}) {
  return (
    <div>
      <label className="text-sm mb-1.5 block" style={{ color: 'var(--text-secondary)' }}>
        {label}
      </label>
      <input
        type="number"
        min={min}
        max={max}
        value={value ?? ''}
        placeholder={placeholder}
        onChange={(e) => {
          const v = e.target.value ? parseInt(e.target.value) : null;
          onChange(v);
        }}
        className="w-full px-3 py-2 rounded-lg border text-sm outline-none transition-colors"
        style={{
          backgroundColor: 'var(--bg-page)',
          borderColor: 'var(--border-light)',
          color: 'var(--text-primary)',
        }}
      />
    </div>
  );
}

function ReasoningOption({
  value,
  label,
  description,
  selected,
  onChange,
}: {
  value: string;
  label: string;
  description: string;
  selected: boolean;
  onChange: () => void;
}) {
  return (
    <label 
      className="flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
      style={{
        backgroundColor: selected ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
        borderColor: selected ? 'var(--accent-blue)' : 'var(--border-light)',
      }}
    >
      <input
        type="radio"
        name="reasoningMode"
        value={value}
        checked={selected}
        onChange={onChange}
        className="sr-only"
      />
      <div 
        className={`w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors`}
        style={{
          borderColor: selected ? 'var(--accent-blue)' : 'var(--border-medium)',
        }}
      >
        {selected && (
          <div 
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: 'var(--accent-blue)' }}
          />
        )}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {label}
        </p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
          {description}
        </p>
      </div>
    </label>
  );
}
