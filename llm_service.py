# llm_service.py
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

class LLMService:
    """Service for handling LLM interactions via Groq API"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        # Initialize Groq client with LangChain
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name="llama-3.1-8b-instant",  # or "llama-3.1-8b-instant" for faster responses
            temperature=0.7,
            max_tokens=2000,
            timeout=30,
            max_retries=3
        )
        
        # Token limits
        self.MAX_CONTEXT_TOKENS = 7000
        self.SYSTEM_PROMPT_TOKENS = 200
        self.RESERVED_RESPONSE_TOKENS = 2000
        
        self.system_prompt = """You are BOT GPT, a helpful and intelligent AI assistant. 
You provide clear, accurate, and concise responses. When you don't know something, 
you admit it honestly. You are friendly, professional, and aim to be as helpful as possible."""
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Rule of thumb: ~4 characters = 1 token
        """
        return max(1, len(text) // 4)
    
    def prepare_messages(self, messages: List[Dict[str, str]], max_history: int = 20) -> List:
        """
        Prepare messages for LLM, ensuring token limits
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_history: Maximum number of messages to include
        
        Returns:
            List of LangChain message objects
        """
        # Take last N messages to stay within context window
        recent_messages = messages[-max_history:] if len(messages) > max_history else messages
        
        # Convert to LangChain message objects
        langchain_messages = [SystemMessage(content=self.system_prompt)]
        
        for msg in recent_messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
        
        return langchain_messages
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        conversation_id: str = None
    ) -> str:
        """
        Generate response for open chat mode
        
        Args:
            messages: Conversation history
            conversation_id: Optional conversation ID for logging
        
        Returns:
            Generated response text
        """
        try:
            logger.info(f"Generating response for conversation {conversation_id}")
            
            # Prepare messages
            langchain_messages = self.prepare_messages(messages)
            
            # Calculate approximate token usage
            total_tokens = sum(self.estimate_tokens(str(msg.content)) for msg in langchain_messages)
            logger.info(f"Estimated input tokens: {total_tokens}")
            
            # Check if we're within limits
            if total_tokens > self.MAX_CONTEXT_TOKENS:
                logger.warning(f"Token count {total_tokens} exceeds limit, truncating history")
                # Reduce history if needed
                langchain_messages = self.prepare_messages(messages, max_history=10)
            
            # Generate response
            response = await self.llm.ainvoke(langchain_messages)
            
            logger.info(f"Response generated successfully for conversation {conversation_id}")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise Exception(f"LLM service error: {str(e)}")
    
    async def generate_rag_response(
        self,
        messages: List[Dict[str, str]],
        context: str,
        conversation_id: str = None
    ) -> str:
        """
        Generate response for RAG mode with document context
        
        Args:
            messages: Conversation history
            context: Retrieved context from documents
            conversation_id: Optional conversation ID for logging
        
        Returns:
            Generated response text
        """
        try:
            logger.info(f"Generating RAG response for conversation {conversation_id}")
            
            # Create RAG-specific system prompt
            rag_system_prompt = f"""{self.system_prompt}

You have access to the following information from the user's documents:

CONTEXT:
{context}

Please answer the user's question based primarily on this context. If the answer 
is not in the context, you may use your general knowledge but indicate that the 
information is not from the provided documents."""
            
            # Prepare messages with RAG context
            langchain_messages = [SystemMessage(content=rag_system_prompt)]
            
            # Add conversation history (keep it shorter for RAG to preserve context space)
            recent_messages = messages[-10:] if len(messages) > 10 else messages
            for msg in recent_messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            # Calculate tokens
            total_tokens = sum(self.estimate_tokens(str(msg.content)) for msg in langchain_messages)
            logger.info(f"Estimated RAG input tokens: {total_tokens}")
            
            # Generate response
            response = await self.llm.ainvoke(langchain_messages)
            
            logger.info(f"RAG response generated successfully for conversation {conversation_id}")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            raise Exception(f"RAG service error: {str(e)}")
    
    def check_token_limit(self, messages: List[Dict[str, str]]) -> bool:
        """
        Check if messages are within token limit
        
        Returns:
            True if within limit, False otherwise
        """
        total_tokens = sum(
            self.estimate_tokens(msg["content"]) 
            for msg in messages
        )
        return total_tokens < self.MAX_CONTEXT_TOKENS