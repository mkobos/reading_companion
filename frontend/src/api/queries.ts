import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDocument, uploadDocument } from "./documents";
import { createWorkspace, deleteWorkspace, getWorkspace } from "./workspaces";

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
