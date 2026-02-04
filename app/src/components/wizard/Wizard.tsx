import { usePipelineStore } from '../../store/pipelineStore';
import { WizardProgress } from './WizardProgress';
import { GenerateStep } from '../steps/GenerateStep';
import { RigStep } from '../steps/RigStep';
import { AnimateStep } from '../steps/AnimateStep';
import { ExportStep } from '../steps/ExportStep';

export function Wizard() {
  const currentStep = usePipelineStore((state) => state.currentStep);

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <GenerateStep />;
      case 1:
        return <RigStep />;
      case 2:
        return <AnimateStep />;
      case 3:
        return <ExportStep />;
      default:
        return <GenerateStep />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-center mb-8">CharMaker</h1>
      <WizardProgress />
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        {renderStep()}
      </div>
    </div>
  );
}
