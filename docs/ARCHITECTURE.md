# Feedback Router Architecture

## System Overview

The ItsJen.ai Feedback Router is a specialized feedback routing system designed for Gen X professionals (ages 40-60). It processes feedback from multiple channels, classifies it against five thematic areas, applies intelligent routing rules, and ensures consistent, empathetic responses.

### Core Values

- **Never leave someone hanging**: Every feedback item gets a response
- **Single source of truth**: Unified feedback schema across all channels
- **Intelligent classification**: ML-assisted thematic tagging with human review gates
- **Flexible routing**: Rule-based system that routes without code changes
- **Audit trail**: Complete visibility into how decisions were made

## 5-Step Pipeline

The feedback journey follows a deterministic 5-step pipeline:

### 1. Identify (Intake Agent)
- Receive feedback from channels (website, Slack, future email/tickets)
- Normalize data into unified schema
- Deduplicate near-identical feedback within 30 minutes
- Extract structured fields (channel, contact, sentiment markers)
- Store raw feedback for audit trail
- **Output**: Normalized feedback item with dedup flags

### 2. Listen (Classifier Agent)
- Analyze normalized feedback
- Assign primary category (bug, feature, general feedback, complaint)
- Tag all relevant themes (5-dimensional vector)
- Extract sentiment scores and emotional profile matches
- Link to contact record for personalization
- Flag privacy concerns or sensitive data
- **Output**: Enriched feedback with classifications and confidence scores

### 3. Classify (Classifier Agent continuation)
- Confidence threshold check
- High confidence (>0.85): Move to routing
- Medium confidence (0.6-0.85): Flag for secondary review, prepare human queue
- Low confidence (<0.6): Auto-queue for human classifier
- **Output**: Classification state document

### 4. Decide (Router Agent)
- Evaluate routing rules in order (150+ rule combinations possible)
- Consider escalation triggers (competitor mention, repeated contact, bug severity, etc.)
- Assign team/slack channel/queue
- Determine response tier (auto-ack, FAQ, draft, human-only)
- Set priorities and flags
- **Output**: Routing decision with reasoning

### 5. Close (Responder Agent → Concierge Agent)
- Generate appropriate response based on tier
- Post to original channel or via email
- Create Slack thread for human responders if needed
- Track response status and satisfaction
- **Output**: Feedback item marked complete with response metadata

## Agent Architecture

### Intake Agent
**Role**: Stateless normalizer that transforms heterogeneous channel input into a unified schema

**Responsibilities**:
- Channel adapters (website form, Slack events, future email/tickets)
- Extract: message body, sender, timestamp, channel metadata
- Deduplication logic (hash-based within 30-minute window)
- Contact identification (email, Slack user ID, anonymous)
- Flag: thread vs. standalone, contains files/attachments
- Data validation (required fields, format checks)

**Output Schema**:
```json
{
  "id": "fb_<timestamp>_<hash>",
  "intake_timestamp": "2026-03-19T14:32:00Z",
  "channel": "website|slack",
  "channel_metadata": { "slack_ts": "...", "user_id": "..." },
  "contact": {
    "identifier": "email@example.com|U1234SLACK",
    "name": "Jane Doe",
    "type": "identified|anonymous"
  },
  "message": {
    "raw": "...",
    "normalized": "..."
  },
  "dedup_key": "hash",
  "is_duplicate": false,
  "duplicate_of_id": null,
  "received_at": "2026-03-19T14:32:00Z"
}
```

### Classifier Agent
**Role**: Intelligent thematic classifier using Claude with structured output

**Responsibilities**:
- Category assignment (bug, feature, feedback, complaint)
- Sentiment analysis (positive, neutral, negative)
- Theme tagging: assign all relevant themes + confidence
- Emotional profile matching (benefit-seeking, concerned, reliability-focused, job-fearful)
- Contact ID linking (create if new)
- Privacy flagging (PII, data sensitivity)
- Confidence scoring per classification

**Thematic Dimensions**:
1. Workplace Productivity (efficiency, tools, workflows)
2. Career Security (employment risks, skills relevance)
3. Learning Curve (upskilling, tech adoption)
4. Privacy & Safety (data protection, compliance)
5. Family & Personal Life (work-life balance, burnout)

**Output Schema**:
```json
{
  "classification": {
    "category": "bug|feature|feedback|complaint",
    "category_confidence": 0.92,
    "themes": [
      {
        "theme": "Workplace Productivity",
        "confidence": 0.85,
        "keywords_found": ["automation", "efficiency"]
      },
      {
        "theme": "Career Security",
        "confidence": 0.61,
        "keywords_found": ["job security"]
      }
    ],
    "sentiment": {
      "primary": "negative",
      "score": -0.73
    },
    "emotional_profile": {
      "benefit_seeking": 0.6,
      "concerned": 0.8,
      "reliability_focused": 0.9,
      "job_fearful": 0.3
    },
    "priority": 1,
    "privacy_flags": []
  },
  "contact_id": "c_uuid",
  "classified_at": "2026-03-19T14:33:15Z"
}
```

