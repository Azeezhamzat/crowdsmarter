import { apiRequest } from "../../lib/api";
import type { Workspace } from "../../lib/types";

export function listWorkspaces(organisationId: string): Promise<Workspace[]> {
  return apiRequest<Workspace[]>(`/organisations/${organisationId}/workspaces/`);
}

export function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiRequest<Workspace>(`/workspaces/${workspaceId}/`);
}

export function createWorkspace(
  organisationId: string,
  input: { name: string; slug: string; description: string },
): Promise<Workspace> {
  return apiRequest<Workspace>(`/organisations/${organisationId}/workspaces/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateWorkspace(
  workspaceId: string,
  input: { name: string; description: string },
): Promise<Workspace> {
  return apiRequest<Workspace>(`/workspaces/${workspaceId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
