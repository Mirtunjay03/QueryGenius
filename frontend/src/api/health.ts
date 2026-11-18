export interface HealthStatus {
  status: string;
}

export async function fetchLiveness(): Promise<HealthStatus> {
  const response = await fetch("/health/live", {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`API health check failed (${response.status}).`);
  }
  return (await response.json()) as HealthStatus;
}
