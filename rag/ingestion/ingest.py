"""Document Ingestion module for the AI LMS RAG pipeline.

Loads PDFs, YouTube transcripts, and text/markdown files, parses them hierarchically,
runs OpenAI embeddings, and stores them in Pinecone namespaces with local document store fallbacks.
"""

import os
import re
import uuid
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from pinecone import Pinecone, PineconeException
import openai
from dotenv import load_dotenv

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore

# Try loading from backend/.env or root or current dir
for path in [Path(".env"), Path(__file__).parent.parent / ".env", Path(__file__).parent.parent.parent / "backend" / ".env"]:
    if path.exists():
        load_dotenv(dotenv_path=path)
        break

# Persistence folder for parent/document storage matching course namespaces
STORAGE_DIR = Path(__file__).parent.parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class DocumentIngestor:
    """Handles loading files, hierarchical chunking, embedding generation, and database indexing."""

    def __init__(
        self,
        index_name: str = "ai-lms",
        api_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> None:
        """Initializes the ingestor, validating Pinecone and OpenAI key credentials.

        Args:
            index_name (str): The Pinecone index name.
            api_key (Optional[str]): Pinecone API key.
            openai_key (Optional[str]): OpenAI API key.

        Raises:
            ValueError: If required API keys are not supplied.
            PineconeException: If Pinecone connection fails.
        """
        self.index_name = index_name
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY must be provided or configured in the environment.")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY must be provided or configured in the environment.")

        # Initialize Pinecone and check index existence
        try:
            self.pc = Pinecone(api_key=self.api_key)
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                raise PineconeException(
                    f"Pinecone index '{self.index_name}' does not exist on this host. "
                    "Please create a 1536-dimension index matching standard text-embedding-3-small."
                )
            self.pinecone_index = self.pc.Index(self.index_name)
        except Exception as e:
            raise PineconeException(f"Failed to connect to Pinecone server: {str(e)}")

        # Configure OpenAI Embedding Model
        self.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=self.openai_key
        )

    def extract_youtube_video_id(self, url_or_id: str) -> Optional[str]:
        """Extracts the 11-character video ID from a YouTube URL.

        Args:
            url_or_id (str): A full YouTube link or raw ID.

        Returns:
            Optional[str]: 11-character YouTube video ID, or None if match fails.
        """
        url_or_id = url_or_id.strip()
        if len(url_or_id) == 11:
            return url_or_id
        match = re.search(r"(?:v=|\/)([\w-]{11})(?:\?|&|$)", url_or_id)
        return match.group(1) if match else None

    def load_pdf(self, file_path: Path, course_id: str, lesson_id: Optional[str] = None) -> List[Document]:
        """Reads a PDF document page-by-page.

        Args:
            file_path (Path): Path to the target PDF file.
            course_id (str): Course UUID mapping context.
            lesson_id (Optional[str]): Lesson UUID mapping context.

        Returns:
            List[Document]: Parsed pages as LlamaIndex Documents.

        Raises:
            FileNotFoundError: If PDF does not exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        documents = []
        try:
            reader = PdfReader(str(file_path))
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                doc = Document(
                    text=text,
                    id_=f"{file_path.name}_page_{page_idx + 1}_{uuid.uuid4().hex[:6]}",
                    metadata={
                        "source": file_path.name,
                        "page_number": page_idx + 1,
                        "course_id": str(course_id),
                        "lesson_id": str(lesson_id) if lesson_id else "None"
                    }
                )
                documents.append(doc)
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF file {file_path.name}: {str(e)}")
        return documents

    def load_youtube(self, url_or_id: str, course_id: str, lesson_id: Optional[str] = None) -> List[Document]:
        """Downloads transcripts for a YouTube video.

        Args:
            url_or_id (str): A full YouTube URL link or ID.
            course_id (str): Course UUID mapping context.
            lesson_id (Optional[str]): Lesson UUID mapping context.

        Returns:
            List[Document]: The transcripts bundled inside a Document.

        Raises:
            ValueError: If YouTube video ID could not be parsed.
            RuntimeError: If download fails due to disablement or system errors.
        """
        video_id = self.extract_youtube_video_id(url_or_id)
        if not video_id:
            raise ValueError(f"Could not parse valid 11-char YouTube video ID from: {url_or_id}")

        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            combined_text = " ".join([entry['text'] for entry in transcript_list])
            doc = Document(
                text=combined_text,
                id_=f"youtube_{video_id}_{uuid.uuid4().hex[:6]}",
                metadata={
                    "source": f"https://youtube.com/watch?v={video_id}",
                    "page_number": 1,
                    "course_id": str(course_id),
                    "lesson_id": str(lesson_id) if lesson_id else "None"
                }
            )
            return [doc]
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            raise RuntimeError(f"YouTube transcript is disabled or not found for video '{video_id}': {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to query YouTube Transcript API: {str(e)}")

    def load_text(self, file_path: Path, course_id: str, lesson_id: Optional[str] = None) -> List[Document]:
        """Loads text or markdown files.

        Args:
            file_path (Path): Path to text/markdown document.
            course_id (str): Course UUID.
            lesson_id (Optional[str]): Lesson UUID.

        Returns:
            List[Document]: Parsed text wrapped as a Document.

        Raises:
            FileNotFoundError: If target file does not exist.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found at path: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            doc = Document(
                text=content,
                id_=f"{file_path.name}_{uuid.uuid4().hex[:6]}",
                metadata={
                    "source": file_path.name,
                    "page_number": 1,
                    "course_id": str(course_id),
                    "lesson_id": str(lesson_id) if lesson_id else "None"
                }
            )
            return [doc]
        except Exception as e:
            raise RuntimeError(f"Error reading text file {file_path.name}: {str(e)}")

    def ingest(
        self,
        file_path_or_url: str,
        file_type: str,
        course_id: str,
        lesson_id: Optional[str] = None
    ) -> int:
        """Processes the document, runs hierarchical chunking, generates embeddings and saves to DB.

        Args:
            file_path_or_url (str): File system path or YouTube link.
            file_type (str): Type indicator ('pdf', 'youtube', 'txt', 'md').
            course_id (str): Course UUID.
            lesson_id (Optional[str]): Lesson UUID.

        Returns:
            int: The number of leaf chunks indexed into the Pinecone database.

        Raises:
            ValueError: If file_type is unsupported.
            Exception: If rate limits or DB connection failures occur.
        """
        # 1. Load Documents
        file_type = file_type.lower().strip()
        if file_type == "pdf":
            documents = self.load_pdf(Path(file_path_or_url), course_id, lesson_id)
        elif file_type == "youtube":
            documents = self.load_youtube(file_path_or_url, course_id, lesson_id)
        elif file_type in ("txt", "md"):
            documents = self.load_text(Path(file_path_or_url), course_id, lesson_id)
        else:
            raise ValueError(f"Unsupported file_type: {file_type}. Use 'pdf', 'youtube', 'txt', or 'md'.")

        if not documents:
            return 0

        # Create localized namespaces persistence paths for docstore
        course_dir = STORAGE_DIR / f"course_{course_id}"
        course_dir.mkdir(parents=True, exist_ok=True)
        docstore_path = course_dir / "docstore.json"

        # Load or create local docstore
        if docstore_path.exists():
            try:
                docstore = SimpleDocumentStore.from_persist_path(str(docstore_path))
            except Exception:
                docstore = SimpleDocumentStore()
        else:
            docstore = SimpleDocumentStore()

        # 2. Hierarchical Chunking Configuration and Explanation
        #
        # --- CHUNKING SIZE STRATEGY CHOICES ---
        # - Parent Chunk (512 tokens): Large enough to retain a comprehensive semantic context 
        #   (e.g., full sections, explanations of functions, or complete paragraphs). This size 
        #   avoids context fragmentation and ensures the LLM receives cohesive background data.
        # - Child Chunk (128 tokens): Granular enough for highly specific vector similarity matching 
        #   (e.g., queries about individual variables, equations, or timestamps). 
        # - Overlap (20 tokens): Guarantees that search queries targeting terms lying on boundaries 
        #   are caught by either child, maintaining semantic flow between contiguous chunks.
        #
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[512, 128],
            chunk_overlap=20
        )
        
        nodes = node_parser.get_nodes_from_documents(documents)
        leaf_nodes = get_leaf_nodes(nodes)

        # Set specific node metadata identifying parent vs child elements
        for node in nodes:
            is_leaf = node in leaf_nodes
            node.metadata = {
                **node.metadata,
                "chunk_type": "child" if is_leaf else "parent"
            }

        # Add all nodes (both parents and children) to the document store for pointer lookups
        docstore.add_documents(nodes)

        # 3. Embedding and Vector Database Storage Setup
        vector_store = PineconeVectorStore(
            pinecone_index=self.pinecone_index,
            namespace=f"course_{course_id}"
        )
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            docstore=docstore
        )

        # Upsert child/leaf vectors into Pinecone with retry logic on rate limits
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                # VectorStoreIndex embeds the provided leaf_nodes and writes them to Pinecone
                VectorStoreIndex(
                    leaf_nodes,
                    storage_context=storage_context,
                    embed_model=self.embed_model
                )
                break
            except openai.RateLimitError as e:
                if attempt == max_retries - 1:
                    raise RuntimeError("Failed to ingest vectors due to OpenAI rate limits. Please try again later.") from e
                print(f"OpenAI rate limit hit during ingestion. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                raise RuntimeError(f"Database insertion failed: {str(e)}") from e

        # Save document store changes locally
        try:
            docstore.persist(str(docstore_path))
        except Exception as e:
            print(f"Warning: Failed to save local docstore: {str(e)}")

        return len(leaf_nodes)
