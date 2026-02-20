const RUNPOD_BASE = 'https://api.runpod.io/v2';

const POLL_INTERVAL_MS = 3000;
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

export type JobStatus = 'IN_QUEUE' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'TIMED_OUT';

interface JobStatusResponse {
  id: string;
  status: JobStatus;
  output?: unknown;
  error?: string;
}

async function submitJob(apiKey: string, endpointId: string, input: object): Promise<string> {
  const res = await fetch(`${RUNPOD_BASE}/${endpointId}/run`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ input }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`RunPod submit failed (${res.status}): ${text}`);
  }

  const data = await res.json() as { id: string };
  return data.id;
}

async function pollJob(
  apiKey: string,
  endpointId: string,
  jobId: string,
  onStatus: (status: JobStatus) => void,
  timeoutMs: number,
): Promise<unknown> {
  const deadline = Date.now() + timeoutMs;
  const timeoutMins = Math.round(timeoutMs / 60000);

  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));

    const res = await fetch(`${RUNPOD_BASE}/${endpointId}/status/${jobId}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`RunPod poll failed (${res.status}): ${text}`);
    }

    const data = await res.json() as JobStatusResponse;
    onStatus(data.status);

    if (data.status === 'COMPLETED') {
      return data.output;
    }
    if (data.status === 'FAILED' || data.status === 'CANCELLED') {
      throw new Error(`RunPod job ${data.status.toLowerCase()}: ${data.error ?? 'unknown error'}`);
    }
  }

  throw new Error(`RunPod job timed out after ${timeoutMins} minutes`);
}

export async function runJob(
  apiKey: string,
  endpointId: string,
  input: object,
  onStatus: (status: JobStatus) => void,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<unknown> {
  const jobId = await submitJob(apiKey, endpointId, input);
  return pollJob(apiKey, endpointId, jobId, onStatus, timeoutMs);
}
