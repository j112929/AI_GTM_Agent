import os
import uuid
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from datetime import datetime, timezone
from backend.core.config import config
from backend.utils.logger import setup_logger

def get_utc_time():
    return datetime.now(timezone.utc).isoformat()

logger = setup_logger("RAG_Service")

class RAGService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RAGService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, collection_name: str = "gtm_knowledge_base"):
        if hasattr(self, 'initialized') and self.initialized:
            return
        
        self.mock_mode = config.MOCK_LLM
        
        if not self.mock_mode and config.OPENAI_API_KEY:
            try:
                self.persist_directory = os.path.join(os.getcwd(), "rag_storage")
                os.makedirs(self.persist_directory, exist_ok=True)
                
                # Create a persistent client
                self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
                
                # Use OpenAI Embeddings
                self.embedding_fn = OpenAIEmbeddings(
                    openai_api_key=config.OPENAI_API_KEY,
                    model="text-embedding-3-small"  # Cost-effective model
                )
                
                # Get or create collection
                self.collection = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"RAG Service initialized with collection '{collection_name}' at {self.persist_directory}")
                
            except Exception as e:
                logger.error(f"Failed to initialize RAG Service: {e}. Falling back to MOCK mode.")
                self.mock_mode = True
        else:
            logger.info("RAG Service initialized in MOCK mode (no API key or MOCK_LLM=True).")
            self.mock_mode = True
            
        self.initialized = True

    def add_documents(self, documents: List[str], metadatas: List[Dict] = None):
        """
        Add documents to the vector store.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Added {len(documents)} documents to RAG (Virtual).")
            return

        if not documents:
            return

        if metadatas is None:
            metadatas = [{"source": "unknown", "timestamp": get_utc_time()} for _ in documents]

        try:
            # Generate Embeddings
            embeddings = self.embedding_fn.embed_documents(documents)
            
            # Generate IDs
            ids = [str(uuid.uuid4()) for _ in documents]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Successfully added {len(documents)} documents to RAG.")
            
        except Exception as e:
            logger.error(f"Error adding documents to RAG: {e}")

    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """
        Query the knowledge base for relevant context.
        """
        if self.mock_mode:
            return [
                {
                    "content": "This is a mock knowledge base entry about our product features.",
                    "metadata": {"source": "mock_data", "relevance": 0.9}
                },
                {
                    "content": "Case Study: We helped Company X increase sales by 30% using AI agents.",
                    "metadata": {"source": "case_study_mock", "relevance": 0.8}
                }
            ]

        try:
            query_embedding = self.embedding_fn.embed_query(query_text)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            output = []
            if results and results.get("documents"):
                # Chroma returns list of lists
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                
                for doc, meta in zip(docs, metas):
                    output.append({
                        "content": doc,
                        "metadata": meta
                    })
            
            return output
            
        except Exception as e:
            logger.error(f"Error querying RAG: {e}")
            return []

# Singleton instance
rag_service = RAGService()
