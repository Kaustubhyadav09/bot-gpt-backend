# BOT GPT - Conversational AI Backend

[![CI/CD Pipeline](https://github.com/yourusername/bot-gpt-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/bot-gpt-backend/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade conversational AI backend with RAG (Retrieval-Augmented Generation) support, built with FastAPI, PostgreSQL, LangChain, and Groq API.

## 🚀 Features

- ✅ **Dual Conversation Modes**
  - Open Chat: General purpose conversations
  - Grounded RAG: Document-based conversations
  
- ✅ **Complete REST API**
  - Create, Read, Update, Delete conversations
  - Message history management
  - Document upload and processing
  
- ✅ **Intelligent Context Management**
  - Token-aware conversation history
  - Sliding window approach for long conversations
  - Cost optimization strategies
  
- ✅ **Document Processing (RAG)**
  - PDF and TXT file support
  - Automatic chunking with overlap
  - Keyword-based retrieval (expandable to vector search)
  
- ✅ **Production Ready**
  - Async/await throughout
  - Database connection pooling
  - Retry logic with exponential backoff
  - Comprehensive error handling
  - Docker containerization
  - CI/CD pipeline with GitHub Actions

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- Groq API Key ([Get one free here](https://console.groq.com/keys))

## 🛠️ Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/bot-gpt-backend.git
cd bot-gpt-backend
```

2. **Create environment file**
```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

3. **Start services**
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

4. **Access API documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Local Setup

1. **Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql

# macOS
brew install postgresql
```

2. **Create database**
```bash
psql -U postgres
CREATE DATABASE botgpt;
CREATE USER botgpt WITH PASSWORD 'botgpt123';
GRANT ALL PRIVILEGES ON DATABASE botgpt TO botgpt;
\q
```

3. **Install Python dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Set environment variables**
```bash
export DATABASE_URL="postgresql+asyncpg://botgpt:botgpt123@localhost:5432/botgpt"
export GROQ_API_KEY="your_groq_api_key_here"
```

5. **Run the application**
```bash
uvicorn main:app --reload
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Key Endpoints

#### 1. Create Conversation (Open Chat)
```http
POST /conversations
Content-Type: application/json

{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "first_message": "Explain quantum computing",
  "mode": "open_chat",
  "document_ids": []
}
```

#### 2. Create Conversation (RAG Mode)
```http
POST /conversations
Content-Type: application/json

{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "first_message": "What does the document say about revenue?",
  "mode": "grounded_rag",
  "document_ids": ["doc-uuid-1", "doc-uuid-2"]
}
```

#### 3. List Conversations
```http
GET /conversations?user_id={uuid}&page=1&limit=20
```

#### 4. Get Conversation Details
```http
GET /conversations/{conversation_id}
```

#### 5. Add Message to Conversation
```http
POST /conversations/{conversation_id}/messages
Content-Type: application/json

{
  "content": "Tell me more about that"
}
```

#### 6. Delete Conversation
```http
DELETE /conversations/{conversation_id}
```

#### 7. Upload Document
```http
POST /documents
Content-Type: multipart/form-data

file: [PDF or TXT file]
user_id: {uuid}
```

#### 8. List Documents
```http
GET /documents?user_id={uuid}
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           FastAPI Application           │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │   API   │  │ Service │  │  Data   │ │
│  │  Layer  │→ │  Layer  │→ │  Layer  │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└────────┬──────────────┬─────────────────┘
         │              │
         ▼              ▼
   ┌──────────┐   ┌──────────┐
   │PostgreSQL│   │Groq API  │
   │          │   │(LangChain)│
   └──────────┘   └──────────┘
```

### Project Structure
```
bot-gpt-backend/
├── main.py              # FastAPI application & routes
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic schemas
├── database.py          # Database configuration
├── llm_service.py       # LLM integration service
├── rag_service.py       # RAG document processing
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Multi-container setup
├── .env.example         # Environment variables template
├── .github/
│   └── workflows/
│       └── ci.yml       # CI/CD pipeline
└── tests/
    ├── __init__.py
    └── test_api.py      # Unit tests
```

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_api.py::test_create_conversation_open_chat -v
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `GROQ_API_KEY` | Groq API key for LLM access | Yes | - |
| `APP_ENV` | Application environment | No | development |
| `LOG_LEVEL` | Logging level | No | INFO |

### LLM Models

Available Groq models (configured in `llm_service.py`):
- `llama-3.1-70b-versatile` (default) - Best quality
- `llama-3.1-8b-instant` - Faster responses

## 📊 Database Schema

### Tables
- **users**: User accounts
- **conversations**: Chat sessions
- **messages**: Individual messages
- **documents**: Uploaded files
- **conversation_documents**: Links conversations to documents

### Relationships
```
User (1) ─── (N) Conversations (1) ─── (N) Messages
User (1) ─── (N) Documents
Conversation (N) ─── (N) Documents (via conversation_documents)
```

## 🚀 Deployment

### Using Docker

1. **Build image**
```bash
docker build -t botgpt:latest .
```

2. **Run container**
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="your_db_url" \
  -e GROQ_API_KEY="your_api_key" \
  botgpt:latest
```

### Production Considerations

1. **Use PostgreSQL connection pooling** (configure in `database.py`)
2. **Enable CORS** for specific origins
3. **Set up rate limiting** per user
4. **Use secrets management** (AWS Secrets Manager, HashiCorp Vault)
5. **Add monitoring** (Prometheus, Grafana)
6. **Set up logging** (ELK stack, CloudWatch)
7. **Use CDN** for document storage (S3, CloudFront)

## 🔐 Security

- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
- Environment variables for sensitive data
- CORS configuration
- File upload size limits (10MB)
- Allowed file types whitelist

## 📈 Scalability

### Current Bottlenecks
1. **Database**: Add read replicas, connection pooling
2. **LLM API**: Rate limiting, request queuing
3. **File Storage**: Move to object storage (S3)

### Scaling Strategies
- Horizontal scaling with load balancer
- Database sharding by user_id
- Redis caching for frequent queries
- Async task queue (Celery) for document processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style
- Use Black for formatting: `black .`
- Follow PEP 8 guidelines
- Add type hints where possible
- Write docstrings for functions

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [Groq](https://groq.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

## 📧 Contact

Your Name - your.email@example.com

Project Link: https://github.com/yourusername/bot-gpt-backend

---

**Built with ❤️ for BOT Consulting**