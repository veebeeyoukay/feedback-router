# Feedback Router API Specification

## Base URL
```
https://api.itjen.ai/feedback
```

## Authentication
All endpoints require either:
- Bearer token in `Authorization` header
- Slack signature verification (for Slack webhook)

```bash
Authorization: Bearer sk_live_xxxxx
```

## Common Response Format

All successful responses return HTTP 200-201 with this format:
```json
{
  "success": true,
  "data": { },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:32:00Z"
  }
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": {
      "field": "contact.email",
      "reason": "required"
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:32:00Z"
  }
}
```

---

## POST /api/feedback/ingest

Ingest feedback from the website widget or external source.

### Request

```json
{
  "contact": {
    "email": "jane@example.com",
    "name": "Jane Doe"
  },
  "message": "I'm struggling with the new automation features. It's hard to understand how to set up workflows.",
  "channel": "website",
  "metadata": {
    "page_url": "https://itjen.ai/features",
    "user_agent": "Mozilla/5.0...",
    "source_campaign": "onboarding_email"
  }
}
```

### Query Parameters
- `async` (boolean, default: true) — Process classification/routing asynchronously
- `skip_dedup` (boolean, default: false) — Disable deduplication check

### Response

```json
{
  "success": true,
  "data": {
    "id": "fb_1711014720_a1b2c3",
    "status": "received",
    "processing_status": "queued",
    "estimated_response_time": "5-10 minutes"
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:32:00Z"
  }
}
```

### Error Cases

**400 Bad Request** — Missing required fields
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "message is required",
    "details": { "field": "message" }
  }
}
```

**409 Conflict** — Duplicate detected
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_DETECTED",
    "message": "Similar feedback received recently",
    "details": {
      "original_id": "fb_1711014600_xyz",
      "similarity_score": 0.92
    }
  }
}
```

---

## POST /api/feedback/slack

Handle Slack events (required for Slack integration).

### Usage
Configure this URL as your Slack request URL in the Slack App settings.

### Request Headers
```
X-Slack-Request-Timestamp: 1711014720
X-Slack-Signature: v0=5f0ee8ac2d7e1c3a2b4...
```

### Request Body (Events)

**Message posted in channel**:
```json
{
  "type": "event_callback",
  "event": {
    "type": "message",
    "text": "The new learning module is confusing",
    "user": "U1234SLACK",
    "channel": "C5678CHAN",
    "ts": "1711014720.000100"
  },
  "user_id": "U1234SLACK"
}
```

**Thread reply**:
```json
{
  "type": "event_callback",
  "event": {
    "type": "message",
    "text": "Can someone help me understand the settings?",
    "user": "U1234SLACK",
    "channel": "C5678CHAN",
    "thread_ts": "1711014720.000100",
    "ts": "1711014721.000200"
  }
}
```

### Response

All Slack requests must be acknowledged within 3 seconds with HTTP 200.

```json
{
  "success": true,
  "data": {
    "feedback_id": "fb_1711014720_slack",
    "processing_status": "queued"
  },
  "meta": {
    "request_id": "req_def456",
    "timestamp": "2026-03-19T14:32:00Z"
  }
}
```

---

## GET /api/feedback/:id

Retrieve a single feedback item with full classification and routing details.

### Parameters
- `:id` (string) — Feedback item ID (e.g., `fb_1711014720_a1b2c3`)

### Response

