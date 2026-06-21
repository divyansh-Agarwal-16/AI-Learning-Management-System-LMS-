"""Retrieval module for the AI LMS RAG pipeline.

Implements hybrid retrieval (dense Pinecone vector + sparse BM25) with Cohere reranking,
mapping leaf child hits to parent context nodes.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from pinecone import Pinecone, PineconeException
import cohere
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.core.schema import NodeWithScore, NodeRelationship, MetadataMode
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.postprocessor.cohere_rerank import CohereRerank

# Try loading from backend/.env or root or current dir
for path in [Path(".env"), Path(__file__).parent.parent / ".env", Path(__file__).parent.parent.parent / "backend" / ".env"]:
    if path.exists():
        load_dotenv(dotenv_path=path)
        break

STORAGE_DIR = Path(__file__).parent.parent / "storage"


class LMSHybridRetriever:
    """Performs hybrid lookup (vector + BM25 keyword) and Cohere reranking to return top 5 chunks."""

    def __init__(
        self,
        index_name: str = "ai-lms",
        api_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        cohere_key: Optional[str] = None
    ) -> None:
        """Initializes retrieval dependencies (Pinecone, OpenAI embeddings, Cohere reranking).

        Args:
            index_name (str): The Pinecone index name.
            api_key (Optional[str]): Pinecone API key.
            openai_key (Optional[str]): OpenAI API key.
            cohere_key (Optional[str]): Cohere API key.

        Raises:
            ValueError: If required API keys are missing.
        """
        self.index_name = index_name
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.cohere_key = cohere_key or os.getenv("COHERE_API_KEY")

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY must be provided or configured.")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY must be provided or configured.")
        if not self.cohere_key:
            raise ValueError("COHERE_API_KEY must be provided or configured.")

        # Connect to Pinecone index
        try:
            self.pc = Pinecone(api_key=self.api_key)
            self.pinecone_index = self.pc.Index(self.index_name)
        except Exception as e:
            raise PineconeException(f"Retrieval engine failed to connect to Pinecone: {str(e)}")

        # Embeddings configuration
        self.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small",
            api_key=self.openai_key
        )

        # Reranker configuration
        self.reranker = CohereRerank(
            api_key=self.cohere_key,
            top_n=5
        )

    def retrieve(self, query_str: str, course_id: str) -> List[NodeWithScore]:
        """Runs the hybrid retrieval pipeline on a course namespace.

        Args:
            query_str (str): The search query statement.
            course_id (str): Course UUID namespace key.

        Returns:
            List[NodeWithScore]: The top 5 reranked parent/child chunks containing metadata.

        Raises:
            FileNotFoundError: If the local docstore is missing (suggesting ingestion wasn't run).
        """
        # 1. Resolve storage contexts
        course_dir = STORAGE_DIR / f"course_{course_id}"
        docstore_path = course_dir / "docstore.json"

        if not docstore_path.exists():
            raise FileNotFoundError(
                f"No database index records found for course '{course_id}'. "
                "Please run ingestion first to index the course resources."
            )

        # Load parent docstore
        docstore = SimpleDocumentStore.from_persist_path(str(docstore_path))
        all_nodes = list(docstore.docs.values())
        child_nodes = [node for node in all_nodes if node.metadata.get("chunk_type") == "child"]

        if not child_nodes:
            return []

        # 2. Dense Vector Retrieval (Pinecone)
        vector_store = PineconeVectorStore(
            pinecone_index=self.pinecone_index,
            namespace=f"course_{course_id}"
        )
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=self.embed_model
        )
        # Fetch top 10 candidates from vector store
        vector_retriever = index.as_retriever(similarity_top_k=10)
        vector_results = vector_retriever.retrieve(query_str)

        # 3. Sparse Keyword Retrieval (Local BM25)
        # Build local BM25 index on child nodes loaded from local docstore
        bm25_retriever = BM25Retriever.from_defaults(
            nodes=child_nodes,
            similarity_top_k=10
        )
        bm25_results = bm25_retriever.retrieve(query_str)

        # 4. Combine and Deduplicate Results by Node ID
        seen_ids = set()
        combined_nodes = []
        for node_with_score in vector_results + bm25_results:
            node_id = node_with_score.node.node_id
            if node_id not in seen_ids:
                seen_ids.add(node_id)
                combined_nodes.append(node_with_score)

        if not combined_nodes:
            return []

        # 5. Cohere Reranking
        query_bundle = QueryBundle(query_str)
        try:
            reranked_nodes = self.reranker.postprocess_nodes(
                nodes=combined_nodes,
                query_bundle=query_bundle
            )
        except Exception as e:
            # Fallback to standard ranking if Cohere fails (rate limits, key invalid, etc.)
            print(f"Warning: Cohere reranking failed. Falling back to default scoring. Error: {str(e)}")
            reranked_nodes = combined_nodes[:5]

        # 6. Map Child Hits to Parent Contexts
        # Hierarchical strategy mapping: return the wider 512-token parent context when a child matches.
        parent_nodes_with_score = []
        for node_with_score in reranked_nodes:
            node = node_with_score.node
            parent_rel = node.relationships.get(NodeRelationship.PARENT)
            
            if parent_rel and docstore.document_exists(parent_rel.node_id):
                parent_node = docstore.get_node(parent_rel.node_id)
                # Keep score from reranking child, wrap the parent node in NodeWithScore
                parent_nodes_with_score.append(
                    NodeWithScore(
                        node=parent_node,
                        score=node_with_score.score
                    )
                )
            else:
                # If no parent relation exists or lookup fails, return the child chunk itself
                parent_nodes_with_score.append(node_with_score)

        return parent_nodes_with_score[:5]
