import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

class LMSQueryEngine:
    def __init__(self, index_name: str = "ai-lms"):
        self.index_name = index_name
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.index = None
        self._initialize_index()

    def _initialize_index(self):
        """Initialize the vector index connection."""
        if not self.api_key or not self.openai_key:
            print("Warning: PINECONE_API_KEY or OPENAI_API_KEY is not set.")
            return

        # Initialize Pinecone
        pc = Pinecone(api_key=self.api_key)
        
        # Connect to vector store
        pinecone_index = pc.Index(self.index_name)
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        
        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Load or create index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store, 
            storage_context=storage_context
        )
        print("LlamaIndex Pinecone VectorStore initialized.")

    def ingest_documents(self, directory_path: str):
        """Load and index documents from a directory."""
        if not self.index:
            print("Index not initialized. Cannot ingest documents.")
            return
            
        print(f"Loading documents from {directory_path}...")
        documents = SimpleDirectoryReader(directory_path).load_data()
        
        for doc in documents:
            self.index.insert(doc)
        print(f"Successfully ingested {len(documents)} documents.")

    def query(self, query_str: str) -> str:
        """Query the index for context-informed responses."""
        if not self.index:
            return "RAG Index is not initialized. Please configure API keys."
            
        query_engine = self.index.as_query_engine()
        response = query_engine.query(query_str)
        return str(response)

if __name__ == "__main__":
    # Test stub
    engine = LMSQueryEngine()
    print("RAG Pipeline modules successfully loaded.")
