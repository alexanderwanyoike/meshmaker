import { useState } from 'react';
import { readFile, writeFile } from '@tauri-apps/plugin-fs';
import { useFilePicker } from '../../hooks/useFilePicker';
import { animateModel } from '../../services/pipeline';
import type { RiggedModel } from '../../types/pipeline';
import { loadConfig, isConfigured } from '../../config';

function uint8ArrayToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

export function AnimateTool() {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [animationPrompt, setAnimationPrompt] = useState('');
  const [duration, setDuration] = useState(3);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [outputData, setOutputData] = useState<string | null>(null);

  const { pickFbx, pickSaveLocation } = useFilePicker();

  const handlePickFbx = async () => {
    try {
      const path = await pickFbx();
      if (path) {
        setInputPath(path);
        setOutputData(null);
        setError(null);
        setStatusMessage(null);
      }
    } catch (err) {
      setError('Failed to pick FBX file');
      console.error(err);
    }
  };

  const handleAnimate = async () => {
    if (!inputPath || !animationPrompt.trim()) return;
    const config = loadConfig();
    if (!isConfigured(config)) {
      setError('RunPod is not configured. Click Settings to enter your API key and endpoint IDs.');
      return;
    }
    setIsProcessing(true);
    setError(null);
    setStatusMessage(null);
    setOutputData(null);
    try {
      const bytes = await readFile(inputPath);
      const data = uint8ArrayToBase64(bytes);
      const model: RiggedModel = {
        id: 'upload-' + Date.now(),
        format: 'fbx',
        data,
        metadata: {},
      };
      const animated = await animateModel(config, model, animationPrompt, duration, setStatusMessage);
      setOutputData(animated.data);
      setStatusMessage('Animation complete!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Animation failed');
      setStatusMessage(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSave = async () => {
    if (!outputData) return;
    try {
      const savePath = await pickSaveLocation('animated.fbx');
      if (savePath) {
        const bytes = base64ToUint8Array(outputData);
        await writeFile(savePath, bytes);
        setStatusMessage('Saved to ' + savePath);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
      console.error(err);
    }
  };

  const canAnimate = !!(inputPath && animationPrompt.trim()) && !isProcessing;

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-2">Animator</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Upload a rigged FBX, describe the animation, and export an animated FBX.
      </p>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Rigged FBX File</label>
          <div
            onClick={handlePickFbx}
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
          >
            {inputPath ? (
              <div className="space-y-2">
                <div className="text-green-500 text-2xl font-bold">Selected</div>
                <p className="text-sm text-gray-600 dark:text-gray-300 truncate">{inputPath}</p>
                <p className="text-xs text-gray-400">Click to change</p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-gray-500">Click to select a rigged FBX file</p>
                <p className="text-xs text-gray-400">.fbx</p>
              </div>
            )}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Animation Prompt</label>
          <textarea
            value={animationPrompt}
            onChange={(e) => setAnimationPrompt(e.target.value)}
            placeholder="Describe the animation... (e.g., 'Walking forward with arms swinging')"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none dark:bg-gray-700 dark:border-gray-600"
            rows={3}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">
            Duration: {duration} seconds
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1s</span>
            <span>10s</span>
          </div>
        </div>
        {statusMessage && (
          <div className={`px-4 py-2 rounded-full text-sm text-center ${outputData ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}>
            {statusMessage}
          </div>
        )}
        {error && (
          <div className="px-4 py-2 rounded-lg text-sm bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}
        <div className="flex gap-3">
          <button
            onClick={handleAnimate}
            disabled={!canAnimate}
            className="flex-1 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? 'Animating...' : 'Animate'}
          </button>
          {outputData && (
            <button
              onClick={handleSave}
              className="flex-1 py-3 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors"
            >
              Save FBX
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
