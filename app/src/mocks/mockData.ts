import type { GeneratedModel, RiggedModel, AnimatedModel } from '../types/pipeline';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function mockGenerateModel(): Promise<GeneratedModel> {
  await delay(2000);
  return {
    id: `gen-${Date.now()}`,
    format: 'glb',
    path: '/mock/generated-model.glb',
    metadata: {
      vertices: 12500,
    },
  };
}

export async function mockRigModel(): Promise<RiggedModel> {
  await delay(1500);
  return {
    id: `rig-${Date.now()}`,
    format: 'glb',
    path: '/mock/rigged-model.glb',
    metadata: {
      vertices: 12500,
      bones: 24,
    },
  };
}

export async function mockAnimateModel(duration: number): Promise<AnimatedModel> {
  await delay(3000);
  return {
    id: `anim-${Date.now()}`,
    format: 'glb',
    path: '/mock/animated-model.glb',
    metadata: {
      vertices: 12500,
      bones: 24,
      fps: 30,
      duration,
    },
  };
}

export async function mockExportModel(_format: 'fbx' | 'glb', path: string): Promise<string> {
  await delay(1000);
  return path;
}
