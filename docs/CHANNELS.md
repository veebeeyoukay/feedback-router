# Feedback Router: Channel Integration Guide

## Overview

The Feedback Router is designed as a multi-channel system from the start. Currently, two channels are fully implemented. The architecture supports adding new channels without modifying core logic.

---

## Current Channels

### 1. Website Widget

**Status**: Production

**Implementation**: Embedded JavaScript widget on website

**Flow**:
1. User encounters feedback form on website
2. Submits: name, email, message
3. Widget POSTs to `/api/feedback/ingest` endpoint
4. User sees confirmation message
5. Feedback enters processing pipeline

**Technical Details**:

```javascript
// Embed on website (in <head> or before </body>)
<script src="https://cdn.itjen.ai/widget.js"></script>
<script>
  ItsJenFeedback.init({
    apiKey: 'your_api_key_here',
    theme: 'light', // or 'dark'
    position: 'bottom-right', // or 'bottom-left'
    placeholder: 'Share your thoughts...'
  });
</script>
```

**Widget Behavior**:
- Floating button in corner
- Opens modal form on click
- Pre-fills name/email if user logged in (optional)
- Shows success message after submission
- Collects: email, name, message, current page URL, user agent
- No data stored in browser (no localStorage)

**Widget Configuration**:
```javascript
{
  apiKey: string,                      // Required: API key for webhook
  theme: 'light' | 'dark',            // Default: 'light'
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left',  // Default: 'bottom-right'
  placeholder: string,                 // Default: 'Share your thoughts...'
  primaryColor: string,                // Default: #0047AB (ItsJen blue)
  buttonText: string,                  // Default: 'Feedback'
  successMessage: string,              // Default: 'Thanks for your feedback!'
  debug: boolean                       // Default: false (enable console logs)
}
```

**Security**:
- API key validated on server
- HTTPS required
- CORS validation
- Rate limiting (10 requests/minute per IP)
- XSS protection in widget code

**Analytics**:
- Track widget impressions
- Track form opens
- Track submit rate
- Track error rate

---

### 2. Slack Integration

**Status**: Production

**Integration Type**: Slack Bot + Events API

