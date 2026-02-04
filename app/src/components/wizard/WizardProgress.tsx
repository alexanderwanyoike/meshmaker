import { usePipelineStore } from '../../store/pipelineStore';

const steps = [
  { label: 'Generate', description: 'Create 3D model' },
  { label: 'Rig', description: 'Add skeleton' },
  { label: 'Animate', description: 'Add motion' },
  { label: 'Export', description: 'Save result' },
];

export function WizardProgress() {
  const currentStep = usePipelineStore((state) => state.currentStep);

  return (
    <div className="flex justify-between mb-8">
      {steps.map((step, index) => (
        <div key={step.label} className="flex flex-col items-center flex-1">
          <div className="flex items-center w-full">
            {index > 0 && (
              <div
                className={`h-1 flex-1 ${
                  index <= currentStep ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              />
            )}
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                index < currentStep
                  ? 'bg-green-500 text-white'
                  : index === currentStep
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-300 text-gray-600'
              }`}
            >
              {index < currentStep ? '✓' : index + 1}
            </div>
            {index < steps.length - 1 && (
              <div
                className={`h-1 flex-1 ${
                  index < currentStep ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              />
            )}
          </div>
          <span
            className={`mt-2 text-sm font-medium ${
              index <= currentStep ? 'text-blue-500' : 'text-gray-500'
            }`}
          >
            {step.label}
          </span>
          <span className="text-xs text-gray-400">{step.description}</span>
        </div>
      ))}
    </div>
  );
}
