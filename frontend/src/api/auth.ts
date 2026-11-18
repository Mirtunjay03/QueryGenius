export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  role: string;
}

export interface Workspace {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
}

async function authRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the status-based fallback.
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function register(payload: {
  email: string;
  password: string;
  display_name: string;
  organization_name: string;
}) {
  return authRequest<TokenResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(payload: { email: string; password: string }) {
  return authRequest<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMe(accessToken: string) {
  return authRequest<User>("/api/v1/auth/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function listOrganizations(accessToken: string) {
  return authRequest<Organization[]>("/api/v1/organizations", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function listWorkspaces(accessToken: string, organizationId: string) {
  return authRequest<Workspace[]>(`/api/v1/organizations/${organizationId}/workspaces`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function createWorkspace(
  accessToken: string,
  organizationId: string,
  payload: { name: string; slug: string },
) {
  return authRequest<Workspace>(`/api/v1/organizations/${organizationId}/workspaces`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(payload),
  });
}