**Flow**:
1. User posts message in feedback channel (e.g., #feedback) or DMs bot
2. Slack sends event to `/api/feedback/slack` endpoint
3. System acknowledges receipt (HTTP 200 within 3 seconds)
4. Feedback enters processing pipeline asynchronously
5. Response posted in thread or via DM

**Setup Instructions**:

```bash
# 1. Create Slack App
# Go to https://api.slack.com/apps
# Click "Create New App" → "From scratch"
# Name: "ItsJen Feedback Router"
# Pick workspace

# 2. Enable Event Subscriptions
# Basic Information → Event Subscriptions
# Enable Events: ON
# Request URL: https://api.itjen.ai/api/feedback/slack
# (Slack will verify with a challenge)

# 3. Subscribe to Bot Events
# message.channels: When a message is posted to a channel
# message.groups: When a message is posted to a private channel
# message.im: When a message is posted to a direct message

# 4. Set OAuth Scopes
# OAuth & Permissions → Scopes → Bot Token Scopes
# Required:
# - chat:write (post messages)
# - users:read (get user info)
# - channels:read (list channels)
# - groups:read (list private channels)
# - reactions:write (add reactions)

# 5. Install Bot
# OAuth & Permissions → Install to Workspace
# Copy Bot Token (starts with xoxb-)

# 6. Set Environment
export SLACK_BOT_TOKEN=xoxb-xxxxx
export SLACK_SIGNING_SECRET=xxxxx
```

**Bot Capabilities**:

```python
# Listen to mentions
@app.message()
async def handle_feedback(message, say, client):
    # Extract message, user, timestamp
    # Normalize and send to intake agent
    # Post response in thread

# React to messages
await client.reactions_add(
    channel=event['channel'],
    timestamp=event['ts'],
    emoji='eyes'  # Acknowledging receipt
)

# Reply in thread
await client.chat_postMessage(
    channel=event['channel'],
    thread_ts=event['ts'],
    text="Thanks for sharing! Our team is reviewing this..."
)
```

**Slack Message Format**:

**Input** (user posts in #feedback):
```
User Jane Doe: "The new learning module is really confusing. It would help if there were step-by-step tutorials."
```

**Captured**:
- User ID: U1234SLACK
- Channel: C5678FEEDBACK
- Timestamp: 1711014720.000100
- Thread: (if reply to existing thread)
- Text: "The new learning module is really confusing..."
- User name: Jane Doe
- User email: jane@example.com (if available in Slack profile)

**Output** (response posted in thread):
```
🤖 ItsJen Feedback Router: Thanks for the detailed feedback about Learning Curve, Jane.
We've seen this come up a few times. Here's a guide that might help: [link]

Our team is also using this feedback to improve the tutorial. I'll flag this with the
product team. Expect an update from them within 24 hours.
```

**Configuration**:
```yaml
# config/slack.yaml
channels:
  feedback:
    id: "C5678FEEDBACK"
    purpose: "User feedback collection"
    responses_in_thread: true
    auto_react: "eyes"  # React with eyes emoji on receipt

message_templates:
  auto_ack: "🤖 ItsJen: Thanks for sharing! Our team is reviewing this..."
  escalation: "🚨 Escalated to leadership. Expect response within 2 hours."

rate_limits:
  messages_per_minute: 60
  reactions_per_hour: 1000
```

---

## Channel Adapter Interface

To add a new channel, implement the `ChannelAdapter` interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ChannelAdapter(ABC):
    """
    Base class for channel adapters. Each new channel must implement these methods.
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the channel identifier (e.g., 'email', 'support_ticket')"""
        pass

    @abstractmethod
    async def parse_message(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw channel event into normalized format.

        Returns:
        {
            'text': 'message content',
            'contact': {
                'identifier': 'email@example.com or user_id',
                'name': 'Jane Doe',
                'email': 'jane@example.com'  # if available
            },
            'channel_metadata': {
                'external_id': 'message_id',
                'thread_id': 'optional_thread_id',
                'received_at': '2026-03-19T14:32:00Z'
            }
        }
        """
        pass

    @abstractmethod
    async def post_response(
        self,
        contact: Dict[str, Any],
        response_content: str,
        channel_metadata: Dict[str, Any],
        response_tier: str
    ) -> bool:
        """
        Post response to the channel.

        Args:
            contact: Contact info (email, name, etc.)
            response_content: The response message
            channel_metadata: Channel-specific metadata
            response_tier: auto_ack|faq_draft|complex_draft|human_only

        Returns:
            True if successfully posted, False otherwise
        """
        pass

    @abstractmethod
    async def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """
        Validate that webhook request is authentic.

        For Slack: verify signature
        For email: verify sender
        For tickets: verify API token

        Returns:
            True if valid, False if suspicious
        """
        pass

    @abstractmethod
    async def get_contact_info(self, contact_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Look up additional contact info from channel system.

        For Slack: fetch user profile
        For email: look up in address book
        For tickets: get from ticket system

        Returns:
            Contact details or None if not found
        """
        pass

    @abstractmethod
    async def handle_error(self, feedback_id: str, error: Exception) -> None:
        """
        Handle errors specific to this channel.

        For Slack: post error message in DM
        For email: send error email
        For tickets: update ticket with error note
        """
        pass
```

### Example Implementation: Email Channel

```python
from typing import Dict, Any, Optional
import hmac
import hashlib
from email.parser import Parser
import aiosmtplib

class EmailChannelAdapter(ChannelAdapter):
    """
    Adapter for email-based feedback (future Wave 2 implementation).
    """

    @property
    def channel_name(self) -> str:
        return "email"

    async def parse_message(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse email message"""
        # raw_event contains MIME message
        email_message = Parser().parsestr(raw_event['message'])

        return {
            'text': email_message.get_payload(decode=True).decode('utf-8'),
            'contact': {
                'identifier': email_message['From'],
                'name': email_message.get('X-Sender-Name', 'Unknown'),
                'email': email_message['From']
            },
            'channel_metadata': {
                'external_id': email_message['Message-ID'],
                'thread_id': email_message['In-Reply-To'],
                'subject': email_message['Subject'],
                'received_at': email_message['Date']
            }
        }

    async def post_response(
        self,
        contact: Dict[str, Any],
        response_content: str,
        channel_metadata: Dict[str, Any],
        response_tier: str
    ) -> bool:
        """Send response via email"""
        async with aiosmtplib.SMTP(hostname='smtp.itjen.ai') as smtp:
            await smtp.send_message(
                from_addr='feedback@itjen.ai',
                to_addrs=[contact['email']],
                subject=f"Re: {channel_metadata.get('subject', 'Feedback')}",
                message=response_content
            )
        return True

    async def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """Verify email webhook signature (if using email service like SendGrid)"""
        signature = headers.get('X-SendGrid-Signature')
        if not signature:
            return False

        timestamp = headers.get('X-SendGrid-Timestamp')
        computed = hmac.new(
            b'webhook_secret',
            f"{timestamp}{body}".encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, computed)

    async def get_contact_info(self, contact_identifier: str) -> Optional[Dict[str, Any]]:
        """Look up contact from email directory"""
        # In real implementation, query contacts database
        return {
            'email': contact_identifier,
            'name': 'Jane Doe',
            'contact_type': 'identified'
        }

    async def handle_error(self, feedback_id: str, error: Exception) -> None:
        """Send error notification via email"""
        await send_email(
            to='admin@itjen.ai',
            subject=f'Feedback Router Error: {feedback_id}',
            body=str(error)
        )
```

---

## Wave 2: Email & Support Tickets

**Timeline**: Q2 2026

**Email Channel**:
- Inbound: feedback@itjen.ai address
- Parse MIME messages
- Extract sender, subject, body
- Link to contact
- Reply via email

**Support Ticket Channel**:
- Integrate with Zendesk/Intercom/Freshdesk
- Pull tickets via API
- Classify tickets as feedback
- Route to teams
- Close tickets with responses

**Implementation Steps**:
1. Implement EmailChannelAdapter
2. Implement TicketChannelAdapter
3. Add routing rules for email and tickets
4. Add response templates for email/tickets
5. Test with real emails and tickets
6. Monitor and tune classification

---

## Wave 3: Phone, Social, Surveys

**Timeline**: Q3-Q4 2026

**Phone Transcripts**:
- Record + transcribe calls
- Feed transcripts into feedback system
- Flag escalations (angry tone, specific words)
- Create follow-up tasks
- Link to contacts

**Social Media**:
- Monitor Twitter/LinkedIn mentions
- Capture sentiment and themes
- Flag negative mentions for quick response
- Track brand mentions

**Surveys**:
- Integrate SurveyMonkey / Typeform responses
- Auto-classify open-ended responses
- Aggregate Likert scale results
- Correlate with feedback trends

**Implementation Approach**:
- Same ChannelAdapter pattern
- Adapt authentication (OAuth for Twitter, API keys for survey tools)
- Handle rate limits per channel
- Manage response strategy per channel (Twitter public reply vs. DM)

---

## Channel Configuration

All channel config lives in `/config`:

```yaml
# config/channels.yaml
channels:
  website:
    enabled: true
    adapter: WebsiteChannelAdapter
    config:
      widget_enabled: true
      form_fields: [email, name, message, page_url]
      rate_limit_per_ip: 10/minute
      success_message: "Thanks for your feedback!"

  slack:
    enabled: true
    adapter: SlackChannelAdapter
    config:
      bot_token_env: SLACK_BOT_TOKEN
      signing_secret_env: SLACK_SIGNING_SECRET
      feedback_channel: "C5678FEEDBACK"
      auto_react_emoji: "eyes"
      response_in_thread: true
      rate_limit: 60/minute

  # Wave 2
  email:
    enabled: false
    adapter: EmailChannelAdapter
    config:
      inbox_address: "feedback@itjen.ai"
      smtp_host_env: SMTP_HOST
      smtp_user_env: SMTP_USER
      smtp_password_env: SMTP_PASSWORD

  # Wave 3
  phone:
    enabled: false
    adapter: PhoneChannelAdapter

  social:
    enabled: false
    adapter: SocialChannelAdapter
```

---

## Response Strategy by Channel

### Website Widget
- **Auto-ACK**: Show in modal, also email
- **FAQ Draft**: Email with FAQ + CTA to reply
- **Complex Draft**: Email draft, user can approve via link
- **Human Only**: Email with request for manual response

### Slack
- **Auto-ACK**: React with ✅, post brief message in thread
- **FAQ Draft**: Post FAQ in thread, add 👍/👎 reactions
- **Complex Draft**: Post in thread as DRAFT, mention @reviewer
- **Human Only**: Post in thread with @team mention

### Email (Future)
- **Auto-ACK**: Immediate auto-reply email
- **FAQ Draft**: Email with FAQ + help links
- **Complex Draft**: Email draft for human approval
- **Human Only**: Forward to support team for response

### Tickets (Future)
- **Auto-ACK**: Internal comment "feedback received"
- **FAQ Draft**: Update ticket description with FAQ
- **Complex Draft**: Add internal note with draft response
- **Human Only**: Assign to team, flag for review

---

## Testing New Channels

```bash
# Test adapter implementation
pytest tests/channels/test_channel_adapter.py -k "EmailChannelAdapter"

# Integration test with mock external service
pytest tests/channels/integration/test_email_channel.py

# Load test (verify rate limiting)
pytest tests/channels/load/test_slack_integration.py --load-test
```

## Monitoring Channel Health

```bash
# Check channel status
GET /api/admin/channels/health

Response:
{
  "website": {
    "status": "healthy",
    "messages_today": 142,
    "error_rate": 0.001,
    "avg_response_time_ms": 350
  },
  "slack": {
    "status": "healthy",
    "messages_today": 43,
    "error_rate": 0.0,
    "avg_response_time_ms": 850
  }
}
```

## Best Practices for Channel Adapters

1. **Stateless**: Adapters should not maintain state between requests
2. **Idempotent**: Same message processed twice should produce same result
3. **Secure**: Validate all webhook signatures, use TLS
4. **Async**: Use async/await for all I/O operations
5. **Retry Logic**: Implement exponential backoff for transient failures
6. **Logging**: Log all requests/responses for debugging
7. **Rate Limits**: Respect external service rate limits
8. **Error Handling**: Never throw exceptions; return False/None and log
