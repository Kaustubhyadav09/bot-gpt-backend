# main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete as sql_delete
from typing import List, Optional
import uuid
from datetime import datetime
import logging

from database import get_db, init_db
from models import User, Conversation, Message, Document, ConversationDocument
from schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
    MessageCreate,
    MessageResponse,
    DocumentUpload,
    DocumentResponse,
    HealthResponse
)
from llm_service import LLMService
from rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="BOT GPT API",
    description="Conversational AI Backend with RAG Support",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
rag_service = RAGService()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    logger.info("Database initialized successfully")


@app.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        await db.execute(select(1))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "llm_api": "available",
        "timestamp": datetime.utcnow()
    }


# ============ CONVERSATION ENDPOINTS ============

@app.post("/api/v1/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new conversation with the first message
    
    Supports two modes:
    - open_chat: General conversation without documents
    - grounded_rag: Conversation grounded in provided documents
    """
    try:
        # Verify user exists (simplified - in production, use proper auth)
        user_result = await db.execute(
            select(User).where(User.id == data.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # Create user if doesn't exist (for demo purposes)
            user = User(id=data.user_id, username=f"user_{data.user_id}", email=f"{data.user_id}@example.com")
            db.add(user)
            await db.commit()
        
        # Create conversation
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=data.user_id,
            title=data.first_message[:50] + "..." if len(data.first_message) > 50 else data.first_message,
            mode=data.mode
        )
        db.add(conversation)
        
        # Associate documents if RAG mode
        if data.mode == "grounded_rag" and data.document_ids:
            for doc_id in data.document_ids:
                conv_doc = ConversationDocument(
                    conversation_id=conversation.id,
                    document_id=doc_id
                )
                db.add(conv_doc)
        
        # Create user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="user",
            content=data.first_message,
            sequence_number=1,
            tokens=llm_service.estimate_tokens(data.first_message)
        )
        db.add(user_message)
        
        await db.commit()
        await db.refresh(conversation)
        
        # Generate LLM response
        if data.mode == "open_chat":
            assistant_content = await llm_service.generate_response(
                messages=[{"role": "user", "content": data.first_message}],
                conversation_id=str(conversation.id)
            )
        else:
            # RAG mode - retrieve context from documents
            context = await rag_service.retrieve_context(
                query=data.first_message,
                document_ids=data.document_ids,
                db=db
            )
            assistant_content = await llm_service.generate_rag_response(
                messages=[{"role": "user", "content": data.first_message}],
                context=context,
                conversation_id=str(conversation.id)
            )
        
        # Create assistant message
        assistant_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_content,
            sequence_number=2,
            tokens=llm_service.estimate_tokens(assistant_content)
        )
        db.add(assistant_message)
        
        # Update conversation token count
        conversation.token_count = user_message.tokens + assistant_message.tokens
        
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
        
        return {
            "conversation_id": conversation.id,
            "message": {
                "id": user_message.id,
                "role": user_message.role,
                "content": user_message.content,
                "tokens": user_message.tokens,
                "created_at": user_message.created_at
            },
            "assistant_response": {
                "id": assistant_message.id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "tokens": assistant_message.tokens,
                "created_at": assistant_message.created_at
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@app.get("/api/v1/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user_id: uuid.UUID = Query(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """List all conversations for a user with pagination"""
    try:
        # Count total conversations
        count_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_deleted == False)
        )
        total = count_result.scalar()
        
        # Fetch conversations with last message
        offset = (page - 1) * limit
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_deleted == False)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        # Fetch message counts and last messages
        conversations_data = []
        for conv in conversations:
            # Get message count
            msg_count_result = await db.execute(
                select(func.count(Message.id))
                .where(Message.conversation_id == conv.id)
            )
            msg_count = msg_count_result.scalar()
            
            # Get last message
            last_msg_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.sequence_number.desc())
                .limit(1)
            )
            last_msg = last_msg_result.scalar_one_or_none()
            
            conversations_data.append({
                "id": conv.id,
                "title": conv.title,
                "mode": conv.mode,
                "message_count": msg_count,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "last_message": last_msg.content[:100] if last_msg else ""
            })
        
        return {
            "conversations": conversations_data,
            "total": total,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed conversation with all messages"""
    try:
        # Fetch conversation
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.is_deleted == False)
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Fetch messages
        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.asc())
        )
        messages = msg_result.scalars().all()
        
        # Fetch associated documents if RAG mode
        documents = []
        if conversation.mode == "grounded_rag":
            doc_result = await db.execute(
                select(Document)
                .join(ConversationDocument)
                .where(ConversationDocument.conversation_id == conversation_id)
            )
            documents = doc_result.scalars().all()
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "mode": conversation.mode,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "token_count": conversation.token_count,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "tokens": msg.tokens,
                    "created_at": msg.created_at,
                    "metadata": msg.message_metadata
                }
                for msg in messages
            ],
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "created_at": doc.created_at
                }
                for doc in documents
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")


