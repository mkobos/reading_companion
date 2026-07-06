"""Loads `.env` before test collection.

`agents-cli eval generate`/`grade` and `app/fast_api_app.py` already call
`load_dotenv()` themselves, but plain `pytest` does not — without this, any
test that makes a real Vertex/AI-Studio call (see AGENTS.md's live-model
tests) fails with a misleading "No API key was provided" error instead of
picking up the project's real credentials.
"""

from dotenv import load_dotenv

load_dotenv()
