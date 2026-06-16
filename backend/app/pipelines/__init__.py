"""Standalone data pipelines.

Each pipeline is an independent orchestration unit:

* ``indexing``   — ingest source documents into the vector store.
* ``sdg``        — generate synthetic evaluation goldens with deepeval.
* ``evaluation`` — score the RAG agent against the golden dataset.

Pipelines communicate only through stored artifacts (the vector database and
the golden-dataset JSON), never by importing or invoking one another. This
keeps each pipeline independently runnable, testable, and schedulable.
"""
