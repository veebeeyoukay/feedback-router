# Feedback Router: Operations Runbook

## Common Scenarios & Responses

### Scenario 1: Lost Visitor (Ambiguous Feedback)

**Trigger**: Classification confidence <0.60 OR feedback doesn't fit any theme

**Example**: "Hi, I'm looking for career coaching resources"

**What Happens**:
1. Intake Agent normalizes the message
2. Classifier Agent can't confidently categorize
3. Router Agent flags for human review
4. Concierge Agent provides warm response

**Response Template** (Concierge Agent):
```
Hi [name], thanks for reaching out. I want to make sure you get the right help.

It sounds like you're looking for [specific topic]. While that's not directly something
we handle, I think [related resource] might help. Have you tried [suggestion]?

If I've misunderstood what you're looking for, let me know and I'll point you in
the right direction.

Best, [Team]
```

**Manual Handling**:
1. Support team reviews in human queue
2. Classify feedback intent
3. Respond with appropriate resource or escalation
4. Add to knowledge base if pattern emerges

---

### Scenario 2: Enterprise Escalation

**Trigger**:
- Customer is enterprise account (>1000 employees)
- Multiple related complaints
- High-priority feature request from key account

**Example**: "We need [feature] for [use case]. This is blocking our deployment to 500 users."

**What Happens**:
1. Classification detects: feature request + career/productivity theme + negative sentiment
2. Routing rule matches escalation trigger
3. System flags for leadership + engineering
4. Creates Slack thread with escalation context

**Manual Handling**:

Step 1: Create escalation ticket
```bash
curl -X POST https://api.itjen.ai/admin/escalations \
  -H "Authorization: Bearer sk_admin_xxxxx" \
  -d '{
    "feedback_id": "fb_1711014720_a1b2c3",
    "escalation_level": "enterprise",
    "assigned_to": "VP Product",
    "deadline": "2026-03-21T12:00:00Z",
    "context": "Enterprise customer, 500 user deployment blocked"
  }'
```

Step 2: Post in Slack channel (C_LEADERSHIP_ESCALATIONS)
```
🚨 ENTERPRISE ESCALATION

Customer: Acme Corp (10,000 seat license)
Contact: john@acmecorp.com
Urgency: Deployment blocked for 500 users
Request: [Feature X]

Response needed by: Tomorrow 12pm

Thread: [Slack thread URL]
```

Step 3: Assign directly to product lead
- @product_lead "Can you review this enterprise request?"
- Set deadline
- Link to customer success notes

Step 4: Follow up
- Respond to customer within 4 hours with: status, timeline, next steps
- Daily standup mention until resolved
- Post resolution back to customer

---

### Scenario 3: Competitor Mention

**Trigger**: Feedback mentions competitor by name OR uses specific competitor terminology

**Examples**:
- "CompetitorX does this much better"
- "We looked at CompetitorX but chose you because..."
- "You're way better than CompetitorX"

**What Happens**:
1. Classifier detects keyword match (configured competitor list)
2. System adds "competitor_mention" flag
3. Router escalates to leadership immediately
4. No auto-response; queued for human

**Manual Handling**:

Step 1: Classify sentiment
- Positive ("better than competitor"): Opportunity signal
- Negative ("competitor is better"): Threat signal
- Neutral (comparison): Research opportunity

Step 2: Respond appropriately

**If Positive** (we won):
```
Hi [name], thanks for choosing us! We're honored you considered [Competitor].
We'd love to know what made you choose ItsJen. Would you have 15 minutes
for a quick call? You could help shape our product roadmap.

[Calendar link]
```

**If Negative** (competitor winning):
```
Hi [name], we appreciate the feedback. [Competitor] is a good product.
We'd love to understand what we're missing for your use case.

Could we schedule a 30-minute call with our product team to discuss?
We're committed to competing on value for Gen X professionals.

[Calendar link]
```

Step 3: Document learnings
- Add to competitive intelligence doc
- Share with product in standup
- Adjust roadmap if pattern emerges

Step 4: Escalate if needed
- If customer considering switching: escalate to customer success
- If product concern: escalate to VP Product
- If multiple mentions: add to quarterly planning

---

### Scenario 4: Repeat Contact (Serial Complainer or Super Fan)

**Trigger**: contact.repeat_count >= 3

