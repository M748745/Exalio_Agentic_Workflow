# Workflow Templates

Pre-built workflow templates demonstrating the Agentic Workflow Builder's capabilities.

## Available Templates

### 1. Smart Cache System (`01_smart_cache_system.json`)
**Difficulty:** Beginner
**Category:** Memory & Caching

Demonstrates intelligent caching with conditional logic:
- Checks cache before expensive operations
- Stores results for future requests (1 hour TTL)
- Reduces latency and API costs

**Use Cases:**
- API response caching
- Expensive computation optimization
- Rate limiting with cached results

**Nodes Used:** `cache_get`, `cache_set`, `if_else`, `ollama_llm`

---

### 2. RAG Q&A System (`02_rag_qa_system.json`)
**Difficulty:** Intermediate
**Category:** AI & Knowledge

Retrieval-Augmented Generation for intelligent Q&A:
- Store documents in vector database
- Semantic search for relevant context
- Generate informed answers using LLM

**Use Cases:**
- Document Q&A systems
- Internal knowledge bases
- Customer support automation
- Research assistance

**Nodes Used:** `vector_store`, `vector_search`, `ollama_llm`

**Requirements:** ChromaDB vector database

---

### 3. Multi-turn Chat Assistant (`03_multiturn_chat_assistant.json`)
**Difficulty:** Beginner
**Category:** Conversational AI

Conversational AI with memory:
- Maintains conversation history
- Provides contextual responses
- Remembers previous interactions

**Use Cases:**
- Customer support chatbots
- Personal AI assistants
- Interactive tutoring systems
- Conversational interfaces

**Nodes Used:** `context_get`, `context_append`, `ollama_llm`

---

### 4. Data Pipeline Workflow (`04_data_pipeline.json`)
**Difficulty:** Intermediate
**Category:** Data Processing

ETL pipeline with AI-powered transformation:
- Cache-first architecture (avoid reprocessing)
- LLM-based data transformation to JSON
- Python validation and formatting
- Dual export (JSON + CSV)
- 2-hour result caching

**Use Cases:**
- ETL pipelines for data warehousing
- API response transformation
- Log file parsing and structuring
- Data migration and format conversion
- Automated data quality checks

**Nodes Used:** `cache_get`, `cache_set`, `if_else`, `ollama_llm`, `python_code`, `file_write`

---

### 5. Smart Email Automation (`05_email_automation.json`)
**Difficulty:** Beginner
**Category:** Automation & Notifications

Intelligent email routing with sentiment analysis:
- Parallel LLM analysis (sentiment + priority)
- Conditional routing based on sentiment
- Manager escalation for negative feedback
- Auto-response generation
- CRM logging via context memory

**Use Cases:**
- Customer support email triage
- Automated feedback processing
- Help desk ticket routing
- Social media message management
- Community forum moderation

**Nodes Used:** `ollama_llm` (3x), `if_else`, `notification`, `context_append`

---

## How to Use Templates

### Option 1: Via API (Recommended)
```bash
# Import a template
curl -X POST http://localhost:5000/api/workflows/import \
  -H "Content-Type: application/json" \
  -d @templates/01_smart_cache_system.json

# List all templates
curl http://localhost:5000/api/templates/list
```

### Option 2: Manual Import
1. Open the React frontend at `http://localhost:3000`
2. Click "Import Workflow" button
3. Upload the JSON file
4. The workflow will appear in the canvas

### Option 3: Copy-Paste
1. Open the template JSON file
2. Copy the contents
3. In the frontend, use "Import from JSON" feature
4. Paste and load

---

## Template Structure

Each template is a JSON file with:

```json
{
  "id": "unique_id",
  "name": "Template Name",
  "description": "What it does",
  "category": "Category",
  "difficulty": "Beginner|Intermediate|Advanced",
  "tags": ["tag1", "tag2"],
  "nodes": [ /* ReactFlow nodes */ ],
  "edges": [ /* ReactFlow edges */ ],
  "metadata": {
    "requirements": ["Dependencies"],
    "useCases": ["Use case 1", "Use case 2"]
  }
}
```

---

## Requirements

### All Templates
- Ollama running locally with `llama3.2:3b` model
  ```bash
  ollama pull llama3.2:3b
  ```

### Vector-based Templates (RAG)
- ChromaDB (automatically initialized)
  ```bash
  pip install chromadb
  ```

### Optional
- Redis for production caching (development uses in-memory fallback)
  ```bash
  docker run -d -p 6379:6379 redis
  ```

---

## Coming Soon

- **Multi-Agent Research**: Parallel agent execution
- **Image Processing**: Vision → Analysis → Report
- **Scheduled Workflows**: Cron-based automation
- **API Integration**: REST → Transform → Database
- **Report Generation**: Data → Charts → PDF

---

## Creating Custom Templates

1. Build your workflow in the visual editor
2. Click "Export Workflow"
3. Save as JSON in this directory
4. Add metadata:
   - description, category, difficulty
   - tags, requirements, use cases
5. Submit a PR or use locally

---

## Support

Questions? Issues?
- Check the [main documentation](../WEEK1_STATUS.md)
- Review the [execution plan](../OPTION_C_EXECUTION_PLAN.md)
- Test with `test_memory_service.py`

**Version**: 1.0.0
**Last Updated**: 2026-09-12
