import type { RunPodConfig } from './types/pipeline';

const CONFIG_KEY = 'charmaker_runpod_config';

export function loadConfig(): Partial<RunPodConfig> {
  try {
    const stored = localStorage.getItem(CONFIG_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

export function saveConfig(config: Partial<RunPodConfig>): void {
  localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}

export function isConfigured(config: Partial<RunPodConfig>): config is RunPodConfig {
  return !!(
    config.apiKey &&
    config.trellisEndpointId &&
    config.unirirEndpointId &&
    config.hymotionEndpointId
  );
}
