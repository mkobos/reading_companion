import { request } from "./client";
import type { components } from "./types";

type Workspace = components["schemas"]["Workspace"];
type WorkspaceDetail = components["schemas"]["WorkspaceDetail"];

export function createWorkspace(): Promise<Workspace> {
  return request<Workspace>("/workspaces", { method: "POST" });
}

export function getWorkspace(workspaceId: string): Promise<WorkspaceDetail> {
  return request<WorkspaceDetail>(`/workspaces/${encodeURIComponent(workspaceId)}`);
}

export function deleteWorkspace(workspaceId: string): Promise<void> {
  return request<void>(`/workspaces/${encodeURIComponent(workspaceId)}`, { method: "DELETE" });
}
