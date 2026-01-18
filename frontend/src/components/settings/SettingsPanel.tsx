'use client';

import { useState, useEffect } from 'react';
import { api, UserSettings } from '@/lib/api';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
      setError(null);
    } catch (err) {
      setError('Failed to load settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = async <K extends keyof UserSettings>(
    key: K,
    value: UserSettings[K]
  ) => {
    if (!settings) return;

    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);

    try {
      setSaving(true);
      await api.updateSettings({ [key]: value });
    } catch (err) {
      console.error('Failed to save setting:', err);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = async () => {
    try {
      setSaving(true);
      const data = await api.resetSettings();
      setSettings(data);
    } catch (err) {
      setError('Failed to reset settings');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className="relative w-full max-w-md bg-white shadow-xl overflow-y-auto"
        style={{ backgroundColor: 'var(--bg-card)' }}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Settings
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-zinc-100 transition-colors"
          >
            <svg className="w-5 h-5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="p-6 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : error ? (
          <div className="p-6 text-center text-red-500">{error}</div>
        ) : settings ? (
          <div className="p-6 space-y-8">
            {/* Retrieval Settings */}
            <section>
              <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4">
                Retrieval Settings
              </h3>

              {/* Data Sources */}
              <div className="space-y-3 mb-6">
                <label className="text-sm font-medium text-zinc-700">Data Sources</label>
                {[
                  { id: 'openalex', name: 'OpenAlex', desc: '250M+ papers, all disciplines' },
                  { id: 'semantic_scholar', name: 'Semantic Scholar', desc: '200M+ papers, strong in CS/AI' },
                ].map(source => (
                  <label key={source.id} className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.default_sources.includes(source.id)}
                      onChange={(e) => {
                        const newSources = e.target.checked
                          ? [...settings.default_sources, source.id]
                          : settings.default_sources.filter(s => s !== source.id);
                        updateSetting('default_sources', newSources);
                      }}
                      className="mt-1 w-4 h-4 text-blue-500 rounded border-zinc-300"
                    />
                    <div>
                      <div className="text-sm text-zinc-700">{source.name}</div>
                      <div className="text-xs text-zinc-400">{source.desc}</div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Papers per Query */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Papers per Query: {settings.papers_per_query}
                </label>
                <input
                  type="range"
                  min={10}
                  max={200}
                  step={10}
                  value={settings.papers_per_query}
                  onChange={(e) => updateSetting('papers_per_query', parseInt(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-zinc-400 mt-1">
                  <span>10</span>
                  <span>100</span>
                  <span>200</span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">
                  More papers = better coverage, but slower processing
                </p>
              </div>

              {/* Year Range */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Publication Year Range
                </label>
                <div className="flex items-center gap-3">
                  <select
                    value={settings.year_from || ''}
                    onChange={(e) => updateSetting('year_from', e.target.value ? parseInt(e.target.value) : null)}
                    className="flex-1 px-3 py-2 border border-zinc-200 rounded-lg text-sm"
                  >
                    <option value="">Any</option>
                    {Array.from({ length: 30 }, (_, i) => 2024 - i).map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                  <span className="text-zinc-400">to</span>
                  <select
                    value={settings.year_to || ''}
                    onChange={(e) => updateSetting('year_to', e.target.value ? parseInt(e.target.value) : null)}
                    className="flex-1 px-3 py-2 border border-zinc-200 rounded-lg text-sm"
                  >
                    <option value="">Any</option>
                    {Array.from({ length: 30 }, (_, i) => 2024 - i).map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Min Citations */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Minimum Citations: {settings.min_citations}
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={settings.min_citations}
                  onChange={(e) => updateSetting('min_citations', parseInt(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-zinc-400 mt-1">
                  <span>0</span>
                  <span>50</span>
                  <span>100+</span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">
                  Higher = more established papers, may miss recent work
                </p>
              </div>
            </section>

            {/* Synthesis Settings */}
            <section>
              <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4">
                Synthesis Settings
              </h3>

              {/* Detail Level */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Detail Level
                </label>
                <div className="space-y-2">
                  {[
                    { value: 'brief', label: 'Brief', desc: 'Quick overview, key points only' },
                    { value: 'balanced', label: 'Balanced', desc: 'Standard detail with citations' },
                    { value: 'detailed', label: 'Detailed', desc: 'Comprehensive with methodology notes' },
                  ].map(option => (
                    <label key={option.value} className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="radio"
                        name="synthesis_detail"
                        checked={settings.synthesis_detail === option.value}
                        onChange={() => updateSetting('synthesis_detail', option.value as 'brief' | 'balanced' | 'detailed')}
                        className="mt-1 w-4 h-4 text-blue-500"
                      />
                      <div>
                        <div className="text-sm text-zinc-700">{option.label}</div>
                        <div className="text-xs text-zinc-400">{option.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Max Sources Cited */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Maximum Sources to Cite: {settings.max_sources_cited}
                </label>
                <input
                  type="range"
                  min={5}
                  max={25}
                  value={settings.max_sources_cited}
                  onChange={(e) => updateSetting('max_sources_cited', parseInt(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-zinc-400 mt-1">
                  <span>5</span>
                  <span>15</span>
                  <span>25</span>
                </div>
              </div>

              {/* Include Sections */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Include Sections
                </label>
                <div className="space-y-2">
                  {[
                    { key: 'include_consensus', label: 'Scientific Consensus' },
                    { key: 'include_contested', label: 'Contested Findings' },
                    { key: 'include_limitations', label: 'Limitations & Gaps' },
                    { key: 'include_methodology', label: 'Methodology Notes' },
                  ].map(section => (
                    <label key={section.key} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings[section.key as keyof UserSettings] as boolean}
                        onChange={(e) => updateSetting(section.key as keyof UserSettings, e.target.checked as never)}
                        className="w-4 h-4 text-blue-500 rounded border-zinc-300"
                      />
                      <span className="text-sm text-zinc-700">{section.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </section>

            {/* RAG Settings */}
            <section>
              <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4">
                RAG Settings (Advanced)
              </h3>

              {/* Chunks per Query */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Chunks per Query: {settings.chunks_per_query}
                </label>
                <input
                  type="range"
                  min={5}
                  max={50}
                  step={5}
                  value={settings.chunks_per_query}
                  onChange={(e) => updateSetting('chunks_per_query', parseInt(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-zinc-400 mt-1">
                  <span>5</span>
                  <span>25</span>
                  <span>50</span>
                </div>
              </div>

              {/* Similarity Threshold */}
              <div className="mb-6">
                <label className="text-sm font-medium text-zinc-700 block mb-2">
                  Similarity Threshold: {settings.similarity_threshold.toFixed(2)}
                </label>
                <input
                  type="range"
                  min={0.5}
                  max={0.95}
                  step={0.05}
                  value={settings.similarity_threshold}
                  onChange={(e) => updateSetting('similarity_threshold', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-zinc-400 mt-1">
                  <span>0.5 (broad)</span>
                  <span>0.95 (strict)</span>
                </div>
                <p className="text-xs text-zinc-400 mt-1">
                  Lower = more results, possibly less relevant
                </p>
              </div>

              {/* Boolean options */}
              <div className="space-y-2">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.reranking_enabled}
                    onChange={(e) => updateSetting('reranking_enabled', e.target.checked)}
                    className="w-4 h-4 text-blue-500 rounded border-zinc-300"
                  />
                  <span className="text-sm text-zinc-700">Enable reranking (recommended)</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.diversify_sources}
                    onChange={(e) => updateSetting('diversify_sources', e.target.checked)}
                    className="w-4 h-4 text-blue-500 rounded border-zinc-300"
                  />
                  <span className="text-sm text-zinc-700">Diversify sources (avoid over-citing)</span>
                </label>
              </div>
            </section>

            {/* Actions */}
            <div className="pt-6 border-t flex items-center justify-between">
              <button
                onClick={resetToDefaults}
                disabled={saving}
                className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                Reset to Defaults
              </button>
              <button
                onClick={onClose}
                className="px-6 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors"
              >
                Done
              </button>
            </div>

            {/* Save indicator */}
            {saving && (
              <div className="fixed bottom-4 right-4 bg-zinc-900 text-white text-sm px-4 py-2 rounded-lg">
                Saving...
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
