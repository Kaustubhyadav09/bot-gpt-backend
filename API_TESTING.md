# BOT GPT API Testing Guide

This guide provides step-by-step instructions for testing all API endpoints using cURL, Postman, or any HTTP client.

## Setup

1. Ensure the API is running at `http://localhost:8000`
2. Have a valid user UUID ready (you can generate one: `python -c "import uuid; print(uuid.uuid4())"`)

## Test Sequence

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "llm_api": "available",
  "timestamp": "2025-01-15T10:00:00.000Z"
}
```

---

### 2. Create a New Conversation (Open Chat Mode)

```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "first_message": "Hello! Can you explain what artificial intelligence is?",
    "mode": "open_chat",
    "document_ids": []
  }'
```

**Expected Response:**
```json
{
  "conversation_id": "uuid-here",
  "message": {
    "id": "uuid",
    "role": "user",
    "content": "Hello! Can you explain what artificial intelligence is?",
    "tokens": 10,
    "created_at": "2025-01-15T10:00:00.000Z"
  },
  "assistant_response": {
    "id": "uuid",
    "role": "assistant",
    "content": "Artificial intelligence (AI) is...",
    "tokens": 150,
    "created_at": "2025-01-15T10:00:02.000Z"
  }
}
```

**Save the `conversation_id` for the next steps!**

---

### 3. List All Conversations

```bash
curl "http://localhost:8000/api/v1/conversations?user_id=3fa85f64-5717-4562-b3fc-2c963f66afa6&page=1&limit=20"
```

**Expected Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "Hello! Can you explain what artificial...",
      "mode": "open_chat",
      "message_count": 2,
      "created_at": "2025-01-15T10:00:00.000Z",
      "updated_at": "2025-01-15T10:00:02.000Z",
      "last_message": "Artificial intelligence (AI) is..."
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

---

### 4. Get Conversation Details

```bash
curl http://localhost:8000/api/v1/conversations/{CONVERSATION_ID}
```

Replace `{CONVERSATION_ID}` with the actual ID from step 2.

**Expected Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Hello! Can you explain...",
  "mode": "open_chat",
  "created_at": "2025-01-15T10:00:00.000Z",
  "updated_at": "2025-01-15T10:00:02.000Z",
  "token_count": 160,
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Hello! Can you explain what artificial intelligence is?",
      "tokens": 10,
      "created_at": "2025-01-15T10:00:00.000Z",
      "metadata": null
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Artificial intelligence (AI) is...",
      "tokens": 150,
      "created_at": "2025-01-15T10:00:02.000Z",
      "metadata": null
    }
  ],
  "documents": []
}
```

---

### 5. Add Message to Conversation

```bash
curl -X POST http://localhost:8000/api/v1/conversations/{CONVERSATION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are some real-world applications of AI?"
  }'
```

**Expected Response:**
```json
{
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "What are some real-world applications of AI?",
    "tokens": 9,
    "created_at": "2025-01-15T10:05:00.000Z"
  },
  "assistant_response": {
    "id": "uuid",
    "role": "assistant",
    "content": "AI has numerous real-world applications including...",
    "tokens": 180,
    "created_at": "2025-01-15T10:05:03.000Z"
  },
  "conversation_token_count": 349
}
```

---

### 6. Upload a Document (for RAG)

Create a test text file first:
```bash
echo "This is a test document about machine learning. Machine learning is a subset of AI." > test_doc.txt
```

Then upload:
```bash
curl -X POST "http://localhost:8000/api/v1/documents?user_id=3fa85f64-5717-4562-b3fc-2c963f66afa6" \
  -F "file=@test_doc.txt"
```

**Expected Response:**
```json
{
  "document_id": "uuid",
  "filename": "test_doc.txt",
  "chunks_created": 1,
  "created_at": "2025-01-15T10:10:00.000Z"
}
```

**Save the `document_id`!**

---

### 7. List Documents

```bash
curl "http://localhost:8000/api/v1/documents?user_id=3fa85f64-5717-4562-b3fc-2c963f66afa6"
```

**Expected Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "test_doc.txt",
      "chunk_count": 1,
      "created_at": "2025-01-15T10:10:00.000Z"
    }
  ]
}
```

---

### 8. Create RAG Conversation

```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "first_message": "What does the document say about machine learning?",
    "mode": "grounded_rag",
    "document_ids": ["YOUR_DOCUMENT_ID_HERE"]
  }'
