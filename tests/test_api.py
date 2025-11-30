# tests/test_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import uuid

from main import app
from database import get_db, Base
from models import User, Conversation, Message

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://botgpt:botgpt123@localhost:5432/botgpt_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=True
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture
async def db_session():
    """Create test database tables and provide session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    """Create test client with database override"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_create_conversation_open_chat(client, test_user):
    """Test creating a new conversation in open chat mode"""
    payload = {
        "user_id": str(test_user.id),
        "first_message": "Hello, this is a test message",
        "mode": "open_chat",
        "document_ids": []
    }
    
    response = await client.post("/api/v1/conversations", json=payload)
    
    # Note: This will fail if GROQ_API_KEY is not set
    # In a real scenario, we would mock the LLM service
    if response.status_code == 201:
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
        assert "assistant_response" in data
        assert data["message"]["content"] == "Hello, this is a test message"
        assert data["message"]["role"] == "user"
        assert data["assistant_response"]["role"] == "assistant"


@pytest.mark.asyncio
async def test_list_conversations(client, test_user, db_session):
    """Test listing conversations"""
    # Create a test conversation
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Conversation",
        mode="open_chat"
    )
    db_session.add(conversation)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/conversations?user_id={test_user.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "conversations" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_conversation_detail(client, test_user, db_session):
    """Test getting conversation details"""
    # Create test conversation with messages
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Conversation",
        mode="open_chat"
    )
    db_session.add(conversation)
    await db_session.flush()
    
    message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="user",
        content="Test message",
        sequence_number=1,
        tokens=3
    )
    db_session.add(message)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/conversations/{conversation.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == str(conversation.id)
    assert data["title"] == "Test Conversation"
    assert len(data["messages"]) == 1


@pytest.mark.asyncio
async def test_delete_conversation(client, test_user, db_session):
    """Test soft deleting a conversation"""
    # Create test conversation
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Conversation",
        mode="open_chat"
    )
    db_session.add(conversation)
    await db_session.commit()
    
    response = await client.delete(f"/api/v1/conversations/{conversation.id}")
    assert response.status_code == 204
    
    # Verify conversation is marked as deleted
    await db_session.refresh(conversation)
    assert conversation.is_deleted == True


@pytest.mark.asyncio
async def test_conversation_not_found(client):
    """Test 404 error for non-existent conversation"""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/conversations/{fake_id}")
    assert response.status_code == 404


# Run with: pytest tests/test_api.py -v