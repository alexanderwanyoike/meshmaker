import { useState } from 'react';
import { usePipelineStore } from '../../store/pipelineStore';
import { WizardProgress } from './WizardProgress';
import { GenerateStep } from '../steps/GenerateStep';
import { RigStep } from '../steps/RigStep';
import { AnimateStep } from '../steps/AnimateStep';
import { ExportStep } from '../steps/ExportStep';
import { Settings } from '../Settings';

export function Wizard() {
  const currentStep = usePipelineStore((state) => state.currentStep);
  const [showSettings, setShowSettings] = useState(false);

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
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">CharMaker</h1>
        <button
          onClick={() => setShowSettings(true)}
          title="Configure RunPod API"
          className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors text-xl"
        >
          ⚙️
        </button>
      </div>
      <WizardProgress />
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        {renderStep()}
      </div>
      {showSettings && <Settings onClose={() => setShowSettings(false)} />}
    </div>
  );
}
