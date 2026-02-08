from concurrent.futures import ThreadPoolExecutor
from typing import cast

from deepeval import evaluate
from deepeval.evaluate.types import EvaluationResult
from deepeval.metrics import GEval
from deepeval.metrics.g_eval import Rubric
from deepeval.models import GPTModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from docling.document_converter import DocumentConverter
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_nebius import ChatNebius
from langchain_text_splitters.character import RecursiveCharacterTextSplitter

# from langchain_text_splitters.nltk import NLTKTextSplitter
# from langchain_text_splitters.sentence_transformers import (
#     SentenceTransformersTokenTextSplitter,
# )
# from langchain_text_splitters.spacy import SpacyTextSplitter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.llm.calculate_cost import get_pricing_info

doc_converter = DocumentConverter()
results = doc_converter.convert(source="app/scripts/eng.md")
results = results.document.export_to_markdown()

# text_splitter = NLTKTextSplitter()
# text_splitter_2 = SentenceTransformersTokenTextSplitter()
text_splitter_3 = RecursiveCharacterTextSplitter(
    chunk_size=2000,  # Large enough for full context
    chunk_overlap=200,  # Critical for translation to carry over context
    separators=["\n\n", "\n", ". ", " ", ""],  # Priority list
    length_function=len,
)
# text_splitter_4 = SpacyTextSplitter()

# chunks = text_splitter_3.split_text(results)

