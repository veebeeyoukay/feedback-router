# Feedback Router

**The front-line feedback agent for ItsJen.ai** — an omni-channel system that receives, understands, classifies, responds to, and routes all inbound feedback from prospects, clients, lost visitors, and anyone else who reaches out.

Built on the Amex concierge principle: *no one gets turned away, everyone gets helped.*

---

## What It Does

Feedback Router is the operational backbone of how ItsJen.ai listens to and acts on what people tell us. It handles two channels today (website and Slack) with architecture designed to add any channel tomorrow.

**For simple interactions** — acknowledging receipt, directing lost visitors, answering FAQs from company docs — it responds directly.

**For complex or sensitive items** — it classifies, summarizes, and routes to the right human with full context so nobody has to repeat themselves.

### Core Pipeline

Every inbound message flows through five steps:

1. **Identify** — Who is this? (prospect, client, lost visitor, internal, unknown)
2. **Listen** — What do they actually need? (surface request vs. underlying need)
3. **Classify** — Category, sentiment, urgency, business impact, ICP theme
4. **Decide** — Respond directly or route to a human?
5. **Close the loop** — Confirm resolution, log everything

### Key Capabilities

- **Omni-channel intake** — Website forms, chat widget, 404 feedback, Slack channels, Slack Connect, and Slack bot interactions
- **ICP-aware classification** — Tags feedback to ItsJen.ai's five core themes (Productivity, Career Security, Learning Curve, Privacy, Family)
- **Intelligent triage** — Rules-based routing with automatic escalation for critical triggers (enterprise + negative sentiment, competitor mentions, legal issues)
- **Direct response** — Auto-responds to simple queries using company knowledge base with on-brand voice
- **Lifecycle tracking** — received → acknowledged → in_review → actioned → resolved → closed
- **Insight aggregation** — Surfaces trends, recurring themes, and emerging issues

---

## Architecture

```
┌──────────────────────────────────────────┐
│            FEEDBACK SOURCES              │
│    Website (Forms, Chat, 404)  │  Slack  │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│      INTAKE LAYER        │
│  Channel Adapters        │
│  Format Normalizers      │
│  Deduplication           │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│    CLASSIFICATION        │
│  Contact Identification  │
│  Category Assignment     │
│  Sentiment Analysis      │
│  Theme Tagging (1-5)     │
│  Urgency Scoring         │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│    TRIAGE & ROUTING      │
│  Rule Engine             │
│  Escalation Logic        │
│  Team Assignment         │
│  Response Decision       │
└──────┬─────────┬─────────┘
       │         │
       ▼         ▼
  ┌─────────┐ ┌────────────┐
  │ Auto-   │ │ Route to   │
  │ Respond │ │ Human via  │
  │         │ │ Slack      │
  └─────────┘ └────────────┘
               │
               ▼
┌──────────────────────────┐
│   INSIGHT & REPORTING    │
│  Trend Detection         │
│  Theme Analytics         │
│  Loop Closure Tracking   │
└──────────────────────────┘
```

---

## ICP & Five Themes

ItsJen.ai serves **Gen X professionals (ages ~40-60)** — pragmatic, results-oriented, cautiously optimistic about AI. They lead with hope but buy on trust.

Every piece of feedback is tagged to one or more of these themes:

| # | Theme | Signal | In Their Words |
|---|-------|--------|----------------|
| 1 | Workplace Productivity | Reports, emails, Excel, project mgmt | *"Make my workday better without making it harder"* |
| 2 | Career Security | Relevance, redundancy, AI skills | *"Am I going to be okay?"* |
| 3 | Learning Curve | Ease of use, no coding, time to learn | *"Just show me what to do"* |
| 4 | Privacy & Safety | Data, compliance, trust | *"I want to use this, but I need to know it's safe"* |
| 5 | Family & Personal Life | Kids, parents, health, finances | *"AI is in my house now. Help me manage it"* |

This theme tagging enables product and marketing to track what the ICP actually cares about and whether messaging is landing.

---

## Project Structure

