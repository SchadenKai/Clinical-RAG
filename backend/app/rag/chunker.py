from typing import Literal

from docling.chunking import HierarchicalChunker, HybridChunker
from docling_core.transforms.chunker.base import BaseChunker

_CHUNKERS_NAME = Literal["hybrid", "hierarchical"]


class ChunkerService:
    def __init__(self):
        self._chunkers: dict[str, type[BaseChunker]] = {
            "hybrid": HybridChunker,
            "hierarchical": HierarchicalChunker,
        }

    def get(self, chunker_name: _CHUNKERS_NAME, **kwargs) -> BaseChunker:
        chunker_cls = self._chunkers.get(chunker_name)
        if chunker_cls is None:
            raise ValueError(f"Chunker '{chunker_name}' is not available")
        return chunker_cls(**kwargs)
