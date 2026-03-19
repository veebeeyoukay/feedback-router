# Feedback Router: Routing Rules Documentation

## Overview

Routing rules determine how feedback flows through the system — which team owns it, what response tier it receives, and when it should be escalated. Rules are defined in YAML and evaluated in order without requiring code changes.

## Rule Syntax

Each routing rule follows this structure:

```yaml
rule_id: rule_001
name: "Bug Reports to Engineering"
description: "High-priority bugs auto-route to engineering team"
enabled: true
priority: 1

conditions:
  - field: classification.category
    operator: equals
    value: "bug"
  - field: classification.priority
    operator: gte
    value: 1

actions:
  - type: assign_team
    value: engineering
  - type: assign_channel
    value: "C_ENGINEERING_FEEDBACK"
  - type: set_response_tier
    value: faq_draft
  - type: set_priority
    value: high

metadata:
  created_at: "2026-03-01T00:00:00Z"
  created_by: "admin@itjen.ai"
```

## Condition Fields and Operators

### Field Reference

**Classification Fields**:
- `classification.category` (string) — `bug`, `feature`, `feedback`, `complaint`
- `classification.priority` (integer) — 0-5 (lower = higher priority)
- `classification.sentiment` (string) — `positive`, `neutral`, `negative`
- `classification.sentiment_score` (number) — -1.0 to 1.0
- `classification.themes` (array) — Theme names like `Workplace Productivity`
- `classification.category_confidence` (number) — 0.0 to 1.0

**Contact Fields**:
- `contact.type` (string) — `identified`, `anonymous`
- `contact.is_repeat` (boolean) — Has submitted feedback before
- `contact.repeat_count` (integer) — Number of previous submissions

**Metadata Fields**:
- `metadata.channel` (string) — `website`, `slack`
- `metadata.is_duplicate` (boolean)
- `metadata.has_escalation_flag` (boolean)
- `metadata.contains_pii` (boolean)

**Content Fields**:
- `content.word_count` (integer) — Message length
- `content.has_attachments` (boolean)

### Operators

| Operator | Type | Example |
|----------|------|---------|
| `equals` | String | `category equals bug` |
| `not_equals` | String | `sentiment not_equals positive` |
| `contains` | String | `message contains "crash"` |
| `not_contains` | String | `message not_contains "thanks"` |
| `in` | String[] | `channel in [website, slack]` |
| `not_in` | String[] | `team not_in [support, qa]` |
| `gt` | Number | `priority gt 2` |
| `gte` | Number | `priority gte 2` |
| `lt` | Number | `sentiment_score lt -0.5` |
| `lte` | Number | `sentiment_score lte 0.0` |
| `between` | Number range | `word_count between 10 100` |
| `is_true` | Boolean | `is_duplicate is_true` |
| `is_false` | Boolean | `is_duplicate is_false` |
| `includes_any` | Array | `themes includes_any ["Career Security", "Privacy & Safety"]` |
| `includes_all` | Array | `themes includes_all ["Learning Curve", "Privacy & Safety"]` |
| `matches_regex` | Regex | `message matches_regex "(\bcrash\b|\berror\b)"` |

### Condition Logic

By default, all conditions must match (AND logic):

```yaml
conditions:
  - field: classification.category
    operator: equals
    value: "bug"
  - field: classification.priority
    operator: gte
    value: 1
  # Both conditions must be true
```

For OR logic, use condition groups:

```yaml
conditions:
  - group: "severity_check"
    logic: OR
    items:
      - field: classification.priority
        operator: gte
        value: 0
      - field: metadata.has_escalation_flag
        operator: is_true
```

## Action Types

| Action | Value | Effect |
|--------|-------|--------|
| `assign_team` | `engineering`, `product`, `support`, `leadership` | Route to team |
| `assign_channel` | Slack channel ID | Post to specific channel |
| `set_response_tier` | `auto_ack`, `faq_draft`, `complex_draft`, `human_only` | Set response level |
| `set_priority` | `low`, `normal`, `high`, `critical` | Set priority |
| `add_flag` | Flag name | Add operational flag |
| `escalate` | Boolean | Trigger escalation |
| `send_notification` | Contact list | Notify specific users |
| `skip_response` | Boolean | Don't auto-respond |
| `add_tag` | Tag name | Add metadata tag |

## Default Routing Rules

### Rule 001: Bug Reports to Engineering

```yaml
rule_id: rule_001
name: "Bug Reports to Engineering"
description: "Route critical and high-priority bugs immediately to engineering"
enabled: true
priority: 1

conditions:
  - field: classification.category
    operator: equals
    value: "bug"
  - field: classification.priority
    operator: gte
    value: 1

actions:
  - type: assign_team
    value: engineering
  - type: assign_channel
    value: "C_ENGINEERING_FEEDBACK"
  - type: set_response_tier
    value: faq_draft
  - type: set_priority
    value: high
```

### Rule 002: Feature Requests to Product

