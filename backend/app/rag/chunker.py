from functools import lru_cache
from typing import Literal

from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
    TextSplitter,
)

_CHUNKERS_NAME = Literal["semantic", "recursive", "markdown"]


class ChunkerService:
    def __init__(self):
        self._chunkers: dict[_CHUNKERS_NAME, TextSplitter] = {
            "semantic": SentenceTransformersTokenTextSplitter,
            "recursive": RecursiveCharacterTextSplitter(
                chunk_size=1021,
                chunk_overlap=10,
            ),
            "markdown": MarkdownTextSplitter,
        }

    def get(self, chunker_name: _CHUNKERS_NAME, **kwargs) -> TextSplitter:
        chunker = self._chunkers.get(chunker_name)
        if chunker is None:
            raise ValueError("Chunker is not available")
        return chunker(**kwargs)


@lru_cache
def get_chunker() -> ChunkerService:
    return ChunkerService()
