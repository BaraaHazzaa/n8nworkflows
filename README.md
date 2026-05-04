# 10 n8n Automation Workflows

Import any `.json` file directly into n8n via **Settings → Import Workflow**.  
Set the required environment variables in your n8n instance before activating.

---

## 1. Gmail → Notion Inbox
**File:** `01_gmail_to_notion_inbox.json`  
**Trigger:** Every minute (polls Gmail for unread emails)  
**What it does:** Captures every unread Gmail message and creates a new page in a Notion database — subject as title, sender, date, and "Unread" status auto-filled.  
**Use case:** Zero-inbox GTD system, email triage dashboard.  
**Env vars needed:** `NOTION_DB_ID`

---

## 2. Typeform Response → Slack + Google Sheets
**File:** `02_typeform_to_slack_sheets.json`  
**Trigger:** New Typeform submission  
**What it does:** On each new form response, posts a formatted summary to a Slack channel (#leads) AND appends the full row to a Google Sheet simultaneously.  
**Use case:** Lead capture, event registrations, customer feedback.  
**Env vars needed:** `TYPEFORM_FORM_ID`, `GOOGLE_SHEET_ID`

---

## 3. Daily Morning Digest Email
**File:** `03_daily_digest_email.json`  
**Trigger:** 7am every weekday (cron)  
**What it does:** Fetches the top 5 tech headlines from NewsAPI, formats them into an HTML digest, and emails them to you every morning.  
**Use case:** Personal briefing, team newsletter, executive summary.  
**Env vars needed:** `NEWS_API_KEY`, `MY_EMAIL`

---

## 4. Stripe Payment → HubSpot CRM + Invoice
**File:** `04_stripe_payment_crm_invoice.json`  
**Trigger:** Stripe `payment_intent.succeeded` webhook  
**What it does:** When a payment succeeds, upserts the customer into HubSpot CRM and triggers invoice generation via your invoicing API — all in parallel.  
**Use case:** SaaS billing automation, e-commerce post-purchase flows.  
**Env vars needed:** Stripe webhook secret, HubSpot API credentials

---

## 5. RSS Feed → Auto Tweet
**File:** `05_rss_to_twitter.json`  
**Trigger:** Every 2 hours (schedule)  
**What it does:** Reads your chosen RSS feed, grabs the latest article, and posts it as a tweet with the title, link, and hashtags.  
**Use case:** Content marketing automation, brand news sharing.  
**Env vars needed:** `RSS_FEED_URL`, Twitter/X OAuth credentials

---

## 6. GitHub Issue → Jira Ticket
**File:** `06_github_issue_to_jira.json`  
**Trigger:** GitHub `issues` webhook (opened events only)  
**What it does:** Whenever a new issue is opened on GitHub, automatically creates a linked Jira ticket with the title, description, and GitHub URL — bridging dev and PM workflows.  
**Use case:** Cross-tool dev team coordination, bug tracking.  
**Env vars needed:** `GITHUB_OWNER`, `GITHUB_REPO`, `JIRA_PROJECT_KEY`

---

## 7. Airtable New Record → PDF Report + Email
**File:** `07_airtable_record_to_pdf_email.json`  
**Trigger:** New record created in Airtable  
**What it does:** Generates a styled PDF from the record's fields using html2pdf API, then emails it as an attachment to the email address stored in the record.  
**Use case:** Auto-sending proposals, reports, certificates, or invoices.  
**Env vars needed:** `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_ID`, `HTML2PDF_KEY`

---

## 8. Slack Slash Command → AI Assistant
**File:** `08_slack_openai_bot.json`  
**Trigger:** Webhook (configure as Slack slash command endpoint)  
**What it does:** Exposes a `/ai` slash command in Slack. User types a question, it hits OpenAI GPT-4o, and returns the response directly in the Slack channel.  
**Use case:** Internal AI assistant, team knowledge bot, quick lookups.  
**Env vars needed:** OpenAI API key (configured in n8n credentials)

---

## 9. WooCommerce New Order → Warehouse + Customer SMS
**File:** `09_woocommerce_order_sms.json`  
**Trigger:** WooCommerce `order.created` webhook  
**What it does:** When an order is placed, simultaneously pings your warehouse webhook with fulfilment details AND sends the customer an SMS confirmation via Twilio.  
**Use case:** E-commerce order fulfilment, customer experience automation.  
**Env vars needed:** `WAREHOUSE_WEBHOOK_URL`, `TWILIO_FROM`

---

## 10. Weekly Google Analytics → Slack Report
**File:** `10_weekly_analytics_to_slack.json`  
**Trigger:** Every Monday at 9am (cron)  
**What it does:** Pulls last 7 days of data from GA4 (sessions, users, bounce rate), summarises the totals with a Code node, and posts a clean report to your #marketing Slack channel.  
**Use case:** Weekly marketing standup, exec reporting, growth tracking.  
**Env vars needed:** `GA4_PROPERTY_ID`, Google Analytics credentials

---

## 11. Email Conversations → PDF Export
**File:** `11_email_conversations_to_pdf.json` (+ `email_to_pdf.py`)  
**Trigger:** Webhook (API endpoint)  
**What it does:** Accepts a POST request with a list of email addresses. It then finds all Gmail conversations involving those addresses, fetches the full threads, and uses a Python script (`reportlab`) to generate a clean, styled PDF of the entire conversation, grouped by thread.  
**Use case:** Legal discovery, HR documentation, project archiving, client communication records.  
**Env vars needed:** None (requires `email_to_pdf.py` to be on the n8n server).

---

## How to Import
1. Open your n8n instance
2. Go to **Workflows → New → Import from file**
3. Select any `.json` file from this bundle
4. Add your credentials in the node settings
5. Set environment variables and **Activate** ✅