```yaml
rule_id: rule_002
name: "Feature Requests to Product"
description: "Route all feature requests to product team"
enabled: true
priority: 2

conditions:
  - field: classification.category
    operator: equals
    value: "feature"

actions:
  - type: assign_team
    value: product
  - type: assign_channel
    value: "C_PRODUCT_FEEDBACK"
  - type: set_response_tier
    value: faq_draft
  - type: set_priority
    value: normal
```

### Rule 003: Learning Curve Feedback to Support

```yaml
rule_id: rule_003
name: "Learning Curve Themes to Support"
description: "Route Learning Curve feedback to support team for FAQ expansion"
enabled: true
priority: 3

conditions:
  - field: classification.themes
    operator: includes_any
    value: ["Learning Curve"]

actions:
  - type: assign_team
    value: support
  - type: assign_channel
    value: "C_SUPPORT_FEEDBACK"
  - type: set_response_tier
    value: faq_draft
  - type: set_priority
    value: normal
```

### Rule 004: Escalate Repeat Complainers

```yaml
rule_id: rule_004
name: "Escalate Repeat Complainers"
description: "Flag for leadership review if someone has complained 3+ times"
enabled: true
priority: 4

conditions:
  - field: classification.category
    operator: equals
    value: "complaint"
  - field: contact.repeat_count
    operator: gte
    value: 3

actions:
  - type: escalate
    value: true
  - type: send_notification
    value: ["leadership@itjen.ai"]
  - type: set_priority
    value: critical
  - type: add_flag
    value: "repeat_complainer"
  - type: set_response_tier
    value: human_only
```

### Rule 005: Escalate Competitor Mentions

```yaml
rule_id: rule_005
name: "Escalate Competitor Mentions"
description: "Flag and escalate any mention of competitors"
enabled: true
priority: 5

conditions:
  - field: content
    operator: matches_regex
    value: "(?i)(competitor1|competitor2|competing_platform)"
  - field: metadata.channel
    operator: equals
    value: "slack"

actions:
  - type: escalate
    value: true
  - type: send_notification
    value: ["leadership@itjen.ai"]
  - type: add_flag
    value: "competitor_mention"
  - type: set_priority
    value: critical
  - type: set_response_tier
    value: human_only
```

### Rule 006: Privacy & Safety Issues to Leadership

```yaml
rule_id: rule_006
name: "Privacy & Safety Escalation"
description: "Immediately escalate any Privacy & Safety themed feedback"
enabled: true
priority: 6

conditions:
  - field: classification.themes
    operator: includes_any
    value: ["Privacy & Safety"]
  - field: classification.sentiment
    operator: equals
    value: "negative"

actions:
  - type: escalate
    value: true
  - type: assign_team
    value: leadership
  - type: send_notification
    value: ["ceo@itjen.ai", "legal@itjen.ai"]
  - type: set_priority
    value: critical
  - type: set_response_tier
    value: human_only
  - type: add_flag
    value: "privacy_escalation"
```

### Rule 007: Career Security + Negative Sentiment

```yaml
rule_id: rule_007
name: "Career Security Concerns"
description: "Career Security + negative sentiment requires human response"
enabled: true
priority: 7

conditions:
  - field: classification.themes
    operator: includes_any
    value: ["Career Security"]
  - field: classification.sentiment
    operator: equals
    value: "negative"

actions:
  - type: set_response_tier
    value: human_only
  - type: add_flag
    value: "career_concern"
  - type: send_notification
    value: ["support@itjen.ai"]
  - type: set_priority
    value: high
```

## Confidence Thresholds

The classification system produces confidence scores (0.0 to 1.0) for each prediction. Routing behavior depends on confidence:

### High Confidence (> 0.85)

- **Condition**: Classification confidence exceeds 85%
- **Behavior**: Apply routing rules immediately, auto-respond if tier allows
- **Example**: Clear bug report with 92% confidence

**Rule Application**:
```yaml
rule_id: rule_auto_high_confidence
name: "High Confidence Auto-Route"
conditions:
  - field: classification.category_confidence
    operator: gt
    value: 0.85
actions:
  - type: skip_human_review
    value: true
```

### Medium Confidence (0.6 to 0.85)

- **Condition**: Classification confidence between 60-85%
- **Behavior**: Apply routing rules, set response tier, but flag for human secondary review
- **Example**: Feedback mentioning career concerns but unclear intent

**Rule Application**:
```yaml
rule_id: rule_medium_confidence
name: "Medium Confidence Flag for Review"
conditions:
  - field: classification.category_confidence
    operator: between
    value: [0.6, 0.85]
actions:
  - type: set_response_tier
    value: faq_draft
  - type: add_flag
    value: "secondary_review_needed"
  - type: send_notification
    value: ["classifier@itjen.ai"]
```

### Low Confidence (< 0.6)

- **Condition**: Classification confidence below 60%
- **Behavior**: Route to human classifier queue, do not auto-respond
- **Example**: Ambiguous message that could fit multiple categories

