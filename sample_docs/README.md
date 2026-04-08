# Sample Documents

Three upload-ready documents for testing the Smart Document Q&A system. Each contains substantial, factual content with verifiable answers — ideal for evaluating retrieval quality, follow-up conversations, and edge-case handling.

## Quick Start

```bash
# Upload
curl -X POST http://localhost:8000/api/v1/documents \
  -H "X-API-Key: your-secret-api-key" \
  -F "file=@sample_docs/company_policy.pdf"

# Poll until status=completed
curl http://localhost:8000/api/v1/tasks/{task_id} -H "X-API-Key: your-secret-api-key"

# Ask a question
curl -X POST http://localhost:8000/api/v1/documents/{document_id}/ask \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of PTO do employees with 5 years of service get?"}'
```

## Documents

### 1. `company_policy.pdf` — Remote Work & Leave Policy (PDF, 4 pages)

A structured corporate policy document for Meridian Technologies covering remote work tiers, equipment stipends, PTO accrual, sick leave, parental leave, bereavement leave, performance reviews, and security requirements. Full of specific numbers, dates, and thresholds.

**Good test questions:**
- "How many PTO days does an employee with 7 years of service receive?"
- "What is the home office setup allowance for Tier 1 remote employees?"
- "What happens if an employee's performance drops below 2.5 on two consecutive reviews?"
- "How long is parental leave for primary caregivers?"

### 2. `async_programming_guide.pdf` — Python Async Programming Guide (PDF, 7 pages)

A technical reference covering coroutines, tasks, the event loop, async context managers, database access patterns, HTTP clients, testing strategies, common pitfalls, and performance benchmarks. Contains concrete numbers, comparisons, and best practices.

**Good test questions:**
- "What is the difference between a coroutine and a Task in asyncio?"
- "How much faster is uvloop compared to the default event loop?"
- "What are the common pitfalls when writing async Python code?"
- "How does asyncpg compare to SQLAlchemy async in query throughput?"

### 3. `quarterly_report_q1_2026.docx` — Q1 2026 Business Report (DOCX)

A full quarterly earnings report with revenue breakdowns by segment and geography, customer metrics, product releases, financial statements, headcount data, and forward guidance. Dense with specific dollar amounts, percentages, and year-over-year comparisons.

**Good test questions:**
- "What was the total revenue in Q1 2026?"
- "Which geographic region grew the fastest?"
- "What is the net revenue retention rate for the Enterprise SaaS segment?"
- "What is the company's Q2 2026 revenue guidance?"
- "How many employees does the company have in London?"

## Why These Three

| Document | Tests |
|----------|-------|
| Policy PDF | Exact fact retrieval, threshold/eligibility lookups, structured section navigation |
| Technical PDF | Concept explanation, comparison questions, multi-section synthesis |
| Business DOCX | Numeric extraction, year-over-year comparison, cross-section analysis, DOCX parsing |

The mix covers both file formats (PDF + DOCX), three content domains (HR policy, technical, financial), and multiple question types (factual, comparative, analytical) — matching the evaluation criteria in the assignment.
