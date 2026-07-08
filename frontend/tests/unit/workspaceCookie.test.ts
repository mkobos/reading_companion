import { afterEach, describe, expect, it } from "vitest";
import {
  clearLastWorkspace,
  getLastWorkspace,
  setLastWorkspace,
} from "../../src/workspace/workspaceCookie";

const COOKIE_NAME = "rc_last_workspace";

function clearAllCookies() {
  document.cookie.split(";").forEach((c) => {
    const name = c.split("=")[0]?.trim();
    if (name) document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
  });
}

describe("workspaceCookie", () => {
  afterEach(() => clearAllCookies());

  it("returns undefined when no cookie is set", () => {
    expect(getLastWorkspace()).toBeUndefined();
  });

  it("round-trips a workspace id through set/get", () => {
    setLastWorkspace("abc123");
    expect(getLastWorkspace()).toBe("abc123");
  });

  it("writes the cookie under the rc_last_workspace name with SameSite=Lax and Path=/", () => {
    setLastWorkspace("abc123");
    expect(document.cookie).toContain(`${COOKIE_NAME}=abc123`);
  });

  it("clears the cookie", () => {
    setLastWorkspace("abc123");
    clearLastWorkspace();
    expect(getLastWorkspace()).toBeUndefined();
  });
});
