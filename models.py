# models.py
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Enum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid as uuid_pkg

Base = declarative_base()


class ConversationMode(str, enum.Enum):
    OPEN_CHAT = "open_chat"
    GROUNDED_RAG = "grounded_rag"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=True)
    mode = Column(Enum(ConversationMode), nullable=False, default=ConversationMode.OPEN_CHAT)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    conversation_documents = relationship("ConversationDocument", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title}, mode={self.mode})>"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # CHANGED: metadata -> message_metadata
    sequence_number = Column(Integer, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)  # Original text content
    chunks = Column(JSON, nullable=True)  # Processed chunks with metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    conversation_documents = relationship("ConversationDocument", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class ConversationDocument(Base):
    """Join table for many-to-many relationship between conversations and documents"""
    __tablename__ = "conversation_documents"
    
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="conversation_documents")
    document = relationship("Document", back_populates="conversation_documents")
    
    def __repr__(self):
        return f"<ConversationDocument(conversation_id={self.conversation_id}, document_id={self.document_id})>"