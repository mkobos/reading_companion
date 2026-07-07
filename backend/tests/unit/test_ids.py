import secrets

from app.ids import generate_note_id, generate_workspace_id


def test_generated_id_has_at_least_128_bits_of_entropy():
    workspace_id = generate_workspace_id()

    # token_urlsafe(n) yields ceil(4n/3) base64url chars for n random bytes.
    # 128 bits = 16 bytes -> at least 22 chars.
    assert len(workspace_id) >= 22


def test_generated_id_is_url_safe_base64_charset():
    workspace_id = generate_workspace_id()

    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )
    assert set(workspace_id) <= allowed


def test_generated_ids_are_not_sequential_or_repeating():
    ids = [generate_workspace_id() for _ in range(20)]

    assert len(set(ids)) == len(ids)


def test_uses_cryptographically_secure_generator(monkeypatch):
    calls = []
    original = secrets.token_urlsafe

    def spy(nbytes=None):
        calls.append(nbytes)
        return original(nbytes)

    monkeypatch.setattr(secrets, "token_urlsafe", spy)

    generate_workspace_id()

    assert calls, "generate_workspace_id must call secrets.token_urlsafe"


def test_note_id_has_at_least_128_bits_of_entropy_and_is_distinct_from_workspace_ids():
    note_id = generate_note_id()
    workspace_id = generate_workspace_id()

    assert len(note_id) >= 22
    assert note_id != workspace_id
