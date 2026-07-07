import pytest

from app.parsing import Block
from app.passages import Passage, PassageValidationError, validate_passage

_BLOCKS = [
    Block(block_id="000000", type="paragraph", text="First block text."),
    Block(block_id="000001", type="paragraph", text="Second block text."),
    Block(block_id="000002", type="paragraph", text="Third block text."),
]


def test_valid_single_block_passage_passes():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=6,
        last_block_id="000000",
        last_block_offset=11,
        text="block",
    )

    validate_passage(passage, _BLOCKS)  # does not raise


def test_valid_multi_block_passage_joins_with_newline():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=6,
        last_block_id="000001",
        last_block_offset=6,
        text="block text.\nSecond",
    )

    validate_passage(passage, _BLOCKS)  # does not raise


def test_unknown_first_block_id_is_rejected():
    passage = Passage(
        first_block_id="999999",
        first_block_offset=0,
        last_block_id="000000",
        last_block_offset=5,
        text="First",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, _BLOCKS)


def test_unknown_last_block_id_is_rejected():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=0,
        last_block_id="999999",
        last_block_offset=5,
        text="First",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, _BLOCKS)


def test_offset_beyond_block_length_is_rejected():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=0,
        last_block_id="000000",
        last_block_offset=999,
        text="First block text.",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, _BLOCKS)


def test_first_after_last_block_is_rejected():
    passage = Passage(
        first_block_id="000001",
        first_block_offset=0,
        last_block_id="000000",
        last_block_offset=5,
        text="First",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, _BLOCKS)


def test_first_offset_not_before_last_offset_in_same_block_is_rejected():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=10,
        last_block_id="000000",
        last_block_offset=10,
        text="",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, _BLOCKS)


def test_text_mismatch_is_rejected():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=6,
        last_block_id="000000",
        last_block_offset=11,
        text="wrong",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, _BLOCKS)


def test_workspace_with_no_document_rejects_any_anchor():
    passage = Passage(
        first_block_id="000000",
        first_block_offset=0,
        last_block_id="000000",
        last_block_offset=5,
        text="First",
    )

    with pytest.raises(PassageValidationError):
        validate_passage(passage, [])
