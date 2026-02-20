import { usePipelineStore } from '../../store/pipelineStore';
import { useFilePicker } from '../../hooks/useFilePicker';
import { WizardNav } from '../wizard/WizardNav';
import { generate3D } from '../../services/pipeline';
import { loadConfig, isConfigured } from '../../config';

export function GenerateStep() {
  const {
    inputImage,
    inputPrompt,
    isProcessing,
    error,
    statusMessage,
    setInputImage,
    setInputPrompt,
    setGeneratedModel,
    setIsProcessing,
    setError,
    setStatusMessage,
    nextStep,
  } = usePipelineStore();
  const { pickImage } = useFilePicker();

  const handlePickImage = async () => {
    try {
      const path = await pickImage();
      if (path) setInputImage(path);
    } catch (err) {
      console.error('Failed to pick image:', err);
    }
  };

  const handleGenerate = async () => {
    if (!inputImage) {
      setError('An image is required to generate a 3D model.');
      return;
    }

    const config = loadConfig();
    if (!isConfigured(config)) {
      setError('RunPod is not configured. Click ⚙️ to enter your API key and endpoint IDs.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    try {
      const model = await generate3D(config, inputImage, setStatusMessage);
      setGeneratedModel(model);
      setStatusMessage(null);
      nextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed');
      setStatusMessage(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const canProceed = !!(inputImage || inputPrompt.trim());

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Generate 3D Model</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Upload an image to generate a 3D character model.
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Image Input</label>
          <div
            onClick={handlePickImage}
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
          >
            {inputImage ? (
              <div className="space-y-2">
                <div className="text-green-500 text-4xl">✓</div>
                <p className="text-sm text-gray-600 dark:text-gray-300 truncate">{inputImage}</p>
                <p className="text-xs text-gray-400">Click to change</p>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-gray-400 text-4xl">📷</div>
                <p className="text-gray-500">Click to select an image</p>
                <p className="text-xs text-gray-400">PNG, JPG, JPEG, or WebP</p>
              </div>
            )}
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white dark:bg-gray-800 text-gray-500">or</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Text Prompt <span className="text-gray-400 font-normal">(future feature)</span>
          </label>
          <textarea
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder="Describe your character... (e.g., 'A fantasy warrior with blue armor')"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none dark:bg-gray-700 dark:border-gray-600 opacity-50"
            rows={3}
            disabled
          />
        </div>

        {statusMessage && (
          <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
            <div className="animate-spin">⚙️</div>
            <span>{statusMessage}</span>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {error}
          </div>
        )}
      </div>

      <WizardNav
        canProceed={canProceed && !isProcessing}
        onNext={handleGenerate}
        nextLabel={isProcessing ? 'Generating...' : 'Generate'}
      />
    </div>
  );
}
