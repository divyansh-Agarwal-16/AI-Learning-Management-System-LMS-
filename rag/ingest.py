"""CLI document ingestion tool for the AI LMS RAG pipeline.

Accepts arguments for course context mapping and file locations, running
hierarchical ingestion and displaying progress metrics using tqdm.
"""

import sys
import os
import argparse
from pathlib import Path
from tqdm import tqdm

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.ingestion.ingest import DocumentIngestor


def main():
    parser = argparse.ArgumentParser(description="Ingest course study materials into the AI LMS RAG pipeline.")
    parser.add_argument(
        "--course_id",
        type=str,
        required=True,
        help="Target Course UUID mapping namespace context"
    )
    parser.add_argument(
        "--file_path",
        type=str,
        required=True,
        help="Path to the document file (PDF, TXT, MD) or YouTube URL"
    )
    parser.add_argument(
        "--file_type",
        type=str,
        required=True,
        choices=["pdf", "youtube", "txt", "md"],
        help="Type of file being ingested"
    )
    parser.add_argument(
        "--lesson_id",
        type=str,
        default=None,
        help="Optional Lesson UUID mapping context"
    )

    args = parser.parse_args()

    # Progress bar step-by-step tracking
    with tqdm(total=100, desc="Initializing Ingestion Pipeline") as pbar:
        # Step 1: Initialize database connections
        pbar.set_description("Connecting to Pinecone index...")
        try:
            ingestor = DocumentIngestor()
        except Exception as e:
            pbar.write(f"\n[ERROR] Connection failed: {str(e)}")
            sys.exit(1)
        pbar.update(20)

        # Step 2: Load document and check paths
        pbar.set_description(f"Loading document data: {args.file_path}...")
        if args.file_type != "youtube":
            path = Path(args.file_path)
            if not path.exists():
                pbar.write(f"\n[ERROR] File not found: {args.file_path}")
                sys.exit(1)
        pbar.update(25)

        # Step 3: Run parsing, embedding generation, and Pinecone database upsert
        pbar.set_description("Extracting text and running hierarchical chunking (parents 512, children 128)...")
        try:
            # Running the ingestion transaction
            pbar.update(15)  # Processing chunking
            
            pbar.set_description("Generating OpenAI embeddings and upserting child vectors to Pinecone...")
            leaf_count = ingestor.ingest(
                file_path_or_url=args.file_path,
                file_type=args.file_type,
                course_id=args.course_id,
                lesson_id=args.lesson_id
            )
            pbar.update(30)  # Database indexing
            
            # Step 4: Persisting database details
            pbar.set_description("Saving document store registries locally...")
            pbar.update(10)  # Persistence complete
            
        except Exception as e:
            pbar.write(f"\n[ERROR] Ingestion failed: {str(e)}")
            sys.exit(1)

        pbar.set_description("Ingestion completed successfully!")

    print(f"\n[SUCCESS] Successfully indexed {leaf_count} child chunks for course namespace 'course_{args.course_id}'.")


if __name__ == "__main__":
    main()
