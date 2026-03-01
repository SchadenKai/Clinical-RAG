from typing import cast

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from app.logger import app_logger
from app.services.rag import RetrievalService
from app.agent.retriever.state import AgentState as InferenceAgentState


@tool
def clinical_retrieval_tool(query: str, runtime: ToolRuntime) -> str:
    """
    Retrieves relevant medical and clinical guidelines documents from CDC and WHO
    using vector search. Use this tool to find factual text chunks regarding
    clinical queries.
    """
    app_logger.info(f"Using clinical_retrieval_tool with query: {query}")
    try:
        context = runtime.context
        retrieval_service: RetrievalService = context.retrieval_service
        request_id = runtime.config.get("configurable", {}).get("thread_id", "")

        if not retrieval_service:
            app_logger.error("Error: RetrievalService not found in agent context.")
            return "Error retrieving documents."

        result_state: dict = retrieval_service.retrieve_documents(
            query=query, request_id=request_id, is_llm_enabled=False
        )
        contexts: list[dict] = result_state.get("documents") or []
        contexts = [
            f"Text: {ctx.get('text', '')}\nSource: {ctx.get('source', '')}"
            for ctx in contexts
        ]
        if not contexts:
            return "No relevant clinical documents found for the query."

        formatted_contexts = "\n\n---\n\n".join(contexts)
        return f"Found the following relevant contexts:\n\n{formatted_contexts}"
    except Exception as e:
        app_logger.error(f"Error in clinical_retrieval_tool: {e}")
        return f"Error retrieving documents: {e}"