```

**Expected Response:**
The assistant will answer based on the uploaded document content.

---

### 9. Delete Conversation

```bash
curl -X DELETE http://localhost:8000/api/v1/conversations/{CONVERSATION_ID}
```

**Expected Response:**
Status 204 No Content (no body)

---

## Postman Collection

### Import Instructions

1. Open Postman
2. Click "Import" button
3. Select "Raw text"
4. Paste the JSON collection below
5. Click "Import"

### Collection JSON

```json
{
  "info": {
    "name": "BOT GPT API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "type": "string"
    },
    {
      "key": "user_id",
      "value": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "type": "string"
    },
    {
      "key": "conversation_id",
      "value": "",
      "type": "string"
    },
    {
      "key": "document_id",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/health",
          "host": ["{{base_url}}"],
          "path": ["health"]
        }
      }
    },
    {
      "name": "Create Conversation (Open Chat)",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test(\"Status is 201\", function () {",
              "    pm.response.to.have.status(201);",
              "});",
              "pm.test(\"Save conversation_id\", function () {",
              "    var jsonData = pm.response.json();",
              "    pm.collectionVariables.set(\"conversation_id\", jsonData.conversation_id);",
              "});"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": \"{{user_id}}\",\n  \"first_message\": \"Hello! Explain quantum computing\",\n  \"mode\": \"open_chat\",\n  \"document_ids\": []\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/conversations",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "conversations"]
        }
      }
    },
    {
      "name": "List Conversations",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/v1/conversations?user_id={{user_id}}&page=1&limit=20",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "conversations"],
          "query": [
            {"key": "user_id", "value": "{{user_id}}"},
            {"key": "page", "value": "1"},
            {"key": "limit", "value": "20"}
          ]
        }
      }
    },
    {
      "name": "Get Conversation Detail",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/v1/conversations/{{conversation_id}}",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "conversations", "{{conversation_id}}"]
        }
      }
    },
    {
      "name": "Add Message",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"content\": \"Tell me more about quantum entanglement\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/conversations/{{conversation_id}}/messages",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "conversations", "{{conversation_id}}", "messages"]
        }
      }
    },
    {
      "name": "Upload Document",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test(\"Save document_id\", function () {",
              "    var jsonData = pm.response.json();",
              "    pm.collectionVariables.set(\"document_id\", jsonData.document_id);",
              "});"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "file",
              "type": "file",
              "src": "/path/to/your/file.txt"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/api/v1/documents?user_id={{user_id}}",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "documents"],
          "query": [{"key": "user_id", "value": "{{user_id}}"}]
        }
      }
    },
    {
      "name": "List Documents",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/v1/documents?user_id={{user_id}}",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "documents"],
          "query": [{"key": "user_id", "value": "{{user_id}}"}]
        }
      }
    },
    {
      "name": "Delete Conversation",
      "request": {
        "method": "DELETE",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/v1/conversations/{{conversation_id}}",
          "host": ["{{base_url}}"],
          "path": ["api", "v1", "conversations", "{{conversation_id}}"]
        }
      }
    }
  ]
}
```

---

## Testing Tips

1. **Use Variables**: Replace UUIDs with your actual values
2. **Check Responses**: Verify HTTP status codes match expected values
3. **Test Error Cases**: Try invalid UUIDs, missing fields, etc.
4. **Monitor Logs**: Check Docker logs: `docker-compose logs -f api`
5. **Database Inspection**: Connect to DB: `docker exec -it botgpt_db psql -U botgpt`

---

## Common Issues

### Issue 1: "Connection refused"
- **Solution**: Ensure API is running: `docker-compose ps`

### Issue 2: "GROQ_API_KEY not set"
- **Solution**: Check `.env` file has valid API key

### Issue 3: "Database connection failed"
- **Solution**: Verify PostgreSQL is running and credentials are correct

### Issue 4: "Document upload fails"
- **Solution**: Check file size (<10MB) and type (PDF/TXT only)

---

## Automated Testing Script

```bash
#!/bin/bash
# test_api.sh - Quick API smoke test

BASE_URL="http://localhost:8000"
USER_ID="3fa85f64-5717-4562-b3fc-2c963f66afa6"

echo "1. Testing health check..."
curl -s $BASE_URL/health | jq

echo -e "\n2. Creating conversation..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"first_message\":\"Hello\",\"mode\":\"open_chat\",\"document_ids\":[]}")

CONV_ID=$(echo $RESPONSE | jq -r '.conversation_id')
echo "Conversation ID: $CONV_ID"

echo -e "\n3. Listing conversations..."
curl -s "$BASE_URL/api/v1/conversations?user_id=$USER_ID" | jq

echo -e "\n4. Getting conversation detail..."
curl -s $BASE_URL/api/v1/conversations/$CONV_ID | jq

echo -e "\n✅ All tests passed!"
```

Run with: `bash test_api.sh`