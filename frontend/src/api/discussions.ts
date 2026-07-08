import { request } from "./client";
import type { components } from "./types";

type Discussion = components["schemas"]["Discussion"];
type DiscussionSummary = components["schemas"]["DiscussionSummary"];
type Turn = components["schemas"]["Turn"];
type Viewport = components["schemas"]["Viewport"];
type Passage = components["schemas"]["Passage"];

export function listDiscussions(workspaceId: string): Promise<DiscussionSummary[]> {
  return request<DiscussionSummary[]>(`/workspaces/${encodeURIComponent(workspaceId)}/discussions`);
}

export function getDiscussion(workspaceId: string, discussionId: string): Promise<Discussion> {
  return request<Discussion>(
    `/workspaces/${encodeURIComponent(workspaceId)}/discussions/${encodeURIComponent(discussionId)}`,
  );
}

export function createDiscussion(
  workspaceId: string,
  body: { message: string; viewport: Viewport; anchor?: Passage },
): Promise<Discussion> {
  return request<Discussion>(`/workspaces/${encodeURIComponent(workspaceId)}/discussions`, {
    method: "POST",
    json: body,
  });
}

export function postTurn(
  workspaceId: string,
  discussionId: string,
  body: { message: string; viewport: Viewport },
): Promise<Turn> {
  return request<Turn>(
    `/workspaces/${encodeURIComponent(workspaceId)}/discussions/${encodeURIComponent(discussionId)}/turns`,
    { method: "POST", json: body },
  );
}