chunks = results.split("\n\n")

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
You are a Professional Native-Level Translator and Linguist specializing in the
target language. Your goal is to translate a specific text segment (the "Target
Chunk") while maintaining perfect grammatical continuity with the surrounding
context.

# Task
Translate the <target_chunk> into the specified target language.

# Input Data
1. <previous_context>: Text preceding the chunk (Read-only: Use for gender/number/tone).
2. <target_chunk>: The text to translate.
3. <next_context>: Text following the chunk (Read-only: Use for syntactic flow).

# Critical Guidelines
1. **Semantic Intent over Literalism**: Do not translate word-for-word.
    - Example: If the source says "hits" (mafia assassinations), do not
      translate as "search results" or "sports goals." Use the
      context-appropriate term (e.g., "Anschläge").
    - Example: If the source says "defeated" (won against), do not translate
      as "added to."
2. **Handle Fragmentation**: The <target_chunk> may start or end in the middle
   of a sentence. Your translation MUST grammatically bridge
   <previous_context> and <next_context>.
    - If <previous_context> ends with an adjective, your chunk must start with
      the modified noun (if applicable in target grammar).
3. **No "Glitching"**:
    - Do NOT repeat the source text in the output.
    - Do NOT switch to lowercase unexpectedly.
    - Do NOT leave English words untranslated unless they are proper nouns or
      standard technical loanwords.
4. **Completeness**: Ensure every concept in <target_chunk> is represented. Do
   not summarize or omit details.

# Chain of Thought (Internal Monologue)
Before outputting the translation, perform this check:
1. **Polysemy Check**: Are there words in <target_chunk> that change meaning
   based on <previous_context>? (e.g., "run", "bank", "hit").
2. **Boundary Check**: How does the <next_context> begin? Does my translation
   create a valid transition?
3. **Tone Check**: Is the source journalistic, academic, or casual? Match it.

# Output
Return ONLY the translated text for the <target_chunk>. Do not include the
context tags or your internal monologue in the final output string.
"""

HUMAN_INPUT_TEMPLATE = """
Dynamic document summary based on the target chunk: {dynamic_summary}
Target chunk: {target_chunk}
Previous Chunk(optional): {previous_chunk}
Next Chunk(optional): {next_chunk}

Current Language: {current_language}
Target Language: {target_language}
"""

RETRY_PROMPT = """
Retry based strictly on the given feedback:
{feedback}
"""

EVALUATOR_PROMPT = """
# Role
You are a Senior Localization Quality Assurance Auditor. You are evaluating a
translation chunk against its source.

# Evaluation Hierarchy
Assess the translation for the following specific failure modes. If a Critical
failure is found, the score must be 1.

1. **CRITICAL FAILURES**
    - **Hallucination/Glitch**: Does the translation devolve into gibberish,
      repetitive loops, or random lowercase text?
    - **Untranslated Content**: Are there English words left in the text that
      should have been translated?
    - **Critical Omission**: Is a significant portion of the source meaning
      missing? (e.g., a whole clause or sentence dropped).
    - **Meaning Inversion**: Does the translation say the opposite of the
      source? (e.g., "Defeated" translated as "Augmented").

2. **MAJOR ERRORS**
    - **Contextual Clashes**: Does the translation fail to agree with the
      <previous_context> (e.g., wrong gender for a previously mentioned noun)?
    - **False Friends/Literalism**: Does it use a dictionary definition that
      makes no sense in context (e.g., translating "running a business" as
      "jogging a business")?
    - **Boundary Friction**: Does the end of the translation create a
      grammatical error when read immediately before <next_context>?

3. **MINOR ERRORS**
    - **Style/Tone**: Is the register slightly off (e.g., too informal for a
      news article)?
    - **Punctuation**: Minor spacing or punctuation errors that do not affect
      meaning.
"""

DYNAMIC_CONTEXT_PROMPT = """
# Role
You are a "Context Injection Engine" for a high-precision translation pipeline.
Your goal is to analyze a specific segment of text (the "Target Chunk") and
extract ONLY the relevant background information from the full document that a
translator would need to translate that specific chunk accurately.

# Input Data
1. <full_document>: The complete text (for reference).
2. <target_chunk>: The specific segment currently being translated.

# The Problem You Are Solving
Translators often fail because they lack context for specific words in the chunk.
- Example Error: Translating "The driver failed" as "The chauffeur failed" when
  the full document reveals the topic is "Printer Software."
- Example Error: Translating "He hit him" as "He punched him" when the full
  document reveals the topic is "Poker" (hit me with a card).

# Your Task
Analyze the <target_chunk> and generate a **"Context Brief"**. You must look at
the <full_document> to answer these three specific questions for the translator:

1.  **Ambiguity Resolution**:
    - Are there polysemous words (words with multiple meanings) in the chunk?
      (e.g., "Run", "Bank", "Hit", "Court").
    - Based on the <full_document>, what is the *exact* definition of those
      words in this specific instance?

2.  **Entity Identification**:
    - Does the chunk contain pronouns like "He", "She", "It", "They"?
    - Who or what do they refer to? (Find the antecedent in the <full_document>).
    - Are there proper nouns? What are they? (e.g., "Juba" is a person, not a place).

3.  **Tone & Domain alignment**:
    - Does this specific chunk require a shift in tone compared to the rest of
      the document? (e.g., A sudden quote within a narrative).

# Strict Output Format
Return a structured JSON object. Do not output conversational text.

{
  "domain_context": "One sentence describing the specific topic of this chunk
    (e.g., '19th-century dance competition' or 'Software installation guide').",
  "ambiguity_glossary": {
    "problematic_word_1": "Specific meaning in this context (e.g., 'Hit' =
      'Assassination', not 'Musical Success')",
    "problematic_word_2": "Specific meaning..."
  },
  "pronoun_resolutions": {
    "it": "Refers to the 'Server Cluster'",
    "he": "Refers to 'Master Juba'"
  }
}
"""


DYNAMIC_CONTEXT_INPUT_PROMPT_TEMPLATE = """
Full document: {full_docs_content}
Target chunk: {target_chunk}
"""


translation_rubric = [
    Rubric(
        score_range=(0, 2),
        expected_outcome="The translation is missing, irrelevant, or purely "
        "hallucinates information not present in the source chunk.",
    ),
    Rubric(
        score_range=(3, 5),
        expected_outcome="The translation conveys general meaning but fails "
        "grammatically due to ignoring the 'previous_context' (e.g., wrong "
        "gender/number) or breaks the syntax of the 'next_context'.",
    ),
    Rubric(
        score_range=(6, 7),
        expected_outcome="The translation is accurate in isolation but creates "
        "a slightly awkward or unnatural transition with the surrounding text "
        "chunks.",
    ),
    Rubric(
        score_range=(8, 9),
        expected_outcome="The translation is accurate and grammatically correct "
        "within the context, with only very minor stylistic friction.",
    ),
    Rubric(
        score_range=(10, 10),
        expected_outcome="The translation is flawless. It perfectly respects the "
        "gender/number from the previous context, flows seamlessly into the "
        "next context, and preserves all formatting.",
    ),
]


class TranslatedChunk(BaseModel):
    thought_process: str = Field(
        description="Analysis of the context, pronouns, and sentence flow boundaries."
    )
    translation: str = Field(description="The translation of the target chunk")
    confidence_score: float = Field(
        description="Score from 0.0 to 1.0 on how confident you are in your translation"
    )
    reasoning: str = Field(description="Reasoning for the confidence score value given")


_EVALUATOR_MODEL = "deepseek-ai/DeepSeek-V3.2"
_TRANSLATOR_MODEL = "deepseek-ai/DeepSeek-V3.2"

output_price, input_price = get_pricing_info(_EVALUATOR_MODEL)
DEEPEVAL_MODEL = GPTModel(
    model=_EVALUATOR_MODEL,
    api_key=settings.llm_api_key,
    base_url="https://api.studio.nebius.ai/v1/",
    cost_per_input_token=input_price,
    cost_per_output_token=output_price,
)

_MACHINE_TRANSLATION_EVALUATOR = GEval(
    name="machine translation evaluation",
    criteria=EVALUATOR_PROMPT,
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
    rubric=translation_rubric,
    threshold=0.7,
    model=DEEPEVAL_MODEL,
)


def evaluate_translation(result: str, messages: list[BaseMessage]) -> EvaluationResult:
    first_message: SystemMessage = messages[0]
    test_case = LLMTestCase(input=first_message.content, actual_output=result)
    return evaluate(test_cases=[test_case], metrics=[_MACHINE_TRANSLATION_EVALUATOR])


def translation(
    client: BaseChatModel,
    messages: list[BaseMessage],
) -> str:
    client = client.with_structured_output(schema=TranslatedChunk, strict=True)
    final_translation = ""
    iteration_number = 0
    while True:
        try:
            print(
                f"Current length of messages for iteration # {iteration_number}"
                f": {len(messages)}"
            )
            results = client.invoke(input=messages)
        except Exception as e:
            raise RuntimeError(f"Something went wrong during invoke: {e}") from e

        print(f"[DEBUG] Results: {str(results)}")

        if results is None:
            print("Translation results cannot be None, Retrying...")
            continue

        translation_results = cast(TranslatedChunk, results)
        print(f"[DEBUG] Starting evaluation on {translation_results.translation}")
        final_translation = translation_results.translation

        eval_results = evaluate_translation(result=final_translation, messages=messages)
        eval_results = eval_results.test_results[0].metrics_data[0]
        print(f"[DEBUG] Evaluation results: {eval_results.score}")
        if not eval_results.success:
            print(f"[DEBUG] Retrying due to reason: {eval_results.reason}")
            messages.append(AIMessage(content=translation_results.translation))
            messages.append(
                HumanMessage(content=RETRY_PROMPT.format(feedback=eval_results.reason))
            )
        else:
            print(f"[DEBUG] Passed ({eval_results.score})")
            break
        iteration_number += 1

    return final_translation


messages_list: list[list[BaseMessage]] = []
client_list: list[BaseChatModel] = []

for _, doc in enumerate(final_docs):
    client = ChatNebius(model=_TRANSLATOR_MODEL, api_key=settings.llm_api_key)

    _msg_input = [
        SystemMessage(content=DYNAMIC_CONTEXT_PROMPT),
        HumanMessage(
            content=DYNAMIC_CONTEXT_INPUT_PROMPT_TEMPLATE.format(
                full_docs_content=results, target_chunk=doc.page_content
            )
        ),
    ]
    dynamic_summary = client.invoke(_msg_input)
    print(f"Geneated dynamic summary for the target chunk: {dynamic_summary}")
    messages = [
        SystemMessage(content=TRANSLATION_PROMPT),
        HumanMessage(
            content=HUMAN_INPUT_TEMPLATE.format(
                dynamic_summary=dynamic_summary if dynamic_summary else "",
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
with ThreadPoolExecutor(max_workers=20) as executor:
    results = executor.map(translation, client_list, messages_list)

    for result in results:
        final_translation += result

print(final_translation)

with open(
    f"app/scripts/filipino{_TRANSLATOR_MODEL.replace('/', '_')}.md",
    mode="w",
    encoding="utf-8",
) as file:
    file.write(final_translation)