**Example**: Jane has submitted 5 pieces of feedback in 2 weeks

**What Happens**:
1. System detects repeat contact
2. Routing rule "Escalate Repeat Contacts" matches
3. Response tier bumped to human_only
4. Leadership notified

**Manual Handling**:

Step 1: Understand the pattern
```bash
# View all feedback from this contact
curl "https://api.itjen.ai/api/feedback?contact_id=c_550e8400"

# Look for:
# - All negative sentiment? (complainer)
# - All positive? (power user/brand advocate)
# - Mixed with escalating? (problem user)
# - Decreasing sentiment? (satisfaction declining)
```

Step 2: Assess customer health

**If Serial Complainer** (high negative, multiple complaints):
```
Response Template:

Hi [name], we've noticed you've raised several concerns recently.
We want to make sure we're addressing what matters to you.

Would you be open to a call with our team? We'd like to:
1. Understand your top 3 issues
2. Explain what we're doing to address similar concerns
3. Get your input on our roadmap

This feedback is valuable, and we want to make sure it translates into improvements.

[Calendar link]
```

Action Items:
- Schedule call with product/support lead
- Prioritize their issues in roadmap
- Assign account owner
- Weekly check-ins

**If Super Fan** (high positive, frequent engagement):
```
Response Template:

[name], we LOVE your enthusiasm for ItsJen! Your feedback has been incredibly
helpful in shaping our product.

We'd love to deepen our relationship. Would you be interested in:
- Beta testing new features?
- Joining our Gen X professionals advisory board?
- Sharing your story as a case study?

Let's hop on a call to explore!

[Calendar link]
```

Action Items:
- Offer beta access
- Invite to advisory board
- Develop case study
- Provide VIP support

Step 3: Set up account management
- Assign dedicated contact person
- Increase response SLA (4 hours → 1 hour)
- Monthly check-ins
- Quarterly business review

---

## Troubleshooting Guide

### Issue: Classification Errors (Wrong Category)

**Symptom**: Feedback classified as "feature" but it's actually a "bug"

**Diagnosis**:
```bash
# Get the feedback item
curl "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3"

# Check classification.category and confidence
# If confidence <0.75, consider human review first
```

**Solution**:

**If Confidence High (>0.85)**: Likely data quality issue, not system issue
- Review feedback text for ambiguity
- Consider if classifier interpretation is actually correct
- Escalate to team lead only if disagree with interpretation

**If Confidence Medium (0.60-0.85)**: System hesitation; manual review is appropriate
- Manually reclassify via API:
```bash
curl -X PATCH "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" \
  -H "Authorization: Bearer sk_xxxxx" \
  -d '{
    "classification": {
      "category": "bug",
      "priority": 1
    }
  }'
```

**If Pattern Emerges**: Retrain classifier
```bash
# Add to training set
python scripts/add_training_example.py \
  --feedback_id "fb_1711014720_a1b2c3" \
  --correct_category "bug" \
  --reason "User describes system crash, not feature request"

# Retrain
python scripts/train_classifier.py --update-model
```

### Issue: Routing Failures (Wrong Team)

**Symptom**: Feedback routes to Support but should go to Engineering

**Diagnosis**:
```bash
# Check routing decision
curl "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" | jq '.routing'

# Check which rule matched
# output: "rule_id": "rule_003"
# Check if rule is correct for this content
```

**Solution**:

**Option 1: Manual Reroute (One-time)**
```bash
curl -X PATCH "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" \
  -H "Authorization: Bearer sk_xxxxx" \
  -d '{
    "routing": {
      "team": "engineering",
      "slack_channel": "C_ENGINEERING_FEEDBACK",
      "priority": "high"
    }
  }'
```

**Option 2: Fix Routing Rule (Systematic)**

If multiple items being misrouted:
1. Identify common pattern (certain category, theme, sentiment)
2. Update routing rule priority/conditions
3. Reload rules: `curl -X POST http://localhost:8000/admin/reload-rules`
4. Monitor impact

Example:
```yaml
# BEFORE: Rule 003 catches all Learning Curve feedback
rule_id: rule_003
conditions:
  - field: classification.themes
    operator: includes_any
    value: ["Learning Curve"]
actions:
  - type: assign_team
    value: support

# AFTER: Add condition to exclude bugs (engineer-level learning)
rule_id: rule_003
conditions:
  - field: classification.themes
    operator: includes_any
    value: ["Learning Curve"]
  - field: classification.category
    operator: not_equals
    value: "bug"
actions:
  - type: assign_team
    value: support
```

