from typing import Optional, cast
from concurrent.futures import ThreadPoolExecutor
from docling.document_converter import DocumentConverter
from langchain_nebius import ChatNebius
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_text_splitters.sentence_transformers import (
    SentenceTransformersTokenTextSplitter,
)
from langchain_text_splitters.nltk import NLTKTextSplitter
from pydantic import BaseModel, Field
from app.core.config import settings
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, BaseMessage
from langchain_core.documents import Document

# document parsing
# chunking
# LLM translation + CoT + SO
# LLM as a judge
# feedback loop
# document builder


doc_converter = DocumentConverter()
results = doc_converter.convert(source="app/scripts/eng.md")
results = results.document.export_to_markdown()

text_splitter = NLTKTextSplitter()
text_splitter_2 = SentenceTransformersTokenTextSplitter()

chunks = text_splitter_2.split_text(results)

final_docs: list[Document] = []
for i, chunk in enumerate(chunks):
    final_docs.append(
        Document(
            page_content=chunk,
            metadata={
                "previous_chunk_id": i - 1 if i > 0 else 0,
                "current_chunk_id": i,
                "next_chunk_id": i + 1 if i + 1 < len(chunks) else i,
            },
        )
    )
print(f"Size of chunks {len(chunks)}")

TRANSLATION_PROMPT = """
# Role
You are an expert Context-Aware Translator Agent. Your goal is to translate a specific segment of text (the "Target Chunk") into a specified target language while preserving the semantic flow, tone, and terminology established by the surrounding context.

# Input Data Structure
You will be provided with three specific blocks of text:
1. <previous_context>: The text immediately preceding the target chunk.
2. <target_chunk>: The specific text you must translate.
3. <next_context>: The text immediately following the target chunk.

# Strict Instructions
1. **Translate ONLY the <target_chunk>**: Do not translate the previous or next context. They are provided solely for your reference to understand the narrative flow.
2. **Contextual Continuity**:
   - Use <previous_context> to determine correct pronoun references (e.g., identifying if "it" refers to a server or a person) and to maintain consistent terminology.
   - Use <next_context> to ensure your translation leads naturally into the next segment (e.g., avoiding sentence structures that would make the start of the next chunk grammatically awkward).
3. **Formatting**: Preserve all Markdown formatting, HTML tags, or code blocks exactly as they appear in the original text.
4. **Tone**: Match the tone of the source text (e.g., formal, technical, casual).
"""

HUMAN_INPUT_TEMPLATE = """
Target chunk: {target_chunk}
Previous Chunk(optional): {previous_chunk}
Next Chunk(optional): {next_chunk}

Current Language: {current_language}
Target Language: {target_language}
"""


class TranslatedChunk(BaseModel):
    translation: str = Field(description="The translation of the target chunk")
    confidence_score: float = Field(
        description="Score from 0.0 to 1.0 on how confident you are in your translation"
    )
    reasoning: str = Field(description="Reasoning for the confidence score value given")


final_translation = ""


def translation(
    client: BaseChatModel,
    messages: list[BaseMessage],
    is_confident: Optional[bool] = False,
) -> str:
    client = client.with_structured_output(schema=TranslatedChunk, strict=True)
    while not is_confident:
        print(is_confident)
        results = client.invoke(input=messages)
        results = cast(TranslatedChunk, results)
        print(results)
        if results.confidence_score < 0.7:
            print(
                f"[DEBUG] Confidence score too low ({results.confidence_score})"
                f": Retrying... (reason:{results.reasoning})"
            )
            messages.append(AIMessage(content=(results)))
            messages.append(HumanMessage(content="Retry based on the given reasoning"))
            is_confident = False
        else:
            print(f"[DEBUG] Passed ({results.confidence_score})")
            is_confident = True
    return results.translation


messages_list: list[list[BaseMessage]] = []
client_list: list[BaseChatModel] = []

for _, doc in enumerate(final_docs):
    client = ChatNebius(
        model="meta-llama/Llama-3.3-70B-Instruct-fast", api_key=settings.llm_api_key
    )

    messages = [
        SystemMessage(content=TRANSLATION_PROMPT),
        HumanMessage(
            content=HUMAN_INPUT_TEMPLATE.format(
                target_chunk=doc.page_content,
                current_language="english",
                target_language="filipino",
                previous_chunk=final_docs[doc.metadata["previous_chunk_id"]]
                if doc.metadata["previous_chunk_id"] != doc.metadata["current_chunk_id"]
                else "",
                next_chunk=final_docs[doc.metadata["next_chunk_id"]]
                if doc.metadata["next_chunk_id"] != doc.metadata["current_chunk_id"]
                else "",
            )
        ),
    ]

    client_list.append(client)
    messages_list.append(messages)

final_translation = ""
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(translation, client_list, messages_list)

    for result in results:
        final_translation += result

print(final_translation)

with open("filipino.md", mode="w") as file:
    file.write(final_translation)
