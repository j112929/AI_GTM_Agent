# External Platform Integration Analysis

This document outlines the external platforms that can be integrated into the **AI GTM Agent** architecture. The system's modular design (Ingest -> Process -> Send) allows for easy plug-and-play integrations.

## 1. Lead Sources (Data Ingestion)

The `LeadIngestionService` and `POST /leads` endpoint can be adapted to accept data from:

| Platform | Integration Method | Complexity | Description |
|----------|-------------------|------------|-------------|
| **Apollo.io** | REST API | Medium | Fetch contact details and push directly to our Ingest API. |
| **LinkedIn** | PhantomBuster / BrightData | Low | Import scraped CSVs or connect via Webhooks from scraping tools. |
| **Typeform / Jottform** | Webhook | Low | Trigger lead creation when a "Contact Us" form is submitted. |
| **HubSpot / Salesforce** | REST API / Webhooks | High | Listen for "New Lead" events in CRM to trigger the AI agent. |
| **Zapier / Make** | Webhook | Low | Use Zapier to map *any* trigger (Sheet row, form, etc.) to `POST /leads`. |

## 2. Intelligence & Research (The "Brain")

The `ICPPersonaAgent` and `LLMClient` currently use simulated responses. They can be connected to:

| Platform | Role | implementation |
|----------|------|----------------|
| **OpenAI (GPT-4o)** | Reasoning & Drafting | Update `backend/core/llm_client.py` to use `openai` lib. |
| **Anthropic (Claude 3.5)** | Copywriting | Excellent for generating human-like cold emails. |
| **Tavily / Serper** | Live Web Search | Give the agent "Search" tools to look up company news before writing. |
| **Perplexity API** | Deep Research | Use for in-depth summary of target companies. |

## 3. Communication Channels (Sending & Receiving)

The `SendOrchestrator` and `InboxListener` are designed to abstract the transport layer:

| Platform | Integration Method | Use Case |
|----------|-------------------|----------|
| **Gmail / GSuite** | Gmail API (OAuth) | Best for personalized, low-volume sending (avoids spam folders). |
| **Microsoft Outlook** | Graph API | Corporate standard for sending. |
| **Instantly / SmartLead** | API | specialized "Cold Outreach" platforms. We can push leads + drafts to them instead of sending directly. |
| **SendGrid / AWS SES** | SMTP | high-volume transactional emails (Not recommended for cold outreach). |

## 4. Notifications & Ops

The `NotifierService` handles alerts:

| Platform | Integration Method | Use Case |
|----------|-------------------|----------|
| **Slack** | Incoming Webhooks | Post "Hot Lead" alerts to a specific #sales channel. |
| **Discord** | Webhooks | Alternative for community-based teams. |
| **PagerDuty** | API | Trigger incidents if the ingest pipeline fails (Enterprise). |

## Recommended Roadmap

1.  **Phase 1 (MVP)**:
    *   **LLM**: Connect **OpenAI** for generation.
    *   **Source**: Manual CSV Upload or **Web Form**.
    *   **Channel**: **Gmail API** (Personal account).

2.  **Phase 2 (Automation)**:
    *   **Source**: **Apollo API** to auto-fetch leads based on criteria.
    *   **Research**: **Tavily Search** to add "Recent News" to emails.
    *   **Ops**: **Slack** notifications for replies.

3.  **Phase 3 (Scale)**:
    *   **Channel**: Deduplicate and push to **SmartLead.ai** for warm-up and sending.
    *   **sync**: Two-way sync with **HubSpot**.

## How to Implement a New Integration

1.  **Ingestion**: Create a new adapter in `backend/services/lead_ingest/adapters/`.
2.  **LLM**: Set `MOCK_LLM=False` and configure the new provider in `backend/core/llm_client.py`.
3.  **Sending**: Implement a generic `EmailSender` interface in `backend/services/sender/providers/`.

## 5. Observability (LLM Ops)

To monitor, trace, and debug LLM calls, we support **LangSmith**.

| Platform | Role | Implementation |
|----------|------|----------------|
| **LangSmith** | Tracing & Debugging | Set `LANGCHAIN_TRACING_V2=true` in `.env`. |

### Setup Instructions
1. Create a LangSmith account and get an API Key.
2. Add the following to your `.env` file:
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_PROJECT=AI_GTM_Agent
   ```
3. The `LLMClient` will automatically wrap the OpenAI client to trace all calls.

| Platform | Role | Implementation |
|----------|------|----------------|
| **Langfuse** | Open Source Tracing | Set `LANGFUSE_PUBLIC_KEY` & `LANGFUSE_SECRET_KEY` in `.env`. |



### Langfuse Setup Instructions
1. Create a Langfuse account (Cloud or Self-Hosted) and get API Keys.
2. Add the following to your `.env` file:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com # Optional if using cloud
   ```
3. The system will detect these keys and automatically switch to the Langfuse OpenAI wrapper.
