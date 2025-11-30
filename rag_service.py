# rag_service.py
from typing import List, Dict
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import uuid
import PyPDF2
import io

from models import Document

logger = logging.getLogger(__name__)


class RAGService:
    """Service for document processing and retrieval (RAG)"""
    
    def __init__(self):
        self.CHUNK_SIZE = 500  # tokens per chunk
        self.CHUNK_OVERLAP = 50  # token overlap between chunks
        self.MAX_CHUNKS_TO_RETRIEVE = 5
    
    async def process_document(
        self,
        content: bytes,
        filename: str,
        content_type: str
    ) -> List[Dict]:
        """
        Process uploaded document into chunks
        
        Args:
            content: File content as bytes
            filename: Original filename
            content_type: MIME type
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Extract text based on file type
            if content_type == "application/pdf":
                text = self._extract_pdf_text(content)
            elif content_type == "text/plain":
                text = content.decode('utf-8', errors='ignore')
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Create chunks
            chunks = self._create_chunks(text)
            
            logger.info(f"Processed {filename}: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise Exception(f"Document processing failed: {str(e)}")
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise Exception(f"Failed to extract PDF text: {str(e)}")
    
    def _create_chunks(self, text: str) -> List[Dict]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full document text
        
        Returns:
            List of chunk dictionaries
        """
        # Estimate characters per token (rough approximation)
        chars_per_token = 4
        chunk_chars = self.CHUNK_SIZE * chars_per_token
        overlap_chars = self.CHUNK_OVERLAP * chars_per_token
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_chars
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "id": chunk_id,
                    "content": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "tokens": len(chunk_text) // chars_per_token
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = end - overlap_chars
        
        return chunks
    
    async def retrieve_context(
        self,
        query: str,
        document_ids: List[uuid.UUID],
        db: AsyncSession
    ) -> str:
        """
        Retrieve relevant context from documents for a query
        
        This is a simple keyword-based retrieval. In production, you would:
        1. Generate embeddings for the query
        2. Use vector similarity search
        3. Rank by semantic relevance
        
        Args:
            query: User's question/message
            document_ids: List of document IDs to search in
            db: Database session
        
        Returns:
            Formatted context string
        """
        try:
            # Fetch documents
            result = await db.execute(
                select(Document)
                .where(Document.id.in_(document_ids))
            )
            documents = result.scalars().all()
            
            if not documents:
                return "No documents found."
            
            # Simple keyword-based retrieval
            # Extract keywords from query (simplified)
            keywords = self._extract_keywords(query)
            
            # Score chunks based on keyword matches
            scored_chunks = []
            for doc in documents:
                if doc.chunks:
                    for chunk in doc.chunks:
                        score = self._calculate_relevance_score(
                            chunk["content"],
                            keywords
                        )
                        scored_chunks.append({
                            "content": chunk["content"],
                            "score": score,
                            "document": doc.filename,
                            "chunk_id": chunk["id"]
                        })
            
            # Sort by score and take top N
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            top_chunks = scored_chunks[:self.MAX_CHUNKS_TO_RETRIEVE]
            
            # Format context
            if not top_chunks or top_chunks[0]["score"] == 0:
                context = "No relevant information found in the documents."
            else:
                context_parts = []
                for i, chunk in enumerate(top_chunks, 1):
                    context_parts.append(
                        f"[Excerpt {i} from {chunk['document']}]:\n{chunk['content']}"
                    )
                context = "\n\n".join(context_parts)
            
            logger.info(f"Retrieved {len(top_chunks)} chunks for query")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return "Error retrieving document context."
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query (simplified)
        In production, use proper NLP techniques
        """
        # Remove common stop words
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "what",
            "when", "where", "who", "how", "why", "in", "on", "at", "to",
            "for", "of", "with", "from", "about", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me"
        }
        
        # Simple tokenization
        words = query.lower().split()
        keywords = [w.strip(".,!?;:") for w in words if w.lower() not in stop_words and len(w) > 2]
        
        return keywords
    
    def _calculate_relevance_score(self, chunk_text: str, keywords: List[str]) -> float:
        """
        Calculate relevance score based on keyword matches
        Simple TF approach (in production, use TF-IDF or embeddings)
        """
        chunk_lower = chunk_text.lower()
        score = 0
        
        for keyword in keywords:
            # Count occurrences
            count = chunk_lower.count(keyword.lower())
            score += count
        
        # Normalize by chunk length
        if len(chunk_text) > 0:
            score = score / (len(chunk_text) / 100)  # Per 100 chars
        
        return score