from typing import Literal

from langchain_text_splitters import (
    CharacterTextSplitter,
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
    SpacyTextSplitter,
    TextSplitter,
)

_CHUNKERS_NAME = Literal["semantic", "recursive", "markdown"]


class ChunkerService:
    def __init__(self):
        self._chunkers: dict[_CHUNKERS_NAME, TextSplitter] = {
            "semantic": SpacyTextSplitter,
            "recursive": RecursiveCharacterTextSplitter,
            "character_based": CharacterTextSplitter,
            "markdown": MarkdownTextSplitter,
        }

    def get(self, chunker_name: _CHUNKERS_NAME, **kwargs) -> TextSplitter:
        chunker = self._chunkers.get(chunker_name)
        if chunker is None:
            raise ValueError("Chunker is not available")
        return chunker(**kwargs)
