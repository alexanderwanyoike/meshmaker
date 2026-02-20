import { useState } from 'react';
import { writeFile } from '@tauri-apps/plugin-fs';
import { useFilePicker } from '../../hooks/useFilePicker';
import { generate3D } from '../../services/pipeline';
import { loadConfig, isConfigured } from '../../config';

function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

export function MeshTool() {
  const [inputPath, setInputPath] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [outputData, setOutputData] = useState<string | null>(null);

  const { pickImage, pickSaveLocation } = useFilePicker();

  const handlePickImage = async () => {
    try {
      const path = await pickImage();
      if (path) {
        setInputPath(path);
        setOutputData(null);
        setError(null);
        setStatusMessage(null);
      }
    } catch (err) {
      setError('Failed to pick image');
      console.error(err);
    }
  };

  const handleGenerate = async () => {
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
      const model = await generate3D(config, inputPath, setStatusMessage);
      setOutputData(model.data);
      setStatusMessage('Mesh generated successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setStatusMessage(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSave = async () => {
    if (!outputData) return;
    try {
      const savePath = await pickSaveLocation('model.glb');
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
      <h2 className="text-2xl font-bold mb-2">Mesh Generator</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Upload an image to generate a 3D GLB mesh.
      </p>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Image Input</label>
          <div
            onClick={handlePickImage}
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
                <p className="text-gray-500">Click to select an image</p>
                <p className="text-xs text-gray-400">PNG, JPG, JPEG, or WebP</p>
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
            onClick={handleGenerate}
            disabled={!inputPath || isProcessing}
            className="flex-1 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? 'Generating...' : 'Generate Mesh'}
          </button>
          {outputData && (
            <button
              onClick={handleSave}
              className="flex-1 py-3 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors"
            >
              Save GLB
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