**Rule Application**:
```yaml
rule_id: rule_low_confidence
name: "Low Confidence - Human Classification"
conditions:
  - field: classification.category_confidence
    operator: lt
    value: 0.6
actions:
  - type: assign_team
    value: support
  - type: set_response_tier
    value: human_only
  - type: add_flag
    value: "classification_review"
  - type: send_notification
    value: ["support@itjen.ai"]
```

## Fallback Behavior

If no rules match or all conditions fail:

```yaml
rule_id: rule_default_fallback
name: "Default Fallback Routing"
description: "Catch-all for unmatched feedback"
enabled: true
priority: 999

conditions: []  # No conditions = always matches if reached

actions:
  - type: assign_team
    value: support
  - type: assign_channel
    value: "C_GENERAL_FEEDBACK"
  - type: set_response_tier
    value: human_only
  - type: set_priority
    value: normal
  - type: add_flag
    value: "unmatched_pattern"
  - type: send_notification
    value: ["support@itjen.ai"]
```

**Fallback Logic**:
1. Evaluate all enabled rules in priority order
2. If a rule matches all conditions, apply its actions and stop
3. If no rule matches, apply default fallback
4. Never drop feedback; always route somewhere

## Rule Evaluation Order

Rules are evaluated in priority order (lower priority number = evaluated first):

```
Priority 1: Bug Reports to Engineering
Priority 2: Feature Requests to Product
Priority 3: Learning Curve Feedback to Support
Priority 4: Escalate Repeat Complainers
Priority 5: Escalate Competitor Mentions
Priority 6: Privacy & Safety Issues to Leadership
Priority 7: Career Security + Negative Sentiment
Priority 999: Default Fallback
```

**Evaluation Stops**: Once a rule matches, evaluation stops and its actions are applied. To have multiple rules apply, design rules to be mutually exclusive or use the same priority.

## Adding Rules Without Code

### Step 1: Create YAML Rule

Edit `/config/routing_rules.yaml`:

```yaml
- rule_id: rule_008
  name: "New Rule Name"
  description: "What this rule does"
  enabled: true
  priority: 8

  conditions:
    - field: classification.category
      operator: equals
      value: "feedback"

  actions:
    - type: assign_team
      value: support
    - type: set_response_tier
      value: faq_draft
```

### Step 2: Reload Configuration

```bash
# Development
curl -X POST http://localhost:8000/admin/reload-rules

# Production (requires admin API key)
curl -X POST https://api.itjen.ai/admin/reload-rules \
  -H "Authorization: Bearer sk_admin_xxxxx"
```

### Step 3: Monitor Impact

Track the new rule's effectiveness:

```bash
# Get rule statistics
curl "https://api.itjen.ai/admin/rules/rule_008/stats"
```

## Modifying Existing Rules

Update the YAML definition and reload:

```yaml
# Before
rule_id: rule_002
priority: 2
conditions:
  - field: classification.category
    operator: equals
    value: "feature"

# After (added minimum confidence requirement)
rule_id: rule_002
priority: 2
conditions:
  - field: classification.category
    operator: equals
    value: "feature"
  - field: classification.category_confidence
    operator: gte
    value: 0.75
```

Then reload: `curl -X POST http://localhost:8000/admin/reload-rules`

## Rule Testing

Test rules before deployment:

```bash
# Test rule against hypothetical feedback
curl -X POST http://localhost:8000/admin/test-rule \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "rule_008",
    "feedback": {
      "category": "feature",
      "priority": 1,
      "themes": ["Workplace Productivity"],
      "sentiment": "neutral"
    }
  }'

# Response
{
  "matched": true,
  "actions": [
    {"type": "assign_team", "value": "support"},
    {"type": "set_response_tier", "value": "faq_draft"}
  ]
}
```

## Rule Audit Log

All rule changes are logged:

```bash
# View rule change history
curl "https://api.itjen.ai/admin/rules/audit-log?rule_id=rule_002"

# Response shows: rule_id, change_type, old_value, new_value, changed_by, changed_at
```

## Best Practices

1. **Specificity**: Design rules to be as specific as possible to avoid over-routing
2. **Priority Order**: Place high-impact rules (escalations) at lower priority numbers
3. **Testing**: Always test new rules against sample feedback before enabling
4. **Monitoring**: Track rule effectiveness with dashboards
5. **Documentation**: Document why each rule exists in the description field
6. **Gradual Rollout**: Enable rules for a subset of feedback before full deployment
7. **Feedback Loop**: Adjust rules based on human reviewer feedback

## Extending Rules

The rule system supports custom operators via plugins:

```python
# In src/routing/custom_operators.py

@register_operator
class DateRangeOperator(Operator):
    name = "date_between"
    def evaluate(self, field_value, args):
        start, end = args
        return start <= field_value <= end

# Use in YAML
conditions:
  - field: created_at
    operator: date_between
    value: ["2026-03-01", "2026-03-31"]
```

## Performance Considerations

- Rule evaluation is single-threaded by design for consistency
- Average evaluation time: <50ms for 100 rules
- Rules are cached in memory; reload takes <1 second
- For high-volume feedback (>1000/day), consider rule indexing
