# Task Compliance Checklist

This checklist maps current implementation status to assignment requirements in `Task.md`.

## Core Functional Requirements

- [x] Upload PDF/DOCX documents
- [x] Process documents asynchronously for search
- [x] Ask grounded questions using retrieved context + LLM
- [x] Support follow-up questions in conversation threads

## Required Technology Stack

- [x] API: FastAPI
- [x] Database: SQLAlchemy + Alembic + PostgreSQL
- [x] Background tasks: Celery + Redis
- [x] Vector search: FAISS
- [x] Embeddings: Sentence Transformers
- [x] LLM integration: OpenAI API

## Infrastructure Requirements

- [x] `docker-compose.yml` starts required services with one command
- [x] `.env.example` includes required variables
- [x] Repository includes at least 3 sample documents

## Evaluation Criteria Coverage

- [x] Retrieval quality strategy documented (hybrid retrieval + reranking)
- [x] LLM grounding behavior documented
- [x] Async progress tracking via task status endpoint
- [x] Failure handling for parser, queue, and LLM errors
- [x] Modular typed code structure
- [x] README includes setup, sample calls, and design decisions

## Verification Notes

- Full test suite passes.
- Docker stack validated: `app`, `db`, `redis`, `worker`.
- Postman collection endpoints align with implemented API routes.
