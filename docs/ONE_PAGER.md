# Feedback Router — One-Pager

## What Is It?

Feedback Router is an AI-powered intake system that catches every inbound message — from website forms, chat widgets, Slack channels, and 404 pages — classifies it, and either responds directly or routes it to the right human with full context.

No feedback falls through the cracks. No one has to repeat themselves.

---

## How It Works

Every message flows through five steps:

```
Receive → Classify → Route → Respond → Close Loop
```

| Step | What Happens |
|------|-------------|
| **Receive** | Message arrives from any channel. Normalized into a standard format. Contact identified. |
| **Classify** | AI assigns category (bug, feature request, complaint, praise, question), sentiment, urgency, and business impact. |
| **Route** | Rules engine decides: auto-respond, or send to a specific team (engineering, product, support, leadership, security). |
| **Respond** | Simple queries get an immediate answer. Complex items get routed with a summary so the human has full context. |
| **Close Loop** | Resolution tracked. Lifecycle: received → acknowledged → in_review → actioned → resolved → closed. |

---

## Key Capabilities

- **Multi-channel intake** — Website forms, chat widget, 404 feedback, Slack (public channels, DMs, Slack Connect), Microsoft Teams
- **AI classification** — Category, sentiment, urgency, theme tagging via Claude API with rule-based fallback
- **Smart routing** — Rules engine with 7 automatic escalation triggers (negative sentiment + enterprise, competitor mentions, security issues, lost customers, executive mentions, critical urgency, high business impact)
- **Direct response** — Auto-responds to simple queries (FAQs, acknowledgments, lost visitor redirects) without human involvement
- **Lifecycle tracking** — Every item tracked from receipt to resolution
- **Trend detection** — Surfaces recurring themes and emerging issues across all channels

---

## Architecture at a Glance

```
  Channels              Pipeline                    Output
 ──────────     ─────────────────────────     ──────────────────
  Website  ──┐                                ┌── Auto-Response
  Slack    ──┼──→ Intake → Classify → Route ──┼── Team Routing
  Teams    ──┤                                ├── Escalation
  Email*   ──┘                                └── Insight Reports
```

**Stack**: Python 3.9+ · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · Celery + Redis · Claude API

---

## What Makes It Different

| Feature | How |
|---------|-----|
| **Nobody gets turned away** | Built on the Amex concierge principle — every message gets a response, even if it's just "we got this, here's what happens next" |
| **Context travels with the message** | When feedback reaches a human, it arrives pre-classified with sentiment, urgency, category, and contact history — no cold handoffs |
| **Rules you can edit without code** | Routing rules, escalation triggers, and team assignments live in YAML config files |
| **Channel-agnostic core** | Adding a new channel means implementing one adapter interface. The classification, routing, and response logic stays the same. |
| **Graceful degradation** | If the LLM is down, rule-based classification takes over automatically |

---

## Numbers

- **287 passing tests** — unit, integration, and end-to-end
- **5 agents** — Intake, Classifier, Router, Responder, Concierge
- **7 escalation triggers** — automatic, configurable
- **6 teams** — Engineering, Product, Support, Leadership, Security, Customer Success
- **2 channels live** — Website, Slack (Teams and Email in progress)

---

## Quick Start

```bash
git clone https://github.com/veebeeyoukay/feedback-router.git
cd feedback-router
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp config/env.example .env   # add your API keys
python -m src.main            # runs on http://localhost:8000
```

Run tests: `pip install pytest && pytest tests/ -o "addopts="`

---

## Status

**v0.2.0** — Core pipeline implemented and tested. Website and Slack channels operational. Microsoft Teams integration in progress. Database persistence, middleware (auth, rate limiting), and async task processing complete.

---

*ItsJen.ai / Generation AI, LLC*
