import { request } from "./client";
import type { components } from "./types";

type Journal = components["schemas"]["Journal"];

export function getJournal(workspaceId: string): Promise<Journal> {
  return request<Journal>(`/workspaces/${encodeURIComponent(workspaceId)}/journal`);
}

export function generateJournal(workspaceId: string): Promise<Journal> {
  return request<Journal>(`/workspaces/${encodeURIComponent(workspaceId)}/journal`, { method: "POST" });
}
