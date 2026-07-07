import pytest

from app.parsing import Block
from app.viewport import ViewportValidationError, resolve_viewport_text

_BLOCKS = [
    Block(block_id="000000", type="paragraph", text="First block text."),
    Block(block_id="000001", type="paragraph", text="Second block text."),
    Block(block_id="000002", type="paragraph", text="Third block text."),
]


def test_single_block_viewport_wraps_one_marker():
    text = resolve_viewport_text(_BLOCKS, "000000", "000000")

    assert text == '<block id="000000">First block text.</block>'


def test_multi_block_viewport_wraps_each_block():
    text = resolve_viewport_text(_BLOCKS, "000000", "000001")

    assert text == (
        '<block id="000000">First block text.</block>\n'
        '<block id="000001">Second block text.</block>'
    )


def test_unknown_first_block_id_is_rejected():
    with pytest.raises(ViewportValidationError):
        resolve_viewport_text(_BLOCKS, "999999", "000001")


def test_unknown_last_block_id_is_rejected():
    with pytest.raises(ViewportValidationError):
        resolve_viewport_text(_BLOCKS, "000000", "999999")


def test_first_after_last_is_rejected():
    with pytest.raises(ViewportValidationError):
        resolve_viewport_text(_BLOCKS, "000001", "000000")
