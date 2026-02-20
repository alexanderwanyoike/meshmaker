import { usePipelineStore } from '../../store/pipelineStore';
import { useFilePicker } from '../../hooks/useFilePicker';
import { WizardNav } from '../wizard/WizardNav';
import { exportModel } from '../../services/pipeline';

export function ExportStep() {
  const {
    animatedModel,
    exportPath,
    isProcessing,
    error,
    setExportPath,
    setIsProcessing,
    setError,
    reset,
  } = usePipelineStore();
  const { pickSaveLocation } = useFilePicker();

  const handlePickSaveLocation = async () => {
    try {
      const path = await pickSaveLocation('character.fbx');
      if (path) setExportPath(path);
    } catch (err) {
      console.error('Failed to pick save location:', err);
    }
  };

  const handleExport = async () => {
    if (!exportPath) {
      await handlePickSaveLocation();
      return;
    }
    if (!animatedModel) return;

    setIsProcessing(true);
    setError(null);
    try {
      await exportModel(animatedModel, exportPath);
      alert(`Character exported successfully to:\n${exportPath}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Export Character</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Save your animated character as an FBX file for use in Unity, Unreal, or Godot.
      </p>

      <div className="space-y-6">
        {animatedModel && (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <h3 className="font-medium text-green-800 dark:text-green-300 mb-2">
              Character Ready for Export
            </h3>
            <div className="text-sm text-green-700 dark:text-green-400 space-y-1">
              <p>Format: Animated FBX (Mixamo skeleton)</p>
              {animatedModel.metadata.duration && (
                <p>Duration: {animatedModel.metadata.duration}s @ {animatedModel.metadata.fps ?? 30} FPS</p>
              )}
              {animatedModel.metadata.generationTime && (
                <p>Generated in: {animatedModel.metadata.generationTime.toFixed(1)}s</p>
              )}
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2">Save Location</label>
          <div
            onClick={handlePickSaveLocation}
            className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition-colors"
          >
            {exportPath ? (
              <div className="space-y-1">
                <div className="text-green-500">✓</div>
                <p className="text-sm text-gray-600 dark:text-gray-300 truncate">{exportPath}</p>
                <p className="text-xs text-gray-400">Click to change</p>
              </div>
            ) : (
              <div className="space-y-1">
                <div className="text-gray-400">📁</div>
                <p className="text-gray-500">Click to choose save location</p>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {error}
          </div>
        )}

        <button
          onClick={reset}
          className="w-full py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        >
          Start Over
        </button>
      </div>

      <WizardNav
        canProceed={!isProcessing}
        onNext={handleExport}
        nextLabel={isProcessing ? 'Exporting...' : 'Export'}
      />
    </div>
  );
}
