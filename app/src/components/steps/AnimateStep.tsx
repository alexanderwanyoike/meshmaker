import { usePipelineStore } from '../../store/pipelineStore';
import { WizardNav } from '../wizard/WizardNav';
import { mockAnimateModel } from '../../mocks/mockData';

export function AnimateStep() {
  const {
    animationPrompt,
    animationDuration,
    setAnimationPrompt,
    setAnimationDuration,
    setAnimatedModel,
    setIsProcessing,
    nextStep,
  } = usePipelineStore();

  const handleAnimate = async () => {
    setIsProcessing(true);
    try {
      const model = await mockAnimateModel(animationDuration);
      setAnimatedModel(model);
      nextStep();
    } catch (error) {
      console.error('Failed to animate model:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const canProceed = animationPrompt.trim().length > 0;

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
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1s</span>
            <span>10s</span>
          </div>
        </div>
      </div>

      <WizardNav canProceed={canProceed} onNext={handleAnimate} nextLabel="Animate" />
    </div>
  );
}
