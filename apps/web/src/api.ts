export interface HealthResponse {
  status: 'ok';
  service: 'ghosttab-api';
  version: string;
}

export async function getHealth(signal: AbortSignal): Promise<HealthResponse> {
  const response = await fetch('/api/health', { signal });
  if (!response.ok) throw new Error(`API returned ${response.status}`);
  const data: unknown = await response.json();
  if (
    typeof data !== 'object' || data === null ||
    !('status' in data) || data.status !== 'ok' ||
    !('service' in data) || data.service !== 'ghosttab-api' ||
    !('version' in data) || typeof data.version !== 'string'
  ) throw new Error('Unexpected API health response');
  return data as HealthResponse;
}
