# Microsoft Teams Setup — MYOTA

Step-by-step instructions for connecting the Feedback Router to MYOTA's Microsoft Teams workspace.

---

## Overview

This integration lets the Feedback Router:
1. **Listen** to messages posted in designated Teams channels (e.g., #feedback, #bugs, #support)
2. **Classify** incoming feedback automatically (category, sentiment, urgency)
3. **Route** items to the right team with full context
4. **Respond** in-thread with acknowledgments and auto-responses
5. **Escalate** critical items (security incidents, data protection concerns, ransomware-related feedback) to leadership

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Microsoft 365 tenant | MYOTA's M365 tenant with Teams enabled |
| Admin access | Azure AD admin or Teams admin role to register the app |
| Azure subscription | For the Bot registration (free tier is fine) |
| Feedback Router running | The FastAPI server deployed and reachable via HTTPS |
| HTTPS endpoint | Public URL with valid TLS cert (e.g., `https://feedback.myota.io/api/v1/teams/webhook`) |

---

## Step 1: Register an Azure Bot

1. Go to the [Azure Portal](https://portal.azure.com)
2. Search for **"Azure Bot"** → Click **Create**
3. Fill in:
   - **Bot handle**: `myota-feedback-router`
   - **Subscription**: MYOTA's Azure subscription
   - **Resource group**: Create new or use existing (e.g., `rg-feedback-router`)
   - **Pricing tier**: F0 (free) for dev, S1 for production
   - **Microsoft App ID**: Select **"Create new Microsoft App ID"**
4. Click **Create** and wait for deployment

After creation:
- Go to the bot resource → **Configuration**
- Set **Messaging endpoint** to: `https://feedback.myota.io/api/v1/teams/webhook`
- Note the **Microsoft App ID** and **App Password** (you'll need both)

---

## Step 2: Create the App Registration

1. Go to **Azure Active Directory** → **App registrations**
2. Find the app created in Step 1 (or create a new one)
3. Under **Certificates & secrets** → **New client secret**
   - Description: `feedback-router-prod`
   - Expiry: 24 months
   - **Copy the secret value immediately** (it won't be shown again)
4. Under **API permissions**, add:
   - `ChannelMessage.Read.All` (Application) — read channel messages
   - `Team.ReadBasic.All` (Application) — list teams/channels
   - `User.Read.All` (Application) — resolve user display names
   - `ChatMessage.Send` (Application) — post responses
5. Click **Grant admin consent for MYOTA**

---

## Step 3: Create the Teams App Manifest

Create a file `teams-app/manifest.json`:

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
  "manifestVersion": "1.17",
  "version": "1.0.0",
  "id": "{{MICROSOFT_APP_ID}}",
  "developer": {
    "name": "MYOTA",
    "websiteUrl": "https://www.myota.io",
    "privacyUrl": "https://www.myota.io/privacy",
    "termsOfUseUrl": "https://www.myota.io/terms"
  },
  "name": {
    "short": "Feedback Router",
    "full": "MYOTA Feedback Router"
  },
  "description": {
    "short": "Routes and classifies inbound feedback",
    "full": "AI-powered feedback intake system that classifies, routes, and responds to messages from Teams channels. Escalates security and data protection issues automatically."
  },
  "icons": {
    "outline": "icon-outline.png",
    "color": "icon-color.png"
  },
  "accentColor": "#1A1A2E",
  "bots": [
    {
      "botId": "{{MICROSOFT_APP_ID}}",
      "scopes": ["team", "personal"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["team"],
          "commands": [
            {
              "title": "status",
              "description": "Show feedback pipeline status and recent activity"
            },
            {
              "title": "digest",
              "description": "Get a summary of today's feedback"
            },
            {
              "title": "escalate",
              "description": "Escalate a feedback item to leadership"
            },
            {
              "title": "assign",
              "description": "Assign feedback to a team member"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["messageTeamMembers"],
  "validDomains": ["feedback.myota.io"]
}
```

Replace `{{MICROSOFT_APP_ID}}` with the App ID from Step 1.

---

## Step 4: Package and Install the App

1. Create a ZIP file containing:
   - `manifest.json`
   - `icon-outline.png` (32x32, transparent background)
   - `icon-color.png` (192x192, full color)

2. In Microsoft Teams:
   - Go to **Apps** → **Manage your apps** → **Upload a custom app**
   - Select the ZIP file
   - Choose **Add to a team** → Select MYOTA's workspace
   - Add the bot to these channels:
     - `#feedback`
     - `#bugs`
     - `#support`
     - `#security-incidents`

---

## Step 5: Configure the Feedback Router

Add these environment variables to the Feedback Router's `.env`:

```bash
# Microsoft Teams / Azure Bot
TEAMS_ENABLED=true
MICROSOFT_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_APP_PASSWORD=your-client-secret-from-step-2
TEAMS_WEBHOOK_URL=https://feedback.myota.io/api/v1/teams/webhook

# Teams channels to monitor (channel IDs from Teams)
TEAMS_MONITORED_CHANNELS=feedback,bugs,support,security-incidents

# MYOTA-specific escalation
# Security and data protection issues auto-escalate
TEAMS_SECURITY_CHANNEL=security-incidents
TEAMS_LEADERSHIP_CHANNEL=leadership-escalations
```

---

## Step 6: Add the Teams Channel Adapter

The Teams adapter handles the Microsoft Bot Framework protocol. Add to `config/channels.yaml`:

```yaml
channels:
  teams:
    enabled: true
    adapter: TeamsChannelAdapter
    config:
      app_id_env: MICROSOFT_APP_ID
      app_password_env: MICROSOFT_APP_PASSWORD
      monitored_channels:
        - name: "feedback"
          purpose: "General feedback collection"
          auto_process: true
          priority: normal
        - name: "bugs"
          purpose: "Bug reports and technical issues"
          auto_process: true
          priority: high
        - name: "support"
          purpose: "Customer support and questions"
          auto_process: true
          priority: normal
        - name: "security-incidents"
          purpose: "Security, ransomware, data protection concerns"
          auto_process: true
          priority: critical
      response_in_thread: true
      auto_react: true
      rate_limit: 60/minute
```

---

## Step 7: Configure MYOTA-Specific Routing Rules

Add to `config/routing_rules.yaml`:

```yaml
# MYOTA-specific rules — data protection and security focus
myota_rules:

  # Ransomware or data breach mentions → immediate escalation
  - name: security_threat_escalation
    trigger:
      keywords:
        - ransomware
        - data breach
        - unauthorized access
        - encryption failure
        - shard integrity
        - data exfiltration
        - compliance violation
    action:
      route_to: security
      escalate: true
      priority: 1
      response_type: human_only
      sla_hours: 1
      notify:
        - security-incidents
        - leadership-escalations

  # Customer data recovery issues → engineering + customer success
  - name: data_recovery_escalation
    trigger:
      keywords:
        - recovery failed
        - cannot restore
        - data loss
        - backup failure
        - point-in-time
        - shard missing
    action:
      route_to: engineering
      escalate: true
      priority: 1
      response_type: human_only
      cc_team: customer_success

  # Enterprise prospect mentioning competitors → sales/leadership
  - name: competitive_threat
    trigger:
      keywords:
        - competitor
        - switching to
        - evaluating alternatives
        - Rubrik
        - Cohesity
        - Veeam
        - Commvault
    action:
      route_to: customer_success
      escalate: true
      priority: 2
      response_type: flag_human

  # Storage cost concerns → product
  - name: pricing_sensitivity
    trigger:
      keywords:
        - too expensive
        - cost reduction
        - storage costs
        - pricing
        - budget
    action:
      route_to: product
      priority: 3
      response_type: faq_draft
```

---

## Step 8: Configure MYOTA Teams

Update `config/teams.yaml` with MYOTA's team structure:

```yaml
teams:
  - team_id: team_engineering
    name: "Engineering"
    description: "Shard & Spread platform, data recovery, infrastructure"
    teams_channel: "engineering-feedback"
    email: "engineering@myota.io"
    response_sla_hours: 4

  - team_id: team_product
    name: "Product"
    description: "Feature requests, roadmap, storage optimization"
    teams_channel: "product-feedback"
    email: "product@myota.io"
    response_sla_hours: 4

  - team_id: team_support
    name: "Support"
    description: "Customer support, onboarding, general questions"
    teams_channel: "support"
    email: "support@myota.io"
    response_sla_hours: 2

  - team_id: team_security
    name: "Security"
    description: "Security incidents, compliance, data protection"
    teams_channel: "security-incidents"
    email: "security@myota.io"
    response_sla_hours: 1

  - team_id: team_leadership
    name: "Leadership"
    description: "Executive escalations, strategic decisions"
    teams_channel: "leadership-escalations"
    email: "leadership@myota.io"
    response_sla_hours: 1

  - team_id: team_customer_success
    name: "Customer Success"
    description: "Enterprise accounts, renewals, churn prevention"
    teams_channel: "customer-success"
    email: "success@myota.io"
    response_sla_hours: 2
```

---

## Step 9: Test the Integration

### Verify bot connection

```bash
# Check the bot is responding
# In Teams, go to #feedback and type:
@Feedback Router status
```

Expected response:
```
Feedback Router is online.
Pipeline: healthy
Channels monitored: feedback, bugs, support, security-incidents
Items processed today: 0
```

### Test classification

Post in `#feedback`:
```
We're having issues with data recovery after the latest update.
The point-in-time restore isn't working for files modified last Tuesday.
```

Expected behavior:
1. Bot reacts with a checkmark
2. Bot replies in thread: "Got it — this has been classified as a bug report (urgency: high) and routed to Engineering. They'll respond within 4 hours."
3. Message appears in `#engineering-feedback` with full context

### Test escalation

Post in `#security-incidents`:
```
A customer reported unauthorized access attempts on their shard storage endpoint.
```

Expected behavior:
1. Bot immediately flags with priority: critical
2. Routes to Security team
3. Also notifies `#leadership-escalations`
4. SLA: 1 hour response

### Run automated tests

```bash
source venv/bin/activate
pytest tests/ -o "addopts=" -v
```

---

## Step 10: Go Live Checklist

- [ ] Azure Bot registered and messaging endpoint verified
- [ ] App installed in MYOTA Teams workspace
- [ ] Bot added to all monitored channels
- [ ] Environment variables set in production `.env`
- [ ] MYOTA routing rules configured and tested
- [ ] Security escalation triggers verified (ransomware, breach, unauthorized access keywords)
- [ ] Team assignments correct (channels map to the right people)
- [ ] SLA hours configured per team
- [ ] HTTPS endpoint live with valid TLS cert
- [ ] Rate limiting configured
- [ ] Monitoring/alerting set up for bot health
- [ ] Team notified that bot is live

---

## Troubleshooting

### Bot not receiving messages
1. Verify the messaging endpoint in Azure Bot → Configuration matches your deployed URL
2. Check the endpoint returns HTTP 200 to Microsoft's health probes
3. Confirm the bot is added to the channel (not just the workspace)

### Bot can't reply in threads
1. Check `ChatMessage.Send` permission is granted with admin consent
2. Verify the App Password hasn't expired
3. Check Feedback Router logs: `tail -f logs/teams.log`

### Escalation not triggering
1. Verify keywords in `routing_rules.yaml` match the message content
2. Check the channel is in the monitored list
3. Run: `curl -X POST https://feedback.myota.io/api/v1/feedback/process -H "Content-Type: application/json" -d '{"text": "ransomware detected", "channel": "security-incidents"}'`

### Token expiry
- Azure client secrets expire. Set a calendar reminder for the expiry date from Step 2.
- Rotate: Azure AD → App registrations → Certificates & secrets → New client secret
- Update `MICROSOFT_APP_PASSWORD` in `.env` and restart

---

## Architecture (MYOTA Deployment)

```
  Teams Channels                Feedback Router              Teams Channels
 ──────────────               ─────────────────            ──────────────────
 #feedback       ──┐                                  ┌── #engineering-feedback
 #bugs           ──┼──→  Intake → Classify → Route ───┼── #product-feedback
 #support        ──┤                                  ├── #security-incidents
 #security-      ──┘                                  ├── #leadership-escalations
  incidents                                           └── #customer-success

                     Azure Bot Framework
                     (webhook ↔ Bot Service)
```

---

*MYOTA × ItsJen.ai Feedback Router — Deployment Guide*
