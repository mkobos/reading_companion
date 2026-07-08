import { request } from "./client";
import type { components } from "./types";

type DocumentView = components["schemas"]["DocumentView"];

export function getDocument(workspaceId: string): Promise<DocumentView> {
  return request<DocumentView>(`/workspaces/${encodeURIComponent(workspaceId)}/document`);
}

export function uploadDocument(workspaceId: string, file: File): Promise<DocumentView> {
  const formData = new FormData();
  formData.append("file", file);
  return request<DocumentView>(`/workspaces/${encodeURIComponent(workspaceId)}/document`, {
    method: "POST",
    body: formData,
  });
}
