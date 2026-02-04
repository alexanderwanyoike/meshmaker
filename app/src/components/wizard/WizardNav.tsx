import { usePipelineStore } from '../../store/pipelineStore';

interface WizardNavProps {
  canProceed: boolean;
  onNext?: () => void;
  nextLabel?: string;
}

export function WizardNav({ canProceed, onNext, nextLabel }: WizardNavProps) {
  const { currentStep, nextStep, prevStep, isProcessing } = usePipelineStore();

  const handleNext = () => {
    if (onNext) {
      onNext();
    } else {
      nextStep();
    }
  };

  return (
    <div className="flex justify-between mt-8 pt-4 border-t border-gray-200">
      <button
        onClick={prevStep}
        disabled={currentStep === 0 || isProcessing}
        className="px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-gray-200 hover:bg-gray-300 text-gray-700"
      >
        Previous
      </button>
      <button
        onClick={handleNext}
        disabled={!canProceed || isProcessing}
        className="px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-blue-500 hover:bg-blue-600 text-white"
      >
        {isProcessing ? 'Processing...' : nextLabel || (currentStep === 3 ? 'Export' : 'Next')}
      </button>
    </div>
  );
}
