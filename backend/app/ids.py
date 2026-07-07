import secrets

_ENTROPY_BYTES = 16  # 128 bits, per spec/contracts/data-model.yaml Workspace.workspace_id


def _generate_id() -> str:
    return secrets.token_urlsafe(_ENTROPY_BYTES)


def generate_workspace_id() -> str:
    """Cryptographically secure, URL-safe workspace capability token.

    Must never be predictable or sequential: it doubles as the sole access
    control for a workspace (spec/features/security.feature).
    """
    return _generate_id()


def generate_note_id() -> str:
    """Cryptographically secure, URL-safe note ID."""
    return _generate_id()
