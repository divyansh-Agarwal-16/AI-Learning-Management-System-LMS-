"""RAG Tools module for the Multi-Agent System.

Provides tools to search course textbooks/documents and summarize individual lessons.
"""

import sys
import structlog
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Configure sys.path to resolve root and backend directory imports
root_path = Path(__file__).parent.parent.parent
backend_path = root_path / "backend"
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from app.models.course import Lesson
from rag.retrieval.retriever import LMSHybridRetriever

logger = structlog.get_logger()


async def search_course_docs(query: str, course_id: str) -> List[str]:
    """Queries the custom hybrid vector and keyword database to find relevant course material.

    Args:
        query (str): The search query keywords/questions.
        course_id (str): The Course UUID to query.

    Returns:
        List[str]: Top 5 matching parent context text chunks.
    """
    logger.info("tool_search_course_docs_start", query=query, course_id=course_id)
    
    try:
        # Initialize retriever
        retriever = LMSHybridRetriever()
        nodes_with_score = retriever.retrieve(query_str=query, course_id=course_id)
        
        # Extract content text from matching nodes
        chunks = []
        for node_with_score in nodes_with_score:
            node = node_with_score.node
            # Extract content without metadata tags to feed clean LLM context
            from llama_index.core.schema import MetadataMode
            content = node.get_content(metadata_mode=MetadataMode.NONE)
            source_file = node.metadata.get("source", "Unknown")
            page_num = node.metadata.get("page_number", 1)
            chunks.append(f"Content: {content}\n(Source: {source_file}, Page: {page_num})")
            
        logger.info("tool_search_course_docs_success", chunks_found=len(chunks))
        return chunks
        
    except Exception as e:
        logger.error("tool_search_course_docs_failed", error=str(e))
        # Graceful fallback: return a notice so the agent knows search failed
        return [f"Warning: Course document search is unavailable (details: {str(e)})."]


async def get_lesson_summary(lesson_id: str, db: AsyncSession) -> str:
    """Fetches details of a lesson from the database to generate a brief summary.

    Args:
        lesson_id (str): UUID representation of the Lesson.
        db (AsyncSession): Active database transaction session.

    Returns:
        str: Summary description of the lesson content.
    """
    logger.info("tool_get_lesson_summary_start", lesson_id=lesson_id)
    
    try:
        # Query lesson table
        result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = result.scalar_one_or_none()
        
        if not lesson:
            logger.warning("tool_get_lesson_summary_not_found", lesson_id=lesson_id)
            return "Lesson details not found in database catalog."
            
        summary = (
            f"Lesson Title: {lesson.title}\n"
            f"Duration: {lesson.duration}\n"
            f"Video Stream URL: {lesson.videoUrl or 'None'}\n"
            f"Textbook Document: {lesson.pdfUrl or 'None'}\n"
            f"Sorting Order Index: {lesson.order}"
        )
        logger.info("tool_get_lesson_summary_success", lesson_title=lesson.title)
        return summary
        
    except Exception as e:
        logger.error("tool_get_lesson_summary_failed", error=str(e))
        return f"Error retrieving lesson summary metadata: {str(e)}"
