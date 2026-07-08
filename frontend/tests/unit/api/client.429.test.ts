import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { request } from "../../../src/api/client";
import { ApiError } from "../../../src/lib/errors";
import { server } from "../../msw/server";

describe("api client request()", () => {
  it("returns parsed JSON on a 2xx response", async () => {
    server.use(
      http.get("/api/workspaces/abc", () =>
        HttpResponse.json({ workspace_id: "abc", created_at: "2026-01-01T00:00:00Z" }),
      ),
    );

    const result = await request<{ workspace_id: string }>("/workspaces/abc");
    expect(result.workspace_id).toBe("abc");
  });

  it("sends a JSON body and content-type header for json option", async () => {
    server.use(
      http.post("/api/workspaces", async ({ request: req }) => {
        expect(req.headers.get("content-type")).toContain("application/json");
        expect(await req.json()).toEqual({ hello: "world" });
        return HttpResponse.json({ ok: true }, { status: 201 });
      }),
    );

    await request("/workspaces", { method: "POST", json: { hello: "world" } });
  });

  it("returns undefined for a 204 No Content response", async () => {
    server.use(http.delete("/api/workspaces/abc", () => new HttpResponse(null, { status: 204 })));
    const result = await request("/workspaces/abc", { method: "DELETE" });
    expect(result).toBeUndefined();
  });

  it("throws ApiError with status and message parsed from the Error body", async () => {
    server.use(
      http.get("/api/workspaces/missing", () =>
        HttpResponse.json({ message: "workspace not found" }, { status: 404 }),
      ),
    );

    const err = await request("/workspaces/missing").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(404);
    expect(err.message).toBe("workspace not found");
  });

  it("parses Retry-After header into retryAfterSeconds on 429 and never retries automatically", async () => {
    let callCount = 0;
    server.use(
      http.post("/api/workspaces", () => {
        callCount += 1;
        return HttpResponse.json(
          { message: "rate limited" },
          { status: 429, headers: { "Retry-After": "30" } },
        );
      }),
    );

    const err = await request("/workspaces", { method: "POST" }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(429);
    expect(err.retryAfterSeconds).toBe(30);
    // Uniform 429 handling, no retry-storm (plan §6.6): the transport layer
    // issues exactly one request and never retries on its own.
    expect(callCount).toBe(1);
  });

  it("never retries automatically on any failure (500)", async () => {
    let callCount = 0;
    server.use(
      http.get("/api/workspaces/flaky", () => {
        callCount += 1;
        return HttpResponse.json({ message: "boom" }, { status: 500 });
      }),
    );

    await request("/workspaces/flaky").catch(() => undefined);
    expect(callCount).toBe(1);
  });
});
