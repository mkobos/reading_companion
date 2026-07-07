"""Viewport block-range resolution, per spec/features/reading-view.feature's
"the backend resolves the viewport text from those block IDs" and
spec/contracts/agent-contract.yaml's viewport_text shared type: concatenated
visible-block text with inline `<block id="...">` XML-style markers.
"""

from dataclasses import dataclass

from app.parsing import Block


@dataclass(frozen=True)
class Viewport:
    first_block_id: str
    last_block_id: str


class ViewportValidationError(Exception):
    pass


def resolve_viewport_text(blocks: list[Block], first_block_id: str, last_block_id: str) -> str:
    """Raises ViewportValidationError on an unknown block ID or a viewport
    whose first block is not at or before its last block."""
    blocks_by_id = {b.block_id: b for b in blocks}
    if first_block_id not in blocks_by_id or last_block_id not in blocks_by_id:
        raise ViewportValidationError("Viewport references an unknown block.")
    if first_block_id > last_block_id:
        raise ViewportValidationError("Viewport's first block must not be after its last block.")

    ordered_ids = [b.block_id for b in blocks]
    first_index = ordered_ids.index(first_block_id)
    last_index = ordered_ids.index(last_block_id)
    spanned = blocks[first_index : last_index + 1]

    return "\n".join(f'<block id="{block.block_id}">{block.text}</block>' for block in spanned)
