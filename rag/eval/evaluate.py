"""Evaluation module for the AI LMS RAG pipeline.

Queries 20 test QA pairs through the LMSQueryEngine, runs RAGAS metric evaluations
for faithfulness, answer relevancy, context precision and context recall,
saves timestamped JSON results, and outputs a formatted summary table.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_index.core.schema import MetadataMode
from rag.query.query_engine import LMSQueryEngine

try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset
    from tabulate import tabulate
    HAS_EVAL_DEPS = True
except ImportError:
    HAS_EVAL_DEPS = False

# Course UUID constants matching seed.py database values
PYTHON_COURSE_UUID = "e4b3c004-94c6-47b2-84c1-cd54cfc0bf7a"
LLAMA_COURSE_UUID = "9d3f82a1-fa4c-4a30-8a8b-3e5f2a1b1c3c"
LANGGRAPH_COURSE_UUID = "8b3f92d4-fc3a-4a25-9b2c-4f5f8b9b2c2d"

# 20 hardcoded test question-answer pairs relevant to the courses
TEST_SUITE: List[Dict[str, str]] = [
    # 1-8: Python Programming (Beginner)
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "What is the output of print(type([]))?",
        "ground_truth": "The output is <class 'list'>."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "Which keyword is used to define a function in Python?",
        "ground_truth": "The def keyword is used to define functions."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "How do you start a comment in Python?",
        "ground_truth": "A single-line comment in Python starts with the hash symbol (#)."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "Which of these is a mutable data type in Python: list or tuple?",
        "ground_truth": "A list is mutable, whereas a tuple is immutable."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "What is the default return value of a function that doesn't return anything?",
        "ground_truth": "The default return value is None."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "How do you instantiate an object of a class in Python?",
        "ground_truth": "You call the class name followed by parentheses, e.g., my_obj = MyClass()."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "What is the primary difference between a list and a tuple in Python?",
        "ground_truth": "Lists are mutable and declared with square brackets [], while tuples are immutable and declared with parentheses ()."
    },
    {
        "course_id": PYTHON_COURSE_UUID,
        "question": "How do you check if a key exists in a dictionary?",
        "ground_truth": "Using the 'in' keyword, e.g., if key in my_dict."
    },

    # 9-14: LlamaIndex RAG Pipelines (Intermediate)
    {
        "course_id": LLAMA_COURSE_UUID,
        "question": "What does RAG stand for?",
        "ground_truth": "RAG stands for Retrieval-Augmented Generation."
    },
    {
        "course_id": LLAMA_COURSE_UUID,
        "question": "What is the primary function of a VectorStoreIndex?",
        "ground_truth": "It indexes text document segments and generates vector embeddings to enable semantic search."
    },
    {
        "course_id": LLAMA_COURSE_UUID,
        "question": "In LlamaIndex, what represents a parsed chunk of a document?",
        "ground_truth": "A parsed document chunk is represented by a Node object."
    },
    {
        "course_id": LLAMA_COURSE_UUID,
        "question": "Which component handles combining matching context nodes with the prompt in LlamaIndex?",
        "ground_truth": "The Response Synthesizer component handles combining contexts with LLM prompts."
    },
    {
        "course_id": LLAMA_COURSE_UUID,
        "question": "Which LLM is used by default if none is configured in LlamaIndex?",
        "ground_truth": "By default, LlamaIndex uses OpenAI's GPT-3.5-Turbo or GPT-4."
    },
    {
        "course_id": LLAMA_COURSE_UUID,
        "question": "How do you load documents from a local directory in LlamaIndex?",
        "ground_truth": "You load them using SimpleDirectoryReader(directory_path).load_data()."
    },

    # 15-20: LangGraph Multi-Agent (Advanced)
    {
        "course_id": LANGGRAPH_COURSE_UUID,
        "question": "What is LangGraph?",
        "ground_truth": "LangGraph is a stateful orchestration library built for creating cyclic agent workflows using LLMs."
    },
    {
        "course_id": LANGGRAPH_COURSE_UUID,
        "question": "What is the purpose of the State dictionary in LangGraph?",
        "ground_truth": "It acts as a centralized database persisted between nodes to share execution context."
    },
    {
        "course_id": LANGGRAPH_COURSE_UUID,
        "question": "How are operations and transitions represented in LangGraph graphs?",
        "ground_truth": "Operations are represented as Nodes, and transitions are represented as Edges."
    },
    {
        "course_id": LANGGRAPH_COURSE_UUID,
        "question": "What is a conditional edge in LangGraph?",
        "ground_truth": "An edge routing graph execution paths dynamically based on a custom routing function output."
    },
    {
        "course_id": LANGGRAPH_COURSE_UUID,
        "question": "How does LangGraph handle short-term memory during stateful flows?",
        "ground_truth": "Through state persistence and checkpointing mechanisms saving node execution states."
    },
    {
        "course_id": LANGGRAPH_COURSE_UUID,
        "question": "What is a human-in-the-loop trigger in LangGraph?",
        "ground_truth": "A checkpoint interrupt pausing graph execution to await manual user validation and feedback."
    }
]


def run_evaluation():
    print("Initializing AI LMS RAG Query Engine...")
    try:
        query_engine = LMSQueryEngine()
    except Exception as e:
        print(f"[ERROR] Connection failed: {str(e)}")
        print("Please check that PINECONE_API_KEY and OPENAI_API_KEY are configured.")
        sys.exit(1)

    print(f"Beginning evaluation of {len(TEST_SUITE)} test QA pairs...")

    questions = []
    answers = []
    contexts = []
    ground_truths = []
    results_raw = []

    for idx, item in enumerate(TEST_SUITE):
        q = item["question"]
        gt = item["ground_truth"]
        cid = item["course_id"]
        print(f"[{idx + 1}/{len(TEST_SUITE)}] Querying: '{q}' in course '{cid[:8]}...'")

        # Run query engine to extract generated answer and retrieved source texts
        try:
            start_time = time.time()
            res = query_engine.query(q, cid)
            latency = time.time() - start_time
            
            # Extract source node texts
            source_texts = []
            if "sources" in res:
                # To populate Ragas contexts properly, we need the actual text contents
                # Retrieve nodes from the hybrid lookup
                try:
                    nodes_with_score = query_engine.retriever.retrieve(q, cid)
                    source_texts = [n.node.get_content(metadata_mode=MetadataMode.NONE) for n in nodes_with_score]
                except Exception:
                    # Fallback using citation metadata text if retrieval fails
                    source_texts = [f"Source: {s.get('source')} Page: {s.get('page_number')}" for s in res["sources"]]
            
            if not source_texts:
                source_texts = ["No context found."]

            questions.append(q)
            answers.append(res["answer"])
            contexts.append(source_texts)
            ground_truths.append(gt)

            results_raw.append({
                "question": q,
                "ground_truth": gt,
                "generated_answer": res["answer"],
                "contexts": source_texts,
                "latency_seconds": latency
            })
        except Exception as e:
            print(f"  Warning: Query failed for '{q}': {str(e)}")
            # Log failure row
            questions.append(q)
            answers.append("Execution error.")
            contexts.append(["Error during retrieval."])
            ground_truths.append(gt)
            results_raw.append({
                "question": q,
                "ground_truth": gt,
                "generated_answer": "Execution error.",
                "contexts": ["Error during retrieval."],
                "latency_seconds": 0.0,
                "error": str(e)
            })

    # Assert evaluation dependencies
    if not HAS_EVAL_DEPS:
        print("\n[WARNING] RAGAS or tabulate libraries are not installed.")
        print("Skipping metric evaluations. Saving raw execution traces to file.")
        save_results(results_raw, None)
        return

    # Check for empty context fallbacks (ragas crashes if context is empty/invalid)
    valid_indices = [i for i, ctx in enumerate(contexts) if ctx and ctx[0] != "No context found."]
    if not valid_indices:
        print("\n[WARNING] No documents found in database. All queries returned empty contexts.")
        print("Ragas metrics cannot evaluate empty contexts. Seeding database first is required.")
        save_results(results_raw, {"status": "skipped_empty_contexts"})
        return

    # Create Datasets format for Ragas evaluate
    print("\nRunning Ragas evaluation scoring...")
    eval_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    try:
        # Run Ragas scoring logic
        score_result = evaluate(
            eval_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
        )
        
        # Save results
        save_results(results_raw, score_result)
        
        # Print summary table
        print_summary_table(score_result)
    except Exception as e:
        print(f"\n[ERROR] Ragas metric scoring failed: {str(e)}")
        print("Saving raw traces without metrics.")
        save_results(results_raw, None)


def save_results(raw_traces: List[Dict[str, Any]], score_result: Optional[Any]) -> None:
    """Writes evaluation run configurations and scoring statistics to JSON file.

    Args:
        raw_traces (List[Dict[str, Any]]): Collected per-query generated logs.
        score_result (Optional[Any]): Computed average RAGAS scores.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = results_dir / f"eval_{timestamp}.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "summary_scores": dict(score_result) if score_result else "unavailable",
        "detailed_runs": raw_traces
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"\n[SUCCESS] Saved evaluation results to: {file_path.absolute()}")


def print_summary_table(score_result: Any) -> None:
    """Draws tabulate grids listing computed RAGAS scores to console.

    Args:
        score_result (Any): Calculated Ragas metrics dictionary.
    """
    headers = ["Metric", "Average Score"]
    rows = []
    
    for metric_name, score in score_result.items():
        rows.append([metric_name.replace("_", " ").title(), f"{score:.4f}"])
        
    print("\n" + "=" * 40)
    print("             RAGAS EVALUATION SUMMARY")
    print("=" * 40)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print("=" * 40 + "\n")


if __name__ == "__main__":
    run_evaluation()
