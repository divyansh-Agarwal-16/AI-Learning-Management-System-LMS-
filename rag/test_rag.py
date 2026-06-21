"""Unit tests for the RAG Pipeline modules.

Tests video ID extraction, chunking metadata assignment, and API key validations.
"""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from llama_index.core import Document
from rag.ingestion.ingest import DocumentIngestor
from rag.retrieval.retriever import LMSHybridRetriever
from rag.query.query_engine import LMSQueryEngine


class TestRAGPipeline(unittest.TestCase):
    """Test suite validating ingestion, parsing, retrieval, and query logic."""

    def test_youtube_video_id_extraction(self):
        """Verifies parsing of standard and short YouTube URLs."""
        # We temporarily mock Pinecone during __init__
        with patch("rag.ingestion.ingest.Pinecone") as mock_pc:
            mock_idx = MagicMock()
            mock_idx.name = "ai-lms"
            mock_pc.return_value.list_indexes.return_value = [mock_idx]
            ingestor = DocumentIngestor(
                index_name="ai-lms",
                api_key="mock-pinecone-key",
                openai_key="mock-openai-key"
            )

            # Test standard URLs
            self.assertEqual(
                ingestor.extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
                "dQw4w9WgXcQ"
            )
            # Test short URLs
            self.assertEqual(
                ingestor.extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ"),
                "dQw4w9WgXcQ"
            )
            # Test query param variations
            self.assertEqual(
                ingestor.extract_youtube_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ&feature=share"),
                "dQw4w9WgXcQ"
            )
            # Test raw IDs
            self.assertEqual(
                ingestor.extract_youtube_video_id("dQw4w9WgXcQ"),
                "dQw4w9WgXcQ"
            )
            # Test invalid formats
            self.assertIsNone(ingestor.extract_youtube_video_id("invalid-url-not-11-chars"))

    def test_missing_api_keys_raises_value_error(self):
        """Ensures that ValueError is raised if any API key is missing."""
        # Unset env vars to prevent local machine values from leaking into test
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                DocumentIngestor(api_key=None, openai_key=None)
            self.assertIn("PINECONE_API_KEY", str(ctx.exception))

            with self.assertRaises(ValueError) as ctx:
                DocumentIngestor(api_key="pinecone-key", openai_key=None)
            self.assertIn("OPENAI_API_KEY", str(ctx.exception))

    def test_text_loading(self):
        """Verifies text loader reads content and applies course/lesson metadata."""
        with patch("rag.ingestion.ingest.Pinecone") as mock_pc:
            mock_idx = MagicMock()
            mock_idx.name = "ai-lms"
            mock_pc.return_value.list_indexes.return_value = [mock_idx]
            ingestor = DocumentIngestor(
                index_name="ai-lms",
                api_key="mock-pinecone-key",
                openai_key="mock-openai-key"
            )

            # Create a temp file
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as temp_f:
                temp_f.write("Hello world! This is a test document.")
                temp_path = Path(temp_f.name)

            try:
                docs = ingestor.load_text(
                    file_path=temp_path,
                    course_id="test-course-uuid",
                    lesson_id="test-lesson-uuid"
                )

                self.assertEqual(len(docs), 1)
                self.assertEqual(docs[0].text, "Hello world! This is a test document.")
                self.assertEqual(docs[0].metadata["course_id"], "test-course-uuid")
                self.assertEqual(docs[0].metadata["lesson_id"], "test-lesson-uuid")
                self.assertEqual(docs[0].metadata["source"], temp_path.name)
            finally:
                # Cleanup temp file
                if temp_path.exists():
                    temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
