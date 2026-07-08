import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createDiscussion, getDiscussion, listDiscussions, postTurn } from "./discussions";
import { getDocument, uploadDocument } from "./documents";
import { createNote, deleteNote, listNotes, updateNote } from "./notes";
import type { components } from "./types";
import { createWorkspace, deleteWorkspace, getWorkspace } from "./workspaces";

type Discussion = components["schemas"]["Discussion"];
type Viewport = components["schemas"]["Viewport"];
type Passage = components["schemas"]["Passage"];
type Note = components["schemas"]["Note"];

// Mutations never auto-retry (Phase 1 plan §6.6: no retry-storm on 429 or
// any other failure). Reads use TanStack Query's default retry behavior.
const NO_RETRY = { retry: false as const };

export function useWorkspace(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => getWorkspace(workspaceId as string),
    enabled: workspaceId !== undefined,
  });
}

export function useDocument(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ["document", workspaceId],
    queryFn: () => getDocument(workspaceId as string),
    enabled: workspaceId !== undefined,
  });
}

export function useCreateWorkspace() {
  return useMutation({
    mutationFn: createWorkspace,
    ...NO_RETRY,
  });
}

export function useUploadDocument(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadDocument(workspaceId, file),
    ...NO_RETRY,
    onSuccess: (document) => {
      queryClient.setQueryData(["document", workspaceId], document);
      queryClient.invalidateQueries({ queryKey: ["workspace", workspaceId] });
    },
  });
}

export function useDeleteWorkspace() {
  return useMutation({
    mutationFn: (workspaceId: string) => deleteWorkspace(workspaceId),
    ...NO_RETRY,
  });
}

export function useDiscussions(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ["discussions", workspaceId],
    queryFn: () => listDiscussions(workspaceId as string),
    enabled: workspaceId !== undefined,
  });
}

export function useDiscussion(workspaceId: string | undefined, discussionId: string | undefined) {
  return useQuery({
    queryKey: ["discussion", workspaceId, discussionId],
    queryFn: () => getDiscussion(workspaceId as string, discussionId as string),
    enabled: workspaceId !== undefined && discussionId !== undefined,
  });
}

export function useCreateDiscussion(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { message: string; viewport: Viewport; anchor?: Passage }) =>
      createDiscussion(workspaceId, body),
    ...NO_RETRY,
    onSuccess: (discussion) => {
      queryClient.setQueryData(["discussion", workspaceId, discussion.discussion_id], discussion);
      queryClient.invalidateQueries({ queryKey: ["discussions", workspaceId] });
    },
  });
}

export function useNotes(workspaceId: string | undefined) {
  return useQuery({
    queryKey: ["notes", workspaceId],
    queryFn: () => listNotes(workspaceId as string),
    enabled: workspaceId !== undefined,
  });
}

export function useCreateNote(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { anchor: Passage; text: string }) => createNote(workspaceId, body),
    ...NO_RETRY,
    onSuccess: (note) => {
      queryClient.setQueryData(["notes", workspaceId], (prev: Note[] | undefined) =>
        prev ? [...prev, note] : [note],
      );
    },
  });
}

export function useUpdateNote(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { noteId: string; text: string }) => updateNote(workspaceId, body.noteId, { text: body.text }),
    ...NO_RETRY,
    onSuccess: (note) => {
      queryClient.setQueryData(["notes", workspaceId], (prev: Note[] | undefined) =>
        prev ? prev.map((n) => (n.note_id === note.note_id ? note : n)) : prev,
      );
    },
  });
}

export function useDeleteNote(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (noteId: string) => deleteNote(workspaceId, noteId),
    ...NO_RETRY,
    onSuccess: (_data, noteId) => {
      queryClient.setQueryData(["notes", workspaceId], (prev: Note[] | undefined) =>
        prev ? prev.filter((n) => n.note_id !== noteId) : prev,
      );
    },
  });
}

export function usePostTurn(workspaceId: string, discussionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { message: string; viewport: Viewport }) => postTurn(workspaceId, discussionId, body),
    ...NO_RETRY,
    onSuccess: (turn) => {
      queryClient.setQueryData(["discussion", workspaceId, discussionId], (prev: Discussion | undefined) =>
        prev ? { ...prev, turns: [...prev.turns, turn] } : prev,
      );
      queryClient.invalidateQueries({ queryKey: ["discussions", workspaceId] });
    },
  });
}
