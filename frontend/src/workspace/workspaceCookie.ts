/** Convenience pointer to the last-used workspace. Client-only: the backend
 * neither sets nor reads it, and it grants no access on its own (a
 * workspace's ID in the URL is what grants access). See Phase 1 plan §6.3. */
const COOKIE_NAME = "rc_last_workspace";

function readCookie(name: string): string | undefined {
  const match = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : undefined;
}

export function getLastWorkspace(): string | undefined {
  return readCookie(COOKIE_NAME);
}

export function setLastWorkspace(workspaceId: string): void {
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(workspaceId)}; SameSite=Lax; Path=/${secure}`;
}

export function clearLastWorkspace(): void {
  document.cookie = `${COOKIE_NAME}=; SameSite=Lax; Path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}
