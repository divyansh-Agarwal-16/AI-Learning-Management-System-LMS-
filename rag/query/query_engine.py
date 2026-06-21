"""Query Engine module for the AI LMS RAG pipeline.

Queries the retrieval pipeline for course context, formats systemic prompt instructions,
queries OpenAI GPT models, and packages the result alongside metadata source citations.
"""

import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from pinecone import PineconeException
import openai
from dotenv import load_dotenv

from llama_index.core.schema import MetadataMode
from rag.retrieval.retriever import LMSHybridRetriever

# Try loading from backend/.env or root or current dir
for path in [Path(".env"), Path(__file__).parent.parent / ".env", Path(__file__).parent.parent.parent / "backend" / ".env"]:
    if path.exists():
        load_dotenv(dotenv_path=path)
        break


class LMSQueryEngine:
    """Consolidates retrieval lookups and OpenAI completion prompts to return context-cited answers."""

    def __init__(
        self,
        index_name: str = "ai-lms",
        api_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        cohere_key: Optional[str] = None
    ) -> None:
        """Initializes the query engine, loading the hybrid retrieval client.

        Args:
            index_name (str): The Pinecone index name.
            api_key (Optional[str]): Pinecone API key.
            openai_key (Optional[str]): OpenAI API key.
            cohere_key (Optional[str]): Cohere API key.

        Raises:
            ValueError: If required API keys are missing.
        """
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY must be provided or configured.")

        # Initialize the hybrid retrieval engine
        self.retriever = LMSHybridRetriever(
            index_name=index_name,
            api_key=api_key,
            openai_key=self.openai_key,
            cohere_key=cohere_key
        )

        # Configure the standard OpenAI Client
        self.client = openai.OpenAI(api_key=self.openai_key)

    def query(self, query_str: str, course_id: str) -> Dict[str, Any]:
        """Runs RAG lookup and generates an OpenAI answer carrying source citations.

        Args:
            query_str (str): User question text.
            course_id (str): Course UUID namespace filter.

        Returns:
            Dict[str, Any]: A dictionary holding:
                - "answer" (str): The generated response.
                - "sources" (List[Dict[str, Any]]): List of metadata source citations.

        Raises:
            Exception: If database connection or LLM queries fail.
        """
        query_str = query_str.strip()
        
        # 1. Retrieve the top 5 chunks with hybrid lookup + Cohere reranking
        try:
            nodes_with_score = self.retriever.retrieve(query_str, course_id)
        except FileNotFoundError as e:
            # Graceful check if course has not been ingested
            return {
                "answer": (
                    "I cannot answer your question right now because no study materials "
                    f"have been uploaded for course '{course_id}'. Please upload course documents first."
                ),
                "sources": []
            }
        except Exception as e:
            raise RuntimeError(f"Retrieval phase failed inside the query engine: {str(e)}") from e

        if not nodes_with_score:
            return {
                "answer": "I could not find any relevant study materials in this course to answer your query.",
                "sources": []
            }

        # 2. Build Context String with Metadata citations
        context_lines = []
        sources = []
        for idx, node_with_score in enumerate(nodes_with_score):
            node = node_with_score.node
            meta = node.metadata
            source_name = meta.get("source", "Unknown")
            page_num = meta.get("page_number", 1)
            citation_key = f"[Source {idx + 1}]"

            content_text = node.get_content(metadata_mode=MetadataMode.NONE)
            context_lines.append(
                f"{citation_key} - File: {source_name}, Page: {page_num}\n"
                f"Content:\n{content_text}\n"
            )

            sources.append({
                "citation_key": citation_key,
                "source": source_name,
                "page_number": page_num,
                "course_id": meta.get("course_id", ""),
                "lesson_id": meta.get("lesson_id", "")
            })

        combined_context = "\n---\n".join(context_lines)

        # 3. Format Prompt Instructions
        system_prompt = (
            "You are an expert AI Tutor designed to help students learn.\n"
            "Answer the student's question using ONLY the provided course context materials.\n"
            "Format your answer to be clear, educational, and well-structured.\n"
            "At the end of statements where you pull information from a source, cite the source "
            "using its exact citation key (e.g. [Source 1], [Source 2]).\n"
            "If the context materials do not contain sufficient details to answer the query, "
            "state clearly that the available course materials do not contain this information."
        )

        user_prompt = (
            f"Retrieved Course Context:\n"
            f"{combined_context}\n"
            f"Question:\n{query_str}\n\n"
            f"Educational Answer:"
        )

        # 4. Generate LLM response with rate limit retries
        max_retries = 3
        retry_delay = 2
        answer = ""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2
                )
                answer = response.choices[0].message.content or ""
                break
            except openai.RateLimitError as e:
                if attempt == max_retries - 1:
                    raise RuntimeError("GPT API calls failed due to OpenAI rate limits. Please try again.") from e
                print(f"OpenAI LLM rate limit hit. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                raise RuntimeError(f"OpenAI GPT text completion failed: {str(e)}") from e

        return {
            "answer": answer.strip(),
            "sources": sources
        }
