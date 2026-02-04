export type WizardStep = 'generate' | 'rig' | 'animate' | 'export';

export interface ModelMetadata {
  vertices?: number;
  bones?: number;
  fps?: number;
  duration?: number;
}

export interface GeneratedModel {
  id: string;
  format: 'glb' | 'fbx';
  path: string;
  metadata: ModelMetadata;
}

export interface RiggedModel {
  id: string;
  format: 'glb' | 'fbx';
  path: string;
  metadata: ModelMetadata;
}

export interface AnimatedModel {
  id: string;
  format: 'glb' | 'fbx';
  path: string;
  metadata: ModelMetadata;
}

export type ExportFormat = 'fbx' | 'glb';

export interface PipelineState {
  currentStep: number;
  inputImage: string | null;
  inputPrompt: string;
  generatedModel: GeneratedModel | null;
  riggedModel: RiggedModel | null;
  animatedModel: AnimatedModel | null;
  animationPrompt: string;
  animationDuration: number;
  exportFormat: ExportFormat;
  exportPath: string | null;
  isProcessing: boolean;
}

export interface PipelineActions {
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: number) => void;
  setInputImage: (path: string | null) => void;
  setInputPrompt: (prompt: string) => void;
  setGeneratedModel: (model: GeneratedModel | null) => void;
  setRiggedModel: (model: RiggedModel | null) => void;
  setAnimatedModel: (model: AnimatedModel | null) => void;
  setAnimationPrompt: (prompt: string) => void;
  setAnimationDuration: (duration: number) => void;
  setExportFormat: (format: ExportFormat) => void;
  setExportPath: (path: string | null) => void;
  setIsProcessing: (processing: boolean) => void;
  reset: () => void;
}
