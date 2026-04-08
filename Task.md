
Assignment: Smart Document Q&A System

Build an API where users can upload documents (PDFs/DOCX) and ask natural language questions that get answered using the document content.

What the system should do

Accept document uploads and process them for search

Answer questions about uploaded documents using retrieved context and an LLM

Handle follow-up questions within a conversation

That's it. How you design the API, structure the code, chunk the documents, craft the prompts, and handle failures is up to you.

Tech Stack

Layer	Use
API	FastAPI
Database	SQLAlchemy + Alembic + MySQL or PostgreSQL
Background tasks	Celery + Redis
Vector search	FAISS
Embeddings	Sentence Transformers
LLM	OpenAI API
Infrastructure

Provide a docker-compose.yml — docker-compose up should start everything with no manual steps

Include .env.example with required variables

Include 3 sample documents in the repo so we can test immediately

What we'll judge you on

Retrieval quality — does your chunking and search strategy actually return useful results, or does the LLM get garbage context?

LLM usage — does your system answer from the document or hallucinate? What happens when the answer isn't in the document?

Async design — does a large document upload block the API? Can we check progress?

Failure handling — what happens when OpenAI is down, the document is corrupt, or the question has no answer?

API design — is it intuitive? Would another developer understand it without reading your code?

Code structure — is it modular and typed, or is everything in one file?

Docker — does it actually work with one command?

Your README — do you explain why you made your design choices, not just what you built?

Submission

Public GitHub repo with a README that includes setup instructions, sample API calls, and a Design Decisions section

Clean commit history
