# System Architecture

## Overview
PRAM Edu uses a monolithic architecture built with Python Flask, SQLite, and an in-house rule-based AI engine.

## Components
1. **Flask App (`app.py`)**: The main entry point routing HTTP requests to internal services.
2. **Database (`database.py`)**: Handles all SQLite interactions with a focus on security (parameterized queries). Includes tables for users, queries, and audit logs.
3. **AI Engine (`ai_engine.py`)**: A class that processes student queries, sanitizes inputs, detects intents, and generates responses from a knowledge base.
4. **Auth (`auth.py`)**: Manages JWT creation and role-based access control (RBAC).

## Security Measures
- **SQL Injection Prevention**: All queries use `?` placeholders. Inputs are further sanitized by the AI engine before processing.
- **Password Hashing**: SHA-256 hashing applied to all stored passwords.
- **JWT**: Stateless, short-lived (24h) tokens.
- **Audit Logging**: Every action (registration, login, query) is logged in the `audit_logs` table.

## Data Flow
`User -> REST API (Flask) -> Auth Middleware -> AI Engine -> Database -> User`