```
feedback-router/
├── src/
│   ├── agents/              # AI agent configs (intake, triage, response, concierge)
│   │   ├── intake.py        # Raw feedback normalization
│   │   ├── classifier.py    # Category, sentiment, theme tagging
│   │   ├── router.py        # Triage rules, escalation, team assignment
│   │   ├── responder.py     # Auto-response generation
│   │   └── concierge.py     # Lost visitor handling
│   ├── channels/
│   │   ├── website/         # Website intake (forms, chat, 404 handler)
│   │   │   ├── webhook.py   # POST /api/feedback/ingest
│   │   │   └── widget.py    # Embeddable JS widget config
│   │   └── slack/           # Slack bot
│   │       ├── events.py    # Slack Events API handler
│   │       ├── commands.py  # Slash commands
│   │       ├── blocks.py    # Block Kit message builders
│   │       └── bot.py       # Bot personality & routing
│   ├── classification/      # Classification engine
│   │   ├── categories.py    # Feedback category taxonomy
│   │   ├── sentiment.py     # Sentiment analysis
│   │   ├── themes.py        # ICP theme tagging (1-5)
│   │   └── contact.py       # Contact identification & history
│   ├── routing/             # Routing engine
│   │   ├── rules.py         # Triage rule definitions
│   │   ├── escalation.py    # Escalation trigger logic
│   │   ├── assignment.py    # Team/individual assignment
│   │   └── engine.py        # Rule evaluation engine
│   ├── schemas/             # Data models
│   │   ├── feedback.py      # Unified feedback schema
│   │   ├── classification.py # Classification output schema
│   │   ├── routing.py       # Routing decision schema
│   │   └── response.py      # Response schema
│   ├── middleware/           # Cross-cutting concerns
│   │   ├── auth.py          # Authentication
│   │   ├── rate_limit.py    # Rate limiting
│   │   └── error_handler.py # Error handling & dead letter queue
│   ├── utils/               # Shared helpers
│   │   ├── logger.py        # Structured logging
│   │   └── config.py        # Configuration loader
│   └── main.py              # Application entry point
├── config/
│   ├── routing_rules.yaml   # Triage rules (editable without code changes)
│   ├── escalation.yaml      # Escalation triggers
│   ├── teams.yaml           # Team definitions and Slack channels
│   └── env.example          # Environment variable template
├── docs/
│   ├── ARCHITECTURE.md      # System design deep dive
│   ├── API.md               # Webhook endpoints & request/response formats
│   ├── ROUTING.md           # Triage logic & escalation rules
│   ├── AGENTS.md            # Agent specifications & system prompts
│   ├── CHANNELS.md          # How to add new feedback channels
│   ├── DEPLOYMENT.md        # Infrastructure & deployment guide
│   ├── ICP_AND_THEMES.md    # ICP definition, themes, brand voice
│   └── RUNBOOK.md           # Operational procedures
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test feedback messages (one per eval scenario)
├── scripts/
│   ├── setup.sh             # Development environment setup
│   └── seed_data.py         # Seed test data
├── .github/
│   └── workflows/
│       └── ci.yml           # CI pipeline
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_ORG/feedback-router.git
cd feedback-router

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/env.example .env
# Edit .env with your Slack tokens, API keys, etc.

# Run
python -m src.main
```

---

## Documentation

| Doc | What it covers |
|-----|---------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, data flows, agent interactions, tech decisions |
| [API Reference](docs/API.md) | Webhook endpoints, request/response formats, authentication |
| [Routing Rules](docs/ROUTING.md) | Triage logic, escalation triggers, team assignment, rule syntax |
| [Agent Specs](docs/AGENTS.md) | System prompts, decision logic, I/O schemas for each agent |
| [Channels Guide](docs/CHANNELS.md) | How to add new feedback channels (email, phone, etc.) |
| [Deployment](docs/DEPLOYMENT.md) | Infrastructure, Slack app setup, monitoring, rollback |
| [ICP & Themes](docs/ICP_AND_THEMES.md) | ICP definition, five themes, brand voice guidelines |
| [Runbook](docs/RUNBOOK.md) | Operational procedures, common scenarios, troubleshooting |

---

## Status

**v0.1.0** — Initial scaffold. Architecture defined, schemas locked, agents specified. Awaiting code-level implementation decisions (see [interview notes](docs/INTERVIEW_NOTES.md) once completed).

---

*ItsJen.ai / Generation AI, LLC — Proprietary*
