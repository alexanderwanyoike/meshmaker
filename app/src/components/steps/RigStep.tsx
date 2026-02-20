import { useEffect } from 'react';
import { usePipelineStore } from '../../store/pipelineStore';
import { WizardNav } from '../wizard/WizardNav';
import { rigModel } from '../../services/pipeline';
import { loadConfig, isConfigured } from '../../config';

export function RigStep() {
  const {
    generatedModel,
    riggedModel,
    isProcessing,
    error,
    statusMessage,
    setRiggedModel,
    setIsProcessing,
    setError,
    setStatusMessage,
    nextStep,
  } = usePipelineStore();

  useEffect(() => {
    if (!riggedModel && generatedModel && !isProcessing && !error) {
      const run = async () => {
        const config = loadConfig();
        if (!isConfigured(config)) {
          setError('RunPod is not configured. Click ⚙️ to enter your API key and endpoint IDs.');
          return;
        }

        setIsProcessing(true);
        try {
          const model = await rigModel(config, generatedModel, setStatusMessage);
          setRiggedModel(model);
          setStatusMessage(null);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Rigging failed');
          setStatusMessage(null);
        } finally {
          setIsProcessing(false);
        }
      };
      run();
    }
  }, [generatedModel, riggedModel, isProcessing, error, setRiggedModel, setIsProcessing, setError, setStatusMessage]);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Rig Model</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Adding a Mixamo-compatible skeleton to your 3D model.
      </p>

      <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-8 text-center">
        {isProcessing ? (
          <div className="space-y-4">
            <div className="animate-spin text-4xl">⚙️</div>
            <p className="text-gray-600 dark:text-gray-300">
              {statusMessage ?? 'Rigging model...'}
            </p>
            <div className="w-full bg-gray-300 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full animate-pulse w-2/3"></div>
            </div>
            <p className="text-xs text-gray-400">This may take a few minutes on cold start</p>
          </div>
        ) : error ? (
          <div className="space-y-3">
            <div className="text-red-500 text-4xl">✗</div>
            <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
          </div>
        ) : riggedModel ? (
          <div className="space-y-4">
            <div className="text-green-500 text-4xl">✓</div>
            <p className="text-gray-600 dark:text-gray-300">Rigging complete!</p>
            {riggedModel.metadata.generationTime && (
              <p className="text-sm text-gray-500">
                Completed in {riggedModel.metadata.generationTime.toFixed(1)}s
              </p>
            )}
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
