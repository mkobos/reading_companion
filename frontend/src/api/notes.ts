import { request } from "./client";
import type { components } from "./types";

type Note = components["schemas"]["Note"];
type Passage = components["schemas"]["Passage"];

export function listNotes(workspaceId: string): Promise<Note[]> {
  return request<Note[]>(`/workspaces/${encodeURIComponent(workspaceId)}/notes`);
}

export function createNote(workspaceId: string, body: { anchor: Passage; text: string }): Promise<Note> {
  return request<Note>(`/workspaces/${encodeURIComponent(workspaceId)}/notes`, {
    method: "POST",
    json: body,
  });
}

export function updateNote(workspaceId: string, noteId: string, body: { text: string }): Promise<Note> {
  return request<Note>(`/workspaces/${encodeURIComponent(workspaceId)}/notes/${encodeURIComponent(noteId)}`, {
    method: "PUT",
    json: body,
  });
}

export function deleteNote(workspaceId: string, noteId: string): Promise<void> {
  return request<void>(`/workspaces/${encodeURIComponent(workspaceId)}/notes/${encodeURIComponent(noteId)}`, {
    method: "DELETE",
  });
}
