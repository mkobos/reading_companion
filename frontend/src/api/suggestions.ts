import { request } from "./client";
import type { components } from "./types";

type Passage = components["schemas"]["Passage"];
type Viewport = components["schemas"]["Viewport"];

export function createSuggestions(
  workspaceId: string,
  body: { anchor: Passage; viewport: Viewport },
): Promise<{ suggestions: string[] }> {
  return request<{ suggestions: string[] }>(`/workspaces/${encodeURIComponent(workspaceId)}/suggestions`, {
    method: "POST",
    json: body,
  });
}
