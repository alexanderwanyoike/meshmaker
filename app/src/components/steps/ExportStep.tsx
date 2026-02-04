import { usePipelineStore } from '../../store/pipelineStore';
import { useFilePicker } from '../../hooks/useFilePicker';
import { WizardNav } from '../wizard/WizardNav';
import { mockExportModel } from '../../mocks/mockData';
import type { ExportFormat } from '../../types/pipeline';

export function ExportStep() {
  const {
    animatedModel,
    exportFormat,
    exportPath,
    setExportFormat,
    setExportPath,
    setIsProcessing,
    reset,
  } = usePipelineStore();
  const { pickSaveLocation } = useFilePicker();

  const handlePickSaveLocation = async () => {
    try {
      const path = await pickSaveLocation(`character.${exportFormat}`);
      if (path) {
        setExportPath(path);
      }
    } catch (error) {
      console.error('Failed to pick save location:', error);
    }
  };

  const handleExport = async () => {
    if (!exportPath) {
      handlePickSaveLocation();
      return;
    }

    setIsProcessing(true);
    try {
      await mockExportModel(exportFormat, exportPath);
      alert(`Model exported successfully to:\n${exportPath}`);
    } catch (error) {
      console.error('Failed to export model:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStartOver = () => {
    reset();
  };

  const formats: { value: ExportFormat; label: string; description: string }[] = [
    { value: 'glb', label: 'GLB', description: 'Recommended for web & game engines' },
    { value: 'fbx', label: 'FBX', description: 'Best for Unity, Unreal, Maya' },
  ];

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Export Model</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Choose your export format and save location.
      </p>

      <div className="space-y-6">
        {animatedModel && (
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <h3 className="font-medium text-green-800 dark:text-green-300 mb-2">
              Model Ready for Export
            </h3>
            <div className="text-sm text-green-700 dark:text-green-400 space-y-1">
              <p>Vertices: {animatedModel.metadata.vertices?.toLocaleString()}</p>
              <p>Bones: {animatedModel.metadata.bones}</p>
              <p>FPS: {animatedModel.metadata.fps}</p>
              <p>Duration: {animatedModel.metadata.duration}s</p>
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-3">Export Format</label>
          <div className="grid grid-cols-2 gap-4">
            {formats.map((format) => (
              <button
                key={format.value}
                onClick={() => setExportFormat(format.value)}
                className={`p-4 rounded-lg border-2 text-left transition-colors ${
                  exportFormat === format.value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 hover:border-gray-300 dark:border-gray-600'
                }`}
              >
                <div className="font-medium">{format.label}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {format.description}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Save Location</label>
          <div
            onClick={handlePickSaveLocation}
            className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition-colors"
          >
            {exportPath ? (
              <div className="space-y-1">
                <div className="text-green-500">✓</div>
                <p className="text-sm text-gray-600 dark:text-gray-300 truncate">
                  {exportPath}
                </p>
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

        <button
          onClick={handleStartOver}
          className="w-full py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
        >
          Start Over
        </button>
      </div>

      <WizardNav canProceed={true} onNext={handleExport} nextLabel="Export" />
    </div>
  );
}