### Router Agent
**Role**: Rule-based decision engine that determines next steps without human intervention for high-confidence items

**Responsibilities**:
- Load and evaluate routing rules (YAML-defined)
- Escalation trigger evaluation
- Confidence threshold checks
- Response tier determination
- Team assignment via mapping
- Flag for secondary review if needed
- Exception handling and fallback routing

**Rule Evaluation**:
- Sequential evaluation (rules have priority order)
- Condition matching (AND/OR logic on theme, sentiment, category, etc.)
- Action execution (assign_team, escalate, flag_human, set_response_tier)
- Audit trail (why this rule matched)

**Output Schema**:
```json
{
  "routing": {
    "team": "engineering|product|support|leadership",
    "slack_channel": "C123ABC",
    "response_tier": "auto_ack|faq_draft|complex_draft|human_only",
    "priority": "low|normal|high|critical",
    "escalation_triggers_matched": ["competitor_mention"],
    "confidence_level": "high|medium|low",
    "rule_id": "rule_008",
    "rule_explanation": "Bug with high priority matched escalation trigger"
  },
  "routed_at": "2026-03-19T14:34:02Z"
}
```

### Responder Agent
**Role**: Generates context-appropriate responses based on tier

**Responsibilities**:
- Generate acknowledgment messages (all tiers)
- Draft FAQ-based responses (tier: faq_draft)
- Draft complex responses with nuance (tier: complex_draft)
- Flag for human response (tier: human_only)
- Personalization (use contact name, reference theme context)
- Channel-specific formatting (Slack vs. email)
- Brand voice consistency

**4-Tier Response Model**:
1. **Auto-ACK**: Simple acknowledgment, no specific content ("Thanks for reaching out. We received your message on [theme].")
2. **FAQ Draft**: Pull from knowledge base, auto-send if high confidence
3. **Complex Draft**: AI-generated draft for human review (in Slack thread or async)
4. **Human-Only**: Queue for manual response (lost visitors, escalations, complaints)

### Concierge Agent
**Role**: Warm, empathetic front-line responder for ambiguous or off-topic feedback

**Responsibilities**:
- Detect "lost visitor" scenarios (feedback not fitting 5 themes)
- Offer warm redirection ("I'm not sure that's directly related to [topic], but I'd love to help...")
- Never say "that's not my department"
- Direct to appropriate resource (career coach, compliance, etc.)
- Escalate when needed with context
- Maintain empathetic tone across all interactions

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CHANNEL ADAPTERS                          │
│  (Website Widget) (Slack Events API) (Email/Tickets Queue)  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              INTAKE AGENT (Normalization)                    │
│  • Deduplication • Schema validation • Contact matching      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────┐
│      PostgreSQL: feedback_items       │
│      (raw + normalized)               │
└────────────────────────┬──────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           CLASSIFIER AGENT (Enrichment)                      │
│  • Category • Sentiment • Themes • Confidence • Priority     │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
  HIGH CONFIDENCE (>0.85)        MEDIUM/LOW CONFIDENCE (<0.85)
        │                                 │
        ▼                                 ▼
┌──────────────────────┐        ┌──────────────────────┐
│   ROUTER AGENT       │        │  HUMAN CLASSIFIER    │
│   (Routing Rules)    │        │  (Review Queue)      │
└──────────┬───────────┘        └──────────┬───────────┘
           │                               │
           │               ┌───────────────┘
           ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL: routing_decisions                   │
│              (team, channel, tier, priority)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
AUTO-ACK           FAQ/COMPLEX DRAFT      HUMAN QUEUE
    │                    │                    │
    └────────────────┬───┴────────────┬───────┘
                     │                │
                     ▼                ▼
          ┌──────────────────────────────────┐
          │  RESPONDER AGENT (Response Gen)  │
          │  • Draft/Generate/Post Messages  │
          └──────────────┬───────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
    CHANNEL POST            SLACK THREAD (Human)
    (Website/Email)         (Complex/Escalation)
```

## Tech Stack

### Backend
- **Framework**: FastAPI (async, type-safe)
- **Language**: Python 3.11+
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **API Client**: httpx (async HTTP)

### Async & Queueing
- **Queue Broker**: Redis
- **Task Queue**: Celery
- **Pattern**: Feedback → Redis queue → Celery worker → async processing

### Database & Storage
- **Primary**: PostgreSQL 15+ (normalized schema, immutable audit logs)
- **Cache**: Redis (session, rate limiting, classification cache)
- **External**: Google Drive (company docs for RAG)

### Slack Integration
- **Library**: slack-bolt (Python async)
- **Features**: Events API, Web API, Interactive Components
- **Handling**: Bolt middleware for verification, retry logic

### AI & ML
- **LLM**: Claude (via Anthropic API)
- **Structured Output**: Pydantic models + Claude function calling
- **Context**: Company docs via Google Drive integration

### Development & Testing
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Linting**: ruff
- **Type Checking**: mypy
- **CI/CD**: GitHub Actions
- **Logging**: structlog (structured, context-aware)

## Async Processing Model

All long-running operations are async and queue-driven:

1. **Immediate operations** (latency < 500ms):
   - Intake normalization
   - Dedup check
   - Data validation

2. **Queued operations** (latency < 5 seconds):
   - Classification (Claude call)
   - Routing decision (rule evaluation)
   - Response generation
   - Channel posting (Slack API, email)

**Queue Architecture**:
```python
# Feedback received → Redis task queue
redis_queue.enqueue('classify_feedback', feedback_id=fb_id, priority=1)