```json
{
  "success": true,
  "data": {
    "id": "fb_1711014720_a1b2c3",
    "version": "1.0",
    "intake": {
      "channel": "website",
      "timestamp": "2026-03-19T14:32:00Z",
      "contact": {
        "id": "c_550e8400",
        "identifier": "jane@example.com",
        "name": "Jane Doe",
        "type": "identified"
      }
    },
    "content": {
      "raw": "I'm struggling with the new automation features...",
      "normalized": "I'm struggling with the new automation features...",
      "language": "en",
      "word_count": 45
    },
    "classification": {
      "category": "feedback",
      "category_confidence": 0.89,
      "themes": [
        {
          "theme": "Learning Curve",
          "confidence": 0.92,
          "keywords_found": ["confusing", "understand", "setup"]
        },
        {
          "theme": "Workplace Productivity",
          "confidence": 0.68,
          "keywords_found": ["automation", "workflows"]
        }
      ],
      "sentiment": "negative",
      "sentiment_score": -0.45,
      "priority": 2,
      "classified_by": "classifier_agent_v1",
      "classified_at": "2026-03-19T14:33:15Z"
    },
    "routing": {
      "team": "product",
      "slack_channel": "C_PRODUCT_FEEDBACK",
      "response_tier": "faq_draft",
      "priority": "normal",
      "escalation_triggers_matched": [],
      "confidence_level": "high",
      "rule_id": "rule_003",
      "rule_explanation": "Learning Curve feedback routes to product team",
      "routed_at": "2026-03-19T14:34:02Z"
    },
    "response": {
      "status": "sent",
      "tier": "faq_draft",
      "content": "Thanks for sharing your feedback about the automation features...",
      "sent_at": "2026-03-19T14:35:45Z",
      "channel_response_id": "ts_12345.67890"
    },
    "metadata": {
      "dedup_key": "hash_xyz",
      "is_duplicate": false,
      "duplicate_of": null,
      "flags": [],
      "tags": ["automation", "ui_ux"],
      "company_doc_context": ["doc_automation_best_practices"]
    },
    "audit": {
      "created_at": "2026-03-19T14:32:00Z",
      "updated_at": "2026-03-19T14:35:45Z",
      "events": [
        {
          "type": "intake",
          "timestamp": "2026-03-19T14:32:00Z",
          "actor": "intake_agent",
          "details": {
            "dedup_check": "no_duplicate"
          }
        },
        {
          "type": "classify",
          "timestamp": "2026-03-19T14:33:15Z",
          "actor": "classifier_agent",
          "details": {
            "model_version": "v1",
            "processing_time_ms": 2100
          }
        },
        {
          "type": "route",
          "timestamp": "2026-03-19T14:34:02Z",
          "actor": "router_agent",
          "details": {
            "rule_matched": "rule_003",
            "evaluation_time_ms": 45
          }
        },
        {
          "type": "respond",
          "timestamp": "2026-03-19T14:35:45Z",
          "actor": "responder_agent",
          "details": {
            "response_generated_by": "faq_generator",
            "posting_channel": "slack"
          }
        }
      ]
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:36:00Z"
  }
}
```

### Error Cases

**404 Not Found**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Feedback item fb_invalid not found"
  }
}
```

---

## GET /api/feedback

List feedback items with filtering, sorting, and pagination.

### Query Parameters

**Filtering**:
- `channel` (string) — Filter by channel: `website`, `slack`
- `category` (string) — Filter by category: `bug`, `feature`, `feedback`, `complaint`
- `theme` (string) — Filter by theme: `Workplace Productivity`, `Career Security`, `Learning Curve`, `Privacy & Safety`, `Family & Personal Life`
- `sentiment` (string) — Filter by sentiment: `positive`, `neutral`, `negative`
- `status` (string) — Filter by status: `received`, `queued`, `classified`, `routed`, `sent`, `resolved`
- `priority` (string) — Filter by priority: `low`, `normal`, `high`, `critical`
- `team` (string) — Filter by assigned team: `engineering`, `product`, `support`, `leadership`
- `from_date` (ISO 8601) — Start of date range
- `to_date` (ISO 8601) — End of date range
- `contact_id` (string) — Filter by contact ID
- `flags` (string) — Filter by flags (comma-separated): `escalation`, `privacy_review`, `human_review`
- `has_response` (boolean) — Filter items with/without responses

**Sorting**:
- `sort_by` (string, default: `created_at`) — Field to sort by
- `sort_order` (string, default: `desc`) — `asc` or `desc`

**Pagination**:
- `page` (integer, default: 1) — Page number
- `limit` (integer, default: 20, max: 100) — Items per page

### Example Request

```bash
GET /api/feedback?theme=Learning%20Curve&status=resolved&from_date=2026-03-01&limit=50&sort_by=created_at&sort_order=desc
```

### Response

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "fb_1711014720_a1b2c3",
        "contact": {
          "id": "c_550e8400",
          "name": "Jane Doe",
          "email": "jane@example.com"
        },
        "content_preview": "I'm struggling with the new automation features...",
        "classification": {
          "category": "feedback",
          "themes": ["Learning Curve", "Workplace Productivity"],
          "sentiment": "negative",
          "priority": 2
        },
        "routing": {
          "team": "product",
          "response_tier": "faq_draft",
          "priority": "normal"
        },
        "response": {
          "status": "sent",
          "sent_at": "2026-03-19T14:35:45Z"
        },
        "created_at": "2026-03-19T14:32:00Z",
        "updated_at": "2026-03-19T14:35:45Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_items": 237,
      "total_pages": 12
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:36:00Z"
  }
}
```

---

## PATCH /api/feedback/:id

Update a feedback item (status, classification, routing).

### Parameters
- `:id` (string) — Feedback item ID

### Request Body

```json
{
  "response_status": "resolved",
  "classification": {
    "category": "bug",
    "priority": 1
  },
  "routing": {
    "team": "engineering",
    "response_tier": "human_only",
    "priority": "high"
  },
  "flags": ["escalation"],
  "notes": "Escalated due to duplicate bug reports"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "fb_1711014720_a1b2c3",
    "response_status": "resolved",
    "classification": {
      "category": "bug",
      "priority": 1
    },
    "routing": {
      "team": "engineering",
      "response_tier": "human_only",
      "priority": "high"
    },
    "updated_at": "2026-03-19T14:45:00Z"
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:45:00Z"
  }
}
```

