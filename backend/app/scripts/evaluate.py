import json

from deepeval.evaluate.types import EvaluationResult
from deepeval.test_case import LLMTestCase

from app.routes.dependencies.evaluator import get_evaluation_pipeline_manual
from app.routes.dependencies.rag import get_retriever_service_manual
from app.utils import get_request_id

#### VIBE CODED ####


def format_metric_value(val):
    """Helper to format scores to 3 decimal places if they are floats."""
    if isinstance(val, float):
        return f"{val:.3f}"
    return str(val)


def generate_md_report(evaluation_result: EvaluationResult) -> str:
    """
    Generates a Markdown report from a DeepEval EvaluationResult object.
    """
    md_output = ""

    # Iterate through each test case result
    for test_result in evaluation_result.test_results:
        # --- 1. Header Information ---
        icon = "✅" if test_result.success else "❌"
        status_text = "PASSED" if test_result.success else "FAILED"

        md_output += f"# 🧪 Test Case: {test_result.name}\n\n"
        md_output += f"**Status:** {icon} **{status_text}**\n\n"

        # Handle Input (can be str or List)
        input_display = test_result.input
        if isinstance(input_display, list):
            # If multimodal or list input, convert to string representation
            input_display = str(input_display)

        md_output += f'**Input Query:**\n> *"{input_display}"*\n\n'

        md_output += "---\n\n"

        # --- 2. Metrics Summary Table ---
        if test_result.metrics_data:
            md_output += "## 📊 Metrics Summary\n\n"
            md_output += "| Metric Name | Score | Threshold | Status |\n"
            md_output += "| :--- | :--- | :--- | :--- |\n"

            for metric in test_result.metrics_data:
                m_icon = "✅ Pass" if metric.success else "❌ Fail"
                score = format_metric_value(metric.score)
                threshold = format_metric_value(metric.threshold)
                md_output += (
                    f"| **{metric.name}** | {score} | {threshold} | {m_icon} |\n"
                )

            md_output += "\n---\n\n"

        # --- 3. Detailed Analysis per Metric ---
        if test_result.metrics_data:
            md_output += "## 🔍 Detailed Analysis\n\n"

            for metric in test_result.metrics_data:
                m_icon = "✅" if metric.success else "❌"
                score = format_metric_value(metric.score)

                md_output += f"### {m_icon} {metric.name}\n"
                md_output += f"- **Score:** {score}\n"
                md_output += f"- **Reason:** {metric.reason}\n\n"

                # Handling Verbose Logs
                if metric.verbose_logs:
                    md_output += (
                        "<details>\n<summary><strong>View Verbose Logs"
                        " & Verdicts</strong></summary>\n\n"
                    )
                    md_output += "```text\n"  # Using text/json
                    md_output += str(metric.verbose_logs)
                    md_output += "\n```\n"
                    md_output += "</details>\n\n"

        # --- 4. Retrieval & Context Data (Optional but useful) ---
        md_output += "## 📚 Retrieval Data\n\n"

        if test_result.retrieval_context:
            md_output += (
                "<details>\n<summary><strong>Retrieval Context"
                "(Chunks)</strong></summary>\n\n"
            )
            for i, ctx in enumerate(test_result.retrieval_context):
                md_output += f"**Chunk {i + 1}:**\n> {ctx}\n\n"
            md_output += "</details>\n\n"

        if test_result.actual_output:
            md_output += f"**Actual LLM Output:**\n\n> {test_result.actual_output}\n\n"

        md_output += "---\n\n"

    return md_output


#### VIBE CODED ####

with open("app/data/reports/synthetic_golden_dataset.json") as file:
    data_list = json.load(file)
filtered_data_list = []
for data in data_list:
    if (
        data["additional_metadata"]["context_quality"] > 0.8
        and data["additional_metadata"]["synthetic_input_quality"] > 0.8
    ):
        filtered_data_list.append(data)

filtered_data_list = filtered_data_list[:5]
user_query = [data["input"] for data in filtered_data_list]

print(len(filtered_data_list) / len(data_list) * 100, "%")

llm_test_list: list[LLMTestCase | None] = []

retriever_service = get_retriever_service_manual()
for i, query in enumerate(user_query):
    agent_state = retriever_service.retrieve_documents(
        query=query, is_llm_enabled=True, request_id=get_request_id()
    )
    retrieved_contexts = agent_state["documents"]
    retrieved_contexts = [docs["text"] for docs in retrieved_contexts]
    llm_test_list.append(
        LLMTestCase(
            input=query,
            actual_output=agent_state["final_answer"],
            expected_output=filtered_data_list[i]["expected_output"],
            context=filtered_data_list[i]["context"],
            retrieval_context=retrieved_contexts,
        )
    )

evaluator = get_evaluation_pipeline_manual()
eval_results = evaluator.evaluate(llm_test_list)

markdown_report = generate_md_report(eval_results)
with open("app/data/reports/test_report.md", "w", encoding="utf-8") as f:
    f.write(markdown_report)
