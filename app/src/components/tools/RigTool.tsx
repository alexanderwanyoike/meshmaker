import { useState } from 'react';
import { readFile, writeFile } from '@tauri-apps/plugin-fs';
import { useFilePicker } from '../../hooks/useFilePicker';
import { rigModel } from '../../services/pipeline';
import type { GeneratedModel } from '../../types/pipeline';
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

export function RigTool() {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [outputData, setOutputData] = useState<string | null>(null);

  const { pickGlb, pickSaveLocation } = useFilePicker();

  const handlePickGlb = async () => {
    try {
      const path = await pickGlb();
      if (path) {
        setInputPath(path);
        setOutputData(null);
        setError(null);
        setStatusMessage(null);
      }
    } catch (err) {
      setError('Failed to pick GLB file');
      console.error(err);
    }
  };

  const handleRig = async () => {
    if (!inputPath) return;
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
      const model: GeneratedModel = {
        id: 'upload-' + Date.now(),
        format: 'glb',
        data,
        metadata: {},
      };
      const rigged = await rigModel(config, model, setStatusMessage);
      setOutputData(rigged.data);
      setStatusMessage('Rigging complete!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rigging failed');
      setStatusMessage(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSave = async () => {
    if (!outputData) return;
    try {
      const savePath = await pickSaveLocation('rigged.fbx');
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

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-2">Auto Rigger</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Upload a GLB file to add a skeleton and export a rigged FBX.
      </p>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">GLB File</label>
          <div
            onClick={handlePickGlb}
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
                <p className="text-gray-500">Click to select a GLB file</p>
                <p className="text-xs text-gray-400">.glb</p>
              </div>
            )}
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
            onClick={handleRig}
            disabled={!inputPath || isProcessing}
            className="flex-1 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? 'Rigging...' : 'Rig Model'}
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
