import { usePipelineStore } from '../../store/pipelineStore';
import { useFilePicker } from '../../hooks/useFilePicker';
import { WizardNav } from '../wizard/WizardNav';
import { mockGenerateModel } from '../../mocks/mockData';

export function GenerateStep() {
  const {
    inputImage,
    inputPrompt,
    setInputImage,
    setInputPrompt,
    setGeneratedModel,
    setIsProcessing,
    nextStep,
  } = usePipelineStore();
  const { pickImage } = useFilePicker();

  const handlePickImage = async () => {
    try {
      const path = await pickImage();
      if (path) {
        setInputImage(path);
      }
    } catch (error) {
      console.error('Failed to pick image:', error);
    }
  };

  const handleGenerate = async () => {
    setIsProcessing(true);
    try {
      const model = await mockGenerateModel();
      setGeneratedModel(model);
      nextStep();
    } catch (error) {
      console.error('Failed to generate model:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const canProceed = !!(inputImage || inputPrompt.trim());

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Generate 3D Model</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Upload an image or enter a text prompt to generate a 3D character model.
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
                <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
                  {inputImage}
                </p>
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
          <label className="block text-sm font-medium mb-2">Text Prompt</label>
          <textarea
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder="Describe your character... (e.g., 'A fantasy warrior with blue armor')"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none dark:bg-gray-700 dark:border-gray-600"
            rows={3}
          />
        </div>
      </div>

      <WizardNav canProceed={canProceed} onNext={handleGenerate} nextLabel="Generate" />
    </div>
  );
}
