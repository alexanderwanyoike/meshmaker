import { useEffect } from 'react';
import { usePipelineStore } from '../../store/pipelineStore';
import { WizardNav } from '../wizard/WizardNav';
import { mockRigModel } from '../../mocks/mockData';

export function RigStep() {
  const {
    generatedModel,
    riggedModel,
    setRiggedModel,
    setIsProcessing,
    isProcessing,
    nextStep,
  } = usePipelineStore();

  useEffect(() => {
    if (!riggedModel && generatedModel && !isProcessing) {
      const runRigging = async () => {
        setIsProcessing(true);
        try {
          const model = await mockRigModel();
          setRiggedModel(model);
        } catch (error) {
          console.error('Failed to rig model:', error);
        } finally {
          setIsProcessing(false);
        }
      };
      runRigging();
    }
  }, [generatedModel, riggedModel, isProcessing, setRiggedModel, setIsProcessing]);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Rig Model</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Adding a skeleton to your 3D model for animation.
      </p>

      <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-8 text-center">
        {isProcessing ? (
          <div className="space-y-4">
            <div className="animate-spin text-4xl">⚙️</div>
            <p className="text-gray-600 dark:text-gray-300">Rigging model...</p>
            <div className="w-full bg-gray-300 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full animate-pulse w-2/3"></div>
            </div>
          </div>
        ) : riggedModel ? (
          <div className="space-y-4">
            <div className="text-green-500 text-4xl">✓</div>
            <p className="text-gray-600 dark:text-gray-300">Rigging complete!</p>
            <div className="text-sm text-gray-500 space-y-1">
              <p>Vertices: {riggedModel.metadata.vertices?.toLocaleString()}</p>
              <p>Bones: {riggedModel.metadata.bones}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-gray-400 text-4xl">🦴</div>
            <p className="text-gray-500">Waiting to start rigging...</p>
          </div>
        )}
      </div>

      <WizardNav canProceed={!!riggedModel} onNext={nextStep} />
    </div>
  );
}
