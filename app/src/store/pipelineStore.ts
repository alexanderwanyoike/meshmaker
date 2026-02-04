import { create } from 'zustand';
import type {
  PipelineState,
  PipelineActions,
  GeneratedModel,
  RiggedModel,
  AnimatedModel,
  ExportFormat,
} from '../types/pipeline';

const initialState: PipelineState = {
  currentStep: 0,
  inputImage: null,
  inputPrompt: '',
  generatedModel: null,
  riggedModel: null,
  animatedModel: null,
  animationPrompt: '',
  animationDuration: 3,
  exportFormat: 'glb',
  exportPath: null,
  isProcessing: false,
};

export const usePipelineStore = create<PipelineState & PipelineActions>((set) => ({
  ...initialState,

  nextStep: () =>
    set((state) => ({
      currentStep: Math.min(state.currentStep + 1, 3),
    })),

  prevStep: () =>
    set((state) => ({
      currentStep: Math.max(state.currentStep - 1, 0),
    })),

  goToStep: (step: number) =>
    set(() => ({
      currentStep: Math.max(0, Math.min(step, 3)),
    })),

  setInputImage: (path: string | null) =>
    set(() => ({
      inputImage: path,
    })),

  setInputPrompt: (prompt: string) =>
    set(() => ({
      inputPrompt: prompt,
    })),

  setGeneratedModel: (model: GeneratedModel | null) =>
    set(() => ({
      generatedModel: model,
    })),

  setRiggedModel: (model: RiggedModel | null) =>
    set(() => ({
      riggedModel: model,
    })),

  setAnimatedModel: (model: AnimatedModel | null) =>
    set(() => ({
      animatedModel: model,
    })),

  setAnimationPrompt: (prompt: string) =>
    set(() => ({
      animationPrompt: prompt,
    })),

  setAnimationDuration: (duration: number) =>
    set(() => ({
      animationDuration: duration,
    })),

  setExportFormat: (format: ExportFormat) =>
    set(() => ({
      exportFormat: format,
    })),

  setExportPath: (path: string | null) =>
    set(() => ({
      exportPath: path,
    })),

  setIsProcessing: (processing: boolean) =>
    set(() => ({
      isProcessing: processing,
    })),

  reset: () => set(() => initialState),
}));