### Issue: Slack Integration Not Working

**Symptom**: Messages posted in #feedback aren't being processed

**Diagnosis**:

```bash
# 1. Check if Slack events are reaching the webhook
curl -X GET http://localhost:8000/api/health | jq '.services.slack_api'

# 2. Check recent Slack webhook requests (if logging enabled)
tail -f logs/slack_webhook.log

# 3. Verify Slack app tokens
python scripts/test_slack_connection.py

# 4. Check if bot is in the feedback channel
# In Slack: /invite @ItsJen to #feedback
```

**Solution**:

**Token Expired**:
```bash
# Regenerate in Slack app settings
# OAuth & Permissions → Reinstall to Workspace
# Update environment variable
export SLACK_BOT_TOKEN=xoxb-new-token

# Restart bot
systemctl restart feedback-router
```

**Webhook URL Wrong**:
```bash
# Update in Slack app settings
# Event Subscriptions → Request URL
# Should be: https://your-domain.com/api/feedback/slack

# Test endpoint
curl -X POST https://your-domain.com/api/feedback/slack \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"xyz"}'
```

**Bot Not in Channel**:
```bash
# In Slack, run command
/invite @ItsJen Feedback

# Or add bot to channel via settings
```

**Too Many Errors**:
```bash
# Check error rate
curl "https://api.itjen.ai/admin/slack/errors?last_hours=1"

# If error rate >5%, page on-call engineer
# Common causes:
# - Rate limiting (check Slack rate limit docs)
# - Missing scopes (add scopes in Slack app settings)
# - Database connection failures
# - Celery worker down
```

### Issue: Classification Queue Backlog

**Symptom**: Feedback taking >30 minutes to classify

**Diagnosis**:
```bash
# Check queue depth
curl http://localhost:8000/api/health | jq '.queue_status'

# Check worker status
celery -A src.celery_app inspect active

# Check Redis memory
redis-cli info memory
```

**Solution**:

**Add More Workers** (immediate):
```bash
# Spin up additional Celery worker
celery -A src.celery_app worker --loglevel=info --hostname=worker2@%h

# Scale horizontally in Kubernetes
kubectl scale deployment feedback-router-worker --replicas=4
```

**Optimize Classification** (long-term):
```python
# Enable classification caching
CLASSIFICATION_CACHE_TTL=604800  # 1 week

# Reduce model inference time
# Use faster model: claude-3-5-haiku (if acceptable)
# or use model caching/quantization
```

**Flush Low-Priority Items** (emergency):
```bash
# If queue critically backed up, deprioritize low-priority items
# This will delay non-urgent feedback processing
curl -X POST http://localhost:8000/admin/queue/deprioritize-low-priority
```

---

## Dead Letter Queue Monitoring

Feedback items that fail multiple times are moved to Dead Letter Queue (DLQ).

### Checking DLQ

```bash
# Get DLQ length
curl http://localhost:8000/admin/dlq/size

# List DLQ items
curl http://localhost:8000/admin/dlq/items?limit=20

# Get details on specific item
curl http://localhost:8000/admin/dlq/fb_1711014720_a1b2c3
```

### Handling DLQ Items

**Step 1: Understand the failure**
```json
{
  "feedback_id": "fb_1711014720_a1b2c3",
  "failed_stage": "classification",
  "error": "Claude API timeout after 3 retries",
  "last_attempt": "2026-03-19T15:32:00Z",
  "attempt_count": 4,
  "original_error_log": "..."
}
```

**Step 2: Determine if transient or permanent**
- **Transient** (network error, rate limit): Retry
- **Permanent** (malformed data, API key invalid): Fix and replay

**Step 3: Take action**

```bash
# Retry specific item
curl -X POST http://localhost:8000/admin/dlq/fb_1711014720_a1b2c3/retry

# Retry all items in DLQ
curl -X POST http://localhost:8000/admin/dlq/retry-all

# Permanently fail and notify user
curl -X POST http://localhost:8000/admin/dlq/fb_1711014720_a1b2c3/fail-permanently \
  -d '{"notification": "true", "reason": "API malfunction"}'

# Remove from DLQ without action
curl -X DELETE http://localhost:8000/admin/dlq/fb_1711014720_a1b2c3
```

