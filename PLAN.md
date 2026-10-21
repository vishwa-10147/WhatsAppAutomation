# Implementation plan

This checklist tracks verified milestones. A checked item means its code exists and its stated verification passed; planned work remains unchecked until implemented.

## Phase 1 — Foundation

- [ ] Initialize the repository layout, local configuration, and developer documentation.
- [ ] Set up FastAPI, typed settings, structured logging, and health/readiness endpoints.
- [ ] Set up PostgreSQL, SQLAlchemy, Alembic, and the initial organization/authentication schema.
- [ ] Implement registration/login and organization membership authorization.
- [ ] Set up React, TypeScript, Vite, and a responsive dashboard shell backed by API health/data endpoints.
- [ ] Add Docker Compose for PostgreSQL, Redis, API, worker, and frontend, with health checks.
- [ ] Verify migrations and local startup; record limitations and commands in README.

## Phase 2 — Official WhatsApp integration

- [x] Add account configuration with encrypted provider credentials.
- [x] Implement Cloud API adapter and explicit mock adapter.
- [x] Verify webhook challenge/signature, persist/dedupe events, and process inbound messages/statuses.
- [x] Add consent-aware text/template/media dispatch, provider error mapping, retries, and rate limits.

## Phase 3 — Workflow engine and visual builder

- [x] Define versioned workflow schema and validate graph topology/configuration.
- [x] Database models for workflows, versions, executions, node_executions, scheduled_jobs.
- [x] Alembic migration for workflow tables.
- [x] Workflow validation, execution engine with node-level tracking.
- [x] REST API for workflows, versions, executions, scheduled jobs.
- [x] Scheduled jobs (cron + one-time) with worker processing.
- [x] React Flow visual editor with node palette, drag-drop, config panel.
- [x] Node execution tracking with input/output/error logging.
- [ ] Persist redacted node inputs/outputs/errors and support inspect/retry/dead-letter operations.

## Phase 4 — Contacts and inbox

- [ ] Add tenant-scoped contacts, tags, custom fields, consent, import/export, search, and segmentation.
- [ ] Persist conversations/messages and implement assignment, status, internal notes, activity, and human takeover.
- [ ] Build inbox views connected to the API.

## Phase 5 — AI assistant

- [ ] Add provider abstraction, deterministic fallback, prompt configuration, and confidence/handoff policy.
- [ ] Add intent classification, structured extraction, conversation context, and optional document RAG.
- [ ] Test injection resistance and ensure unsupported business facts are not invented.

## Phase 6 — Scheduling, campaigns, and connectors

- [ ] Add time-zone-aware one-time/recurring schedules and consent-aware template campaigns.
- [ ] Add connector interfaces for webhooks, REST, commerce, payments, CRM, spreadsheets, and notifications.
- [ ] Add campaign preview/test-send, pause/resume/cancel, and verified event-driven restaurant notifications.

## Phase 7 — Production hardening

- [ ] Add tenant/auth/workflow/webhook/dispatch/scheduler/AI integration coverage and frontend critical-flow coverage.
- [ ] Add analytics from persisted data, operational metrics, alerts, audit review, and retention/deletion tooling.
- [ ] Complete deployment, backup/restore, privacy, security, and Meta approval documentation.
- [ ] Verify the complete local Docker path and record what still requires external credentials/approval.

## Current implementation checklist

- [x] Inspected workspace: empty directory, no existing repository or source to preserve.
- [x] Wrote initial architecture and phased plan.
- [ ] Implement and verify Phase 1 foundation.
- [ ] Review and correct starter implementation gaps discovered during resume.
- [x] Replace process-local random access tokens with signed expiring tokens and verify organization membership on authenticated requests.
- [x] Replace unfinished feature screens with explicit in-development states and remove fabricated dashboard counts.
- [x] Configure Compose migrations before API/worker startup and add the worker entry point.
- [x] Run a frontend production build and an API registration/login/readiness smoke check.
- [ ] Run automated backend tests and a full dependency audit.
