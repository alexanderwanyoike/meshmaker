import { usePipelineStore } from '../../store/pipelineStore';
import { WizardNav } from '../wizard/WizardNav';
import { animateModel } from '../../services/pipeline';
import { loadConfig, isConfigured } from '../../config';

export function AnimateStep() {
  const {
    riggedModel,
    animationPrompt,
    animationDuration,
    isProcessing,
    error,
    statusMessage,
    setAnimationPrompt,
    setAnimationDuration,
    setAnimatedModel,
    setIsProcessing,
    setError,
    setStatusMessage,
    nextStep,
  } = usePipelineStore();

  const handleAnimate = async () => {
    if (!riggedModel) return;

    const config = loadConfig();
    if (!isConfigured(config)) {
      setError('RunPod is not configured. Click ⚙️ to enter your API key and endpoint IDs.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    try {
      const model = await animateModel(
        config,
        riggedModel,
        animationPrompt,
        animationDuration,
        setStatusMessage,
      );
      setAnimatedModel(model);
      setStatusMessage(null);
      nextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Animation failed');
      setStatusMessage(null);
    } finally {
      setIsProcessing(false);
    }
  };

  const canProceed = animationPrompt.trim().length > 0 && !isProcessing;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Animate Model</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Describe the animation you want for your character.
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Animation Prompt</label>
          <textarea
            value={animationPrompt}
            onChange={(e) => setAnimationPrompt(e.target.value)}
            placeholder="Describe the animation... (e.g., 'Walking forward with arms swinging')"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none dark:bg-gray-700 dark:border-gray-600"
            rows={3}
            disabled={isProcessing}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Duration: {animationDuration} seconds
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={animationDuration}
            onChange={(e) => setAnimationDuration(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            disabled={isProcessing}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1s</span>
            <span>10s</span>
          </div>
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
        canProceed={canProceed}
        onNext={handleAnimate}
        nextLabel={isProcessing ? 'Animating...' : 'Animate'}
      />
    </div>
  );
}