@app.post("/api/v1/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message_to_conversation(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new message to existing conversation and get LLM response"""
    try:
        # Verify conversation exists
        conv_result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.is_deleted == False)
        )
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get message count for sequence number
        msg_count_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        msg_count = msg_count_result.scalar()
        
        # Create user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="user",
            content=data.content,
            sequence_number=msg_count + 1,
            tokens=llm_service.estimate_tokens(data.content)
        )
        db.add(user_message)
        
        # Fetch conversation history (last 10 message pairs = 20 messages)
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.desc())
            .limit(20)
        )
        history_messages = list(reversed(history_result.scalars().all()))
        
        # Format history for LLM
        formatted_history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
        formatted_history.append({"role": "user", "content": data.content})
        
        # Generate LLM response
        if conversation.mode == "open_chat":
            assistant_content = await llm_service.generate_response(
                messages=formatted_history,
                conversation_id=str(conversation_id)
            )
        else:
            # RAG mode - get document IDs
            doc_result = await db.execute(
                select(ConversationDocument.document_id)
                .where(ConversationDocument.conversation_id == conversation_id)
            )
            doc_ids = [row[0] for row in doc_result.all()]
            
            # Retrieve context
            context = await rag_service.retrieve_context(
                query=data.content,
                document_ids=doc_ids,
                db=db
            )
            
            assistant_content = await llm_service.generate_rag_response(
                messages=formatted_history,
                context=context,
                conversation_id=str(conversation_id)
            )
        
        # Create assistant message
        assistant_message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            sequence_number=msg_count + 2,
            tokens=llm_service.estimate_tokens(assistant_content)
        )
        db.add(assistant_message)
        
        # Update conversation
        conversation.token_count += user_message.tokens + assistant_message.tokens
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)
        
        return {
            "user_message": {
                "id": user_message.id,
                "role": user_message.role,
                "content": user_message.content,
                "tokens": user_message.tokens,
                "created_at": user_message.created_at
            },
            "assistant_response": {
                "id": assistant_message.id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "tokens": assistant_message.tokens,
                "created_at": assistant_message.created_at
            },
            "conversation_token_count": conversation.token_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@app.delete("/api/v1/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a conversation"""
    try:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation.is_deleted = True
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


# ============ DOCUMENT ENDPOINTS (RAG Support) ============

@app.post("/api/v1/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document for RAG"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "text/plain"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: PDF, TXT"
            )
        
        # Read file content
        content = await file.read()
        
        # Process document
        chunks = await rag_service.process_document(
            content=content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # Create document record
        document = Document(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=file.filename,
            content=content.decode('utf-8', errors='ignore') if file.content_type == "text/plain" else None,
            chunks=chunks
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "chunks_created": len(chunks),
            "created_at": document.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@app.get("/api/v1/documents")
async def list_documents(
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """List all documents for a user"""
    try:
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        documents = result.scalars().all()
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "chunk_count": len(doc.chunks) if doc.chunks else 0,
                    "created_at": doc.created_at
                }
                for doc in documents
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)