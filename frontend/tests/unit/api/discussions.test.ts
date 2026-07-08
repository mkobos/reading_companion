import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { createDiscussion, getDiscussion, listDiscussions, postTurn } from "../../../src/api/discussions";
import { ApiError } from "../../../src/lib/errors";
import { server } from "../../msw/server";

const VIEWPORT = { first_block_id: "000000", last_block_id: "000001" };

describe("discussions API module", () => {
  it("listDiscussions issues a GET to the workspace's discussions collection", async () => {
    server.use(
      http.get("/api/workspaces/ws1/discussions", () =>
        HttpResponse.json([
          { discussion_id: "d1", created_at: "2026-01-01T00:00:00Z", turn_count: 1 },
        ]),
      ),
    );

    const result = await listDiscussions("ws1");
    expect(result).toHaveLength(1);
    expect(result[0]?.discussion_id).toBe("d1");
  });

  it("encodes the workspace id in listDiscussions", async () => {
    server.use(
      http.get("/api/workspaces/ws%201/discussions", () => HttpResponse.json([])),
    );
    await listDiscussions("ws 1");
  });

  it("getDiscussion issues a GET to the specific discussion and encodes both ids", async () => {
    server.use(
      http.get("/api/workspaces/ws%201/discussions/d%201", () =>
        HttpResponse.json({ discussion_id: "d 1", created_at: "2026-01-01T00:00:00Z", turns: [] }),
      ),
    );

    const result = await getDiscussion("ws 1", "d 1");
    expect(result.discussion_id).toBe("d 1");
  });

  it("createDiscussion POSTs a JSON body with message/viewport/anchor and returns the Discussion", async () => {
    server.use(
      http.post("/api/workspaces/ws1/discussions", async ({ request: req }) => {
        expect(req.headers.get("content-type")).toContain("application/json");
        const body = await req.json();
        expect(body).toEqual({ message: "hello", viewport: VIEWPORT });
        return HttpResponse.json(
          { discussion_id: "d1", created_at: "2026-01-01T00:00:00Z", turns: [] },
          { status: 201 },
        );
      }),
    );

    const result = await createDiscussion("ws1", { message: "hello", viewport: VIEWPORT });
    expect(result.discussion_id).toBe("d1");
  });

  it("postTurn POSTs a JSON body with message/viewport and returns the bare Turn", async () => {
    server.use(
      http.post("/api/workspaces/ws1/discussions/d1/turns", async ({ request: req }) => {
        const body = await req.json();
        expect(body).toEqual({ message: "follow up", viewport: VIEWPORT });
        return HttpResponse.json(
          {
            turn_id: "t2",
            user_message: "follow up",
            agent_response: "reply",
            viewport: VIEWPORT,
            created_at: "2026-01-01T00:00:00Z",
          },
          { status: 201 },
        );
      }),
    );

    const result = await postTurn("ws1", "d1", { message: "follow up", viewport: VIEWPORT });
    expect(result.turn_id).toBe("t2");
  });

  it("maps a 502 response to an ApiError with the backend message", async () => {
    server.use(
      http.post("/api/workspaces/ws1/discussions", () =>
        HttpResponse.json({ message: "Agent turn failed; nothing was saved. Retry." }, { status: 502 }),
      ),
    );

    const err = await createDiscussion("ws1", { message: "hi", viewport: VIEWPORT }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(502);
    expect(err.message).toBe("Agent turn failed; nothing was saved. Retry.");
  });

  it("maps a 429 response to an ApiError with retryAfterSeconds from the Retry-After header", async () => {
    server.use(
      http.post("/api/workspaces/ws1/discussions/d1/turns", () =>
        HttpResponse.json({ message: "rate limited" }, { status: 429, headers: { "Retry-After": "12" } }),
      ),
    );

    const err = await postTurn("ws1", "d1", { message: "hi", viewport: VIEWPORT }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(429);
    expect(err.retryAfterSeconds).toBe(12);
  });

  it("propagates a network error as a plain non-ApiError rejection", async () => {
    server.use(http.post("/api/workspaces/ws1/discussions", () => HttpResponse.error()));

    const err = await createDiscussion("ws1", { message: "hi", viewport: VIEWPORT }).catch((e) => e);
    expect(err).not.toBeInstanceOf(ApiError);
  });
});
