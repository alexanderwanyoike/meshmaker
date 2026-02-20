import { readFile, writeFile } from '@tauri-apps/plugin-fs';
import { runJob, type JobStatus } from './runpod';
import { uint8ArrayToBase64, base64ToUint8Array } from '../utils/encoding';
import type { RunPodConfig, GeneratedModel, RiggedModel, AnimatedModel } from '../types/pipeline';

const HYMOTION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes — large model, slow cold start

function statusToMessage(status: JobStatus): string {
  switch (status) {
    case 'IN_QUEUE':
      return 'Waiting for GPU...';
    case 'IN_PROGRESS':
      return 'Processing...';
    default:
      return status;
  }
}

export async function generate3D(
  config: RunPodConfig,
  imagePath: string,
  onStatus: (msg: string) => void,
): Promise<GeneratedModel> {
  onStatus('Reading image...');
  const imageBytes = await readFile(imagePath);
  const imageBase64 = uint8ArrayToBase64(imageBytes);

  onStatus('Submitting to Trellis...');
  const output = await runJob(
    config.apiKey,
    config.trellisEndpointId,
    { image: imageBase64, resolution: 512, texture_size: 2048 },
    (status) => onStatus(statusToMessage(status)),
  ) as { glb: string; metadata: Record<string, unknown> };

  if (!output?.glb) {
    throw new Error('Trellis returned no GLB data');
  }

  return {
    id: `gen-${Date.now()}`,
    format: 'glb',
    data: output.glb,
    metadata: {
      seed: output.metadata?.seed as number | undefined,
      generationTime: output.metadata?.total_time as number | undefined,
    },
  };
}

export async function rigModel(
  config: RunPodConfig,
  generatedModel: GeneratedModel,
  onStatus: (msg: string) => void,
): Promise<RiggedModel> {
  onStatus('Submitting to UniRig...');
  const output = await runJob(
    config.apiKey,
    config.unirirEndpointId,
    { mesh: generatedModel.data, format: 'fbx', seed: 12345 },
    (status) => onStatus(statusToMessage(status)),
  ) as { output: string; processing_time: number };

  if (!output?.output) {
    throw new Error('UniRig returned no FBX data');
  }

  return {
    id: `rig-${Date.now()}`,
    format: 'fbx',
    data: output.output,
    metadata: {
      generationTime: output.processing_time,
    },
  };
}

export async function animateModel(
  config: RunPodConfig,
  riggedModel: RiggedModel,
  prompt: string,
  duration: number,
  onStatus: (msg: string) => void,
): Promise<AnimatedModel> {
  onStatus('Submitting to HyMotion...');
  const output = await runJob(
    config.apiKey,
    config.hymotionEndpointId,
    {
      prompt,
      duration,
      fps: 30,
      character_fbx: riggedModel.data,
    },
    (status) => onStatus(statusToMessage(status)),
    HYMOTION_TIMEOUT_MS,
  ) as { animated_fbx: string; metadata: Record<string, unknown> };

  if (!output?.animated_fbx) {
    throw new Error('HyMotion returned no animated FBX data');
  }

  return {
    id: `anim-${Date.now()}`,
    format: 'fbx',
    data: output.animated_fbx,
    metadata: {
      fps: 30,
      duration,
      seed: output.metadata?.seed as number | undefined,
      generationTime: output.metadata?.generation_time as number | undefined,
    },
  };
}

export async function exportModel(
  animatedModel: AnimatedModel,
  exportPath: string,
): Promise<void> {
  const bytes = base64ToUint8Array(animatedModel.data);
  await writeFile(exportPath, bytes);
}
