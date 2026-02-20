import { useState } from 'react';
import { loadConfig, saveConfig } from '../config';
import type { RunPodConfig } from '../types/pipeline';

interface SettingsProps {
  onClose: () => void;
}

export function Settings({ onClose }: SettingsProps) {
  const [config, setConfig] = useState<Partial<RunPodConfig>>(() => loadConfig());
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    saveConfig(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const field = (
    key: keyof RunPodConfig,
    label: string,
    placeholder: string,
    secret = false,
  ) => (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        type={secret ? 'password' : 'text'}
        value={config[key] ?? ''}
        onChange={(e) => setConfig((prev) => ({ ...prev, [key]: e.target.value }))}
        placeholder={placeholder}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600"
      />
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">RunPod Configuration</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {field('apiKey', 'API Key', 'rpa_...', true)}
          {field('trellisEndpointId', 'Trellis Endpoint ID', 'abc123xyz')}
          {field('unirirEndpointId', 'UniRig Endpoint ID', 'abc123xyz')}
          {field('hymotionEndpointId', 'HyMotion Endpoint ID', 'abc123xyz')}
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
          Find endpoint IDs in your RunPod serverless dashboard.
        </p>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
          >
            {saved ? '✓ Saved' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