### DLQ Alerts

```yaml
- name: "DLQ Size > 10"
  query: "dlq_size > 10"
  severity: warning
  action: "Page on-call + check API status"

- name: "DLQ Size > 50"
  query: "dlq_size > 50"
  severity: critical
  action: "Page VP Engineering + investigate"

- name: "DLQ Item Not Retried After 24h"
  query: "max(item.age) > 24h"
  severity: warning
  action: "Email #ops channel"
```

---

## Manual Classification/Rerouting

When classification or routing is incorrect, you can manually correct it.

### Manual Classification

```bash
# View current classification
curl "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" | jq '.classification'

# Update classification
curl -X PATCH "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" \
  -H "Authorization: Bearer sk_admin_xxxxx" \
  -d '{
    "classification": {
      "category": "bug",
      "themes": [
        {"theme": "Workplace Productivity", "confidence": 0.8},
        {"theme": "Learning Curve", "confidence": 0.3}
      ],
      "priority": 1
    }
  }'

# This triggers re-routing automatically
```

### Manual Rerouting

```bash
# View current routing
curl "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" | jq '.routing'

# Update routing
curl -X PATCH "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3" \
  -H "Authorization: Bearer sk_admin_xxxxx" \
  -d '{
    "routing": {
      "team": "engineering",
      "slack_channel": "C_ENGINEERING",
      "response_tier": "complex_draft",
      "priority": "high",
      "escalation_triggers_matched": ["potential_bug"]
    }
  }'

# This queues new response generation if tier changed
```

### Audit Trail

All manual changes are logged with:
- Who made the change
- When
- What changed (before/after)
- Reason (optional)

```bash
# View change history
curl "https://api.itjen.ai/api/feedback/fb_1711014720_a1b2c3/audit"

# Output includes all modifications to this feedback item
```

---

## Weekly Operations Checklist

Every Monday 9am:

- [ ] Check DLQ size (should be <5)
- [ ] Review escalations from last week (any patterns?)
- [ ] Check classification error rate (should be <2%)
- [ ] Review repeat complainers (any churning at risk?)
- [ ] Check API performance metrics (latency, error rate)
- [ ] Database backup verification (last backup <24h old)
- [ ] Review Slack bot errors (if any)
- [ ] Update runbook with new scenarios/lessons learned

**Tool**:
```bash
python scripts/weekly_ops_check.py --generate-report
# Outputs: weekly_ops_report_[date].md
```

---

## Escalation Contacts

| Scenario | Primary | Secondary | Time Limit |
|----------|---------|-----------|-----------|
| Lost Visitor (ambiguous) | Support Lead | Concierge Agent | 4 hours |
| Enterprise Request | VP Product | VP Sales | 4 hours |
| Competitor Mention | VP Product | CEO | 2 hours |
| Security/Privacy Issue | Head of Security | Legal | 1 hour |
| System Outage | VP Engineering | On-Call Engineer | immediate |
| Bug Report (critical) | Engineering Lead | VP Product | 2 hours |
| DLQ Backlog >50 items | VP Engineering | On-Call | immediate |
| API Performance Degradation | VP Engineering | On-Call | immediate |

---

## Post-Incident Review Template

When something goes wrong:

```markdown
# Post-Incident Review: [Incident Name]

## Timeline
- **Start**: 2026-03-19T14:32:00Z
- **Detection**: 2026-03-19T14:45:00Z (13 minutes)
- **Resolution**: 2026-03-19T15:20:00Z (48 minutes)
- **Duration**: 48 minutes

## Impact
- Feedback items affected: 247
- Response time impacted: 13 minutes
- Customers notified: 3

## Root Cause
[What actually happened]

## Contributing Factors
[Why the system didn't catch this]

## Immediate Actions Taken
- [Action 1]
- [Action 2]

## Permanent Fixes
- [Fix 1] - Owner: X - ETA: Date
- [Fix 2] - Owner: Y - ETA: Date

## Monitoring Improvements
- [Alert to add]
- [Metric to track]

## Process Improvements
- [Runbook update needed]
- [Training topic]
```

Post in #incidents channel + distribute to team
