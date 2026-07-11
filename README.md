# AI-Powered B2B Outreach Research Agent

## Problem Statement
Sales Development Representatives (SDRs) spend a massive amount of time researching prospects to find genuine pain points or "gaps" to reference in their outreach. Automated outreach often relies on generic templates that yield low reply rates. This Proof of Concept (POC) aims to solve this by automating the deep-dive research process. Given a prospect's name, title, and company, the agent scours the web (via DuckDuckGo) for real, evidenced problems—such as internal challenges mentioned in job postings, engineering blogs, or customer complaints. It then drafts a highly personalized, polite, and concise outreach message that directly addresses that gap without relying on generic sales clichés. Finally, a human-in-the-loop can approve, edit, or regenerate the draft before it is logged as final.

## Architecture

```
                      +---------------------------------------+
                      |               main.py                 |
                      |  (Human-in-the-Loop CLI & DB Logging) |
                      +------------------+--------------------+
                                         |
                                         v
                      +---------------------------------------+
                      |               agent.py                |
                      |        (LangGraph Orchestration)      |
                      +-------+-----------------------+-------+
                              |                       |
                              v                       v
               +-----------------------+     +-----------------------+
               | research_tool.py      |     | draft_tool.py         |
               | (DuckDuckGo Search +  |     | (ChatGroq +           |
               |  BeautifulSoup +      |     |  Strict Prompting)    |
               |  ChatGroq Extraction) |     +-----------------------+
               +-----------------------+
```

## Setup Instructions

1. **Install Dependencies**:
   Ensure you have Python 3.11+ installed. Run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Open `outreach_agent/.env` and insert your Groq API key:
   ```env
   GROQ_API_KEY=your_real_api_key_here
   ```

3. **Run the CLI**:
   ```bash
   python outreach_agent/main.py
   ```

4. **Run the UI (Streamlit)**:
   You can also run the agent with a local graphical interface:
   ```bash
   cd outreach_agent
   streamlit run app.py
   ```
   Navigate to the `outreach_agent` directory and start the CLI:
   ```bash
   cd outreach_agent
   python main.py
   ```

## Example Run

```text
=== AI B2B Outreach Research Agent ===
Prospect Name: Jane Doe
Prospect Title: VP of Engineering
Prospect Company: Acme Corp

[+] Starting agent run...
Agent: Researching Acme Corp...
Found 11 unique URLs to process.
Fetching and analyzing: https://acmecorp.com/careers/vp-engineering
Fetching and analyzing: https://acmecorp.com/engineering-blog/scaling-challenges
...

[+] Agent found 2 potential gap signals.

[0] Type: BLOG_POST (Confidence: 0.9)
Source: https://acmecorp.com/engineering-blog/scaling-challenges
Evidence: "Our transition to microservices has resulted in severe deployment bottlenecks, pushing our Q3 feature release back by four weeks."
Gap: Experiencing severe deployment bottlenecks due to microservices transition, delaying feature releases.

[1] Type: JOB_POSTING (Confidence: 0.75)
Source: https://acmecorp.com/careers/vp-engineering
Evidence: "Looking for an engineering leader with proven experience reducing CI/CD pipeline failure rates."
Gap: High CI/CD pipeline failure rates.

Agent: Drafting message based on top gap...

=== CHOSEN GAP ===
[0] Type: BLOG_POST (Confidence: 0.9)
Source: https://acmecorp.com/engineering-blog/scaling-challenges
Evidence: "Our transition to microservices has resulted in severe deployment bottlenecks, pushing our Q3 feature release back by four weeks."
Gap: Experiencing severe deployment bottlenecks due to microservices transition, delaying feature releases.

=== GENERATED DRAFT ===
Subject: Acme Corp's deployment bottlenecks
Body:
Hi Jane,

I read your recent engineering blog post detailing Acme Corp's transition to microservices and the resulting four-week delay in your Q3 feature release due to deployment bottlenecks. 

Our AI-powered automation platform specifically addresses CI/CD bottlenecks by analyzing code changes to selectively run only required tests and optimize container builds. This mechanism typically cuts deployment times by 40% and significantly reduces pipeline failures. 

Would you be open to a brief call this week to see if we can help streamline your upcoming Q4 releases?

Best,
[Your Name]

Options:
[A]pprove draft
[E]dit draft
[R]egenerate with a different gap
[S]kip
Decision [A/E/R/S]: A
[+] Draft approved and saved to database.
```

## What I'd Add For Production

1. **Robust Search API**: Replace DuckDuckGo (which is rate-limited and often blocks scrapers) with a paid API like Serper.dev, Bing Search API, or Google Custom Search for better recall and reliability.
2. **Headless Browser / Better Scraping**: Use Playwright or Selenium with residential proxies to scrape modern JavaScript-heavy sites (like LinkedIn or Glassdoor) to avoid being blocked by Cloudflare.
3. **CRM Integration**: Integrate with Salesforce, HubSpot, or Outreach.io to pull prospect lists dynamically and push approved drafts directly to the SDR's outbox.
4. **Reply-Rate Feedback Loop**: Track which drafted emails actually receive positive replies. Feed this data back into the LLM as few-shot examples to continuously improve the drafting prompt and confidence ranking.
5. **Caching & Asynchronous Processing**: Cache search results in Redis to avoid redundant queries and use Celery/RQ to process multiple prospects in parallel rather than blocking synchronously in the CLI.
