"""Passage anchor validation, per spec/contracts/data-model.yaml's Passage
schema: "an anchor referencing an unknown block ID, with an offset beyond
the block's length, with first after last, or whose text does not match
the anchored range is rejected (HTTP 400); nothing is stored."

Multi-block join convention (resolved spec gap, see
docs/repo_configuration_progress.md): block texts are joined with "\n"
when reconstructing the anchored range for the text self-check.
"""

from dataclasses import dataclass

from app.parsing import Block

_JOIN = "\n"


@dataclass(frozen=True)
class Passage:
    first_block_id: str
    first_block_offset: int
    last_block_id: str
    last_block_offset: int
    text: str


class PassageValidationError(Exception):
    pass


def validate_passage(passage: Passage, blocks: list[Block]) -> None:
    blocks_by_id = {b.block_id: b for b in blocks}
    first_block = blocks_by_id.get(passage.first_block_id)
    last_block = blocks_by_id.get(passage.last_block_id)
    if first_block is None or last_block is None:
        raise PassageValidationError("Passage anchor references an unknown block.")

    if passage.first_block_offset < 0 or passage.first_block_offset > len(first_block.text):
        raise PassageValidationError("Passage anchor offset is beyond the block's length.")
    if passage.last_block_offset < 0 or passage.last_block_offset > len(last_block.text):
        raise PassageValidationError("Passage anchor offset is beyond the block's length.")

    if passage.first_block_id == passage.last_block_id:
        if passage.first_block_offset >= passage.last_block_offset:
            raise PassageValidationError(
                "Passage anchor's first offset must be before its last offset."
            )
    elif passage.first_block_id > passage.last_block_id:
        raise PassageValidationError("Passage anchor's first block must not be after its last block.")

    reconstructed = _reconstruct_text(passage, blocks)
    if reconstructed != passage.text:
        raise PassageValidationError("Passage text does not match the anchored range.")


def _reconstruct_text(passage: Passage, blocks: list[Block]) -> str:
    ordered_ids = [b.block_id for b in blocks]
    first_index = ordered_ids.index(passage.first_block_id)
    last_index = ordered_ids.index(passage.last_block_id)
    spanned = blocks[first_index : last_index + 1]

    if len(spanned) == 1:
        block = spanned[0]
        return block.text[passage.first_block_offset : passage.last_block_offset]

    pieces = [spanned[0].text[passage.first_block_offset :]]
    pieces.extend(block.text for block in spanned[1:-1])
    pieces.append(spanned[-1].text[: passage.last_block_offset])
    return _JOIN.join(pieces)
