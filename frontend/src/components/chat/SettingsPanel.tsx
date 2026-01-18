'use client';

import { useEffect, useState } from 'react';

interface Settings {
  openalexEnabled: boolean;
  semanticScholarEnabled: boolean;
  papersPerQuery: number;
}

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const DEFAULT_SETTINGS: Settings = {
  openalexEnabled: true,
  semanticScholarEnabled: true,
  papersPerQuery: 30,
};

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);

  // Load settings from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('sciencerag-settings');
    if (saved) {
      try {
        setSettings(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load settings:', e);
      }
    }
  }, []);

  // Save settings to localStorage
  const updateSettings = (updates: Partial<Settings>) => {
    const newSettings = { ...settings, ...updates };
    setSettings(newSettings);
    localStorage.setItem('sciencerag-settings', JSON.stringify(newSettings));
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="fixed right-0 top-0 h-full w-80 z-50 animate-slideInRight overflow-y-auto"
        style={{
          backgroundColor: 'var(--bg-primary)',
          borderLeft: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-xl)',
        }}
      >
        {/* Header */}
        <div
          className="sticky top-0 p-4 flex items-center justify-between"
          style={{
            backgroundColor: 'var(--bg-primary)',
            borderBottom: '1px solid var(--border-light)',
          }}
        >
          <h2
            className="text-lg font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >
            Settings
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md transition-colors"
            style={{ color: 'var(--text-tertiary)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
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

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Data Sources Section */}
          <section>
            <h3
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--text-secondary)' }}
            >
              Data Sources
            </h3>
            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.openalexEnabled}
                  onChange={(e) => updateSettings({ openalexEnabled: e.target.checked })}
                  className="w-4 h-4 rounded accent-blue-600"
                />
                <span style={{ color: 'var(--text-primary)' }}>OpenAlex</span>
                <span
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: 'var(--accent-success)',
                    color: 'white',
                  }}
                >
                  250M+ works
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.semanticScholarEnabled}
                  onChange={(e) => updateSettings({ semanticScholarEnabled: e.target.checked })}
                  className="w-4 h-4 rounded accent-blue-600"
                />
                <span style={{ color: 'var(--text-primary)' }}>Semantic Scholar</span>
                <span
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: 'var(--accent-primary)',
                    color: 'white',
                  }}
                >
                  200M+ papers
                </span>
              </label>
              <label className="flex items-center gap-3 cursor-not-allowed opacity-50">
                <input
                  type="checkbox"
                  disabled
                  className="w-4 h-4 rounded"
                />
                <span style={{ color: 'var(--text-primary)' }}>PubMed</span>
                <span
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    color: 'var(--text-muted)',
                  }}
                >
                  coming soon
                </span>
              </label>
            </div>
          </section>

          {/* Divider */}
          <hr style={{ borderColor: 'var(--border-light)' }} />

          {/* Results Section */}
          <section>
            <h3
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--text-secondary)' }}
            >
              Results
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span style={{ color: 'var(--text-primary)' }}>Papers per query</span>
                <select
                  value={settings.papersPerQuery}
                  onChange={(e) => updateSettings({ papersPerQuery: parseInt(e.target.value) })}
                  className="px-3 py-1.5 rounded-md text-sm"
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-light)',
                    color: 'var(--text-primary)',
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={30}>30</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </div>
          </section>

          {/* Divider */}
          <hr style={{ borderColor: 'var(--border-light)' }} />

          {/* Keyboard Shortcuts */}
          <section>
            <h3
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--text-secondary)' }}
            >
              Keyboard Shortcuts
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span style={{ color: 'var(--text-muted)' }}>Focus input</span>
                <kbd
                  className="px-2 py-0.5 rounded text-xs font-mono"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  ⌘K
                </kbd>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--text-muted)' }}>Submit query</span>
                <kbd
                  className="px-2 py-0.5 rounded text-xs font-mono"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Enter
                </kbd>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--text-muted)' }}>New line</span>
                <kbd
                  className="px-2 py-0.5 rounded text-xs font-mono"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  ⇧Enter
                </kbd>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--text-muted)' }}>Close panel</span>
                <kbd
                  className="px-2 py-0.5 rounded text-xs font-mono"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Esc
                </kbd>
              </div>
            </div>
          </section>

          {/* Divider */}
          <hr style={{ borderColor: 'var(--border-light)' }} />

          {/* About Section */}
          <section>
            <h3
              className="text-sm font-medium mb-3"
              style={{ color: 'var(--text-secondary)' }}
            >
              About
            </h3>
            <div className="space-y-2">
              <p style={{ color: 'var(--text-muted)' }} className="text-sm">
                ScienceRAG v1.0
              </p>
              <p style={{ color: 'var(--text-muted)' }} className="text-xs">
                AI-powered scientific literature intelligence platform.
                Built for researchers, by researchers.
              </p>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