# Celery worker processes asynchronously
@celery_app.task
async def classify_feedback(feedback_id: str):
    feedback = db.get(feedback_id)
    classification = await claude.classify(feedback)
    db.update(feedback_id, classification)
    redis_queue.enqueue('route_feedback', feedback_id=fb_id)
```

## Unified Feedback Schema

All feedback items conform to this schema throughout the pipeline:

```json
{
  "id": "fb_<timestamp>_<hash>",
  "version": "1.0",

  "intake": {
    "channel": "website|slack",
    "timestamp": "2026-03-19T14:32:00Z",
    "contact": {
      "id": "c_uuid",
      "identifier": "email|slack_user_id",
      "name": "string",
      "type": "identified|anonymous"
    }
  },

  "content": {
    "raw": "original message as received",
    "normalized": "normalized text (grammar, format corrections)",
    "language": "en",
    "word_count": 150
  },

  "classification": {
    "category": "bug|feature|feedback|complaint",
    "category_confidence": 0.92,
    "themes": [
      {
        "theme": "Workplace Productivity",
        "confidence": 0.85
      }
    ],
    "sentiment": "positive|neutral|negative",
    "sentiment_score": -0.73,
    "priority": 1,
    "classified_by": "classifier_agent_v1",
    "classified_at": "2026-03-19T14:33:15Z"
  },

  "routing": {
    "team": "engineering|product|support|leadership",
    "slack_channel": "C123ABC",
    "response_tier": "auto_ack|faq_draft|complex_draft|human_only",
    "priority": "low|normal|high|critical",
    "routed_at": "2026-03-19T14:34:02Z",
    "rule_id": "rule_008"
  },

  "response": {
    "status": "pending|draft|sent|resolved",
    "tier": "auto_ack|faq_draft|complex_draft|human_only",
    "content": "...",
    "sent_at": "2026-03-19T14:35:45Z",
    "channel_response_id": "ts_12345.67890"
  },

  "metadata": {
    "dedup_key": "hash",
    "is_duplicate": false,
    "duplicate_of": null,
    "flags": ["escalation", "privacy_review"],
    "tags": ["competitor_mention"],
    "company_doc_context": ["doc_id_1", "doc_id_2"]
  },

  "audit": {
    "created_at": "2026-03-19T14:32:00Z",
    "updated_at": "2026-03-19T14:35:45Z",
    "events": [
      {
        "type": "intake|classify|route|respond|resolve",
        "timestamp": "...",
        "actor": "agent_name",
        "details": {}
      }
    ]
  }
}
```

## Integration with Google Drive

The system integrates with Google Drive for company documentation:

```python
# On system startup
google_drive_client.download_company_docs()  # Store in local cache
build_vector_index(docs)  # For semantic search

# During classification
relevant_docs = vector_search(feedback_content, top_k=3)
context = "\n".join([doc.content for doc in relevant_docs])
classification = claude.classify(feedback, context=context)
```

**Benefits**:
- Real-time policy/documentation context
- Consistent tone with company docs
- References to official resources in responses
- Reduced hallucination in responses

## System Resilience

### Failure Handling
- **Classification failure**: Route to human review queue
- **Routing failure**: Default team assignment + escalate
- **Response posting failure**: Retry with exponential backoff (max 3 attempts)
- **Database failure**: Circuit breaker pattern, graceful degradation

### Monitoring & Observability
- Structured logging with context (feedback_id, contact_id, agent_name)
- Metrics: classification latency, routing latency, response rate, success rate
- Health check endpoint: database, Redis, Slack API connectivity
- Dead letter queue for failed items

## Security & Privacy

- All feedback stored in PostgreSQL with encryption at rest
- Slack credentials in environment variables only
- PII flagged and handled per privacy policy
- Audit trail for all decisions (immutable events)
- Rate limiting on API endpoints (per IP, per contact)
- Request validation and sanitization

## Extensibility

The architecture supports adding:
1. **New channels**: Implement channel adapter interface
2. **New routing rules**: Add YAML definitions (no code changes)
3. **New themes**: Update classification model and scoring
4. **New response tiers**: Extend responder agent logic
5. **New integrations**: Redis queue supports arbitrary workers