### Error Cases

**409 Conflict** — Cannot update immutable fields:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_UPDATE",
    "message": "Field 'id' is immutable",
    "details": {
      "field": "id"
    }
  }
}
```

---

## GET /api/insights/trends

Retrieve trends across feedback items (themes, sentiment, categories over time).

### Query Parameters
- `from_date` (ISO 8601) — Start of date range
- `to_date` (ISO 8601) — End of date range
- `group_by` (string, default: `day`) — Grouping: `hour`, `day`, `week`, `month`
- `channel` (string) — Filter by channel

### Response

```json
{
  "success": true,
  "data": {
    "date_range": {
      "from": "2026-03-01T00:00:00Z",
      "to": "2026-03-19T23:59:59Z"
    },
    "total_feedback_items": 847,
    "theme_distribution": {
      "Workplace Productivity": {
        "count": 312,
        "percentage": 36.8,
        "trend": "up"
      },
      "Career Security": {
        "count": 198,
        "percentage": 23.4,
        "trend": "stable"
      },
      "Learning Curve": {
        "count": 187,
        "percentage": 22.1,
        "trend": "up"
      },
      "Privacy & Safety": {
        "count": 104,
        "percentage": 12.3,
        "trend": "down"
      },
      "Family & Personal Life": {
        "count": 46,
        "percentage": 5.4,
        "trend": "stable"
      }
    },
    "sentiment_distribution": {
      "positive": {
        "count": 245,
        "percentage": 28.9,
        "trend": "up"
      },
      "neutral": {
        "count": 412,
        "percentage": 48.6,
        "trend": "stable"
      },
      "negative": {
        "count": 190,
        "percentage": 22.4,
        "trend": "down"
      }
    },
    "category_distribution": {
      "feedback": 450,
      "feature": 201,
      "bug": 143,
      "complaint": 53
    },
    "response_metrics": {
      "items_with_response": 798,
      "response_rate": 0.942,
      "avg_response_time_seconds": 287
    },
    "timeline": [
      {
        "date": "2026-03-19",
        "feedback_count": 34,
        "avg_sentiment_score": 0.12,
        "top_theme": "Workplace Productivity",
        "top_category": "feedback"
      },
      {
        "date": "2026-03-18",
        "feedback_count": 42,
        "avg_sentiment_score": 0.05,
        "top_theme": "Learning Curve",
        "top_category": "feature"
      }
    ],
    "emerging_issues": [
      {
        "keyword": "automation",
        "frequency": 67,
        "theme": "Learning Curve",
        "sentiment_context": "mostly negative",
        "recommendation": "Create automation tutorial FAQ"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:36:00Z"
  }
}
```

---

## GET /api/health

System health check (no authentication required).

### Response

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2026-03-19T14:36:00Z",
    "services": {
      "database": {
        "status": "healthy",
        "response_time_ms": 12
      },
      "redis": {
        "status": "healthy",
        "response_time_ms": 5
      },
      "slack_api": {
        "status": "healthy",
        "response_time_ms": 234
      },
      "claude_api": {
        "status": "healthy",
        "response_time_ms": 1200
      }
    },
    "queue_status": {
      "classification_queue_length": 23,
      "routing_queue_length": 5,
      "response_queue_length": 8
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-19T14:36:00Z"
  }
}
```

---

## Error Codes Reference

| Code | HTTP | Meaning |
|------|------|---------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `DUPLICATE_DETECTED` | 409 | Similar feedback detected |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependency unavailable |

---

## Rate Limiting

All endpoints are rate limited:
- Unauthenticated: 10 requests/minute per IP
- Authenticated: 1000 requests/minute per API key
- Slack webhook: 60 requests/minute

Headers returned:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1711014900
```

---

## Pagination Best Practices

For large result sets, always paginate:

```bash
# First page
curl "https://api.itjen.ai/feedback?page=1&limit=50"

# Check pagination metadata
# If total_pages > 1, fetch remaining pages

# Subsequent pages
curl "https://api.itjen.ai/feedback?page=2&limit=50"
curl "https://api.itjen.ai/feedback?page=3&limit=50"
```

---

## Webhooks (Future)

The system will support event webhooks for real-time notifications:

```bash
POST /api/webhooks/subscribe

{
  "url": "https://your-app.com/feedback-webhook",
  "events": ["feedback.created", "feedback.classified", "feedback.routed", "response.sent"],
  "secret": "whsec_xxxxx"
}
```

Events will be signed with HMAC-SHA256.
