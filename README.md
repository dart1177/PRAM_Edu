# PRAM Edu - Secure AI Student Query API

A production-ready Python Flask backend for an educational mobile app, with AI intent detection for automated student queries.

## Features
- Secure JWT authentication with Role-Based Access Control (RBAC).
- SQLite database with strict parameterized queries protecting against SQL injection.
- Rule-based AI Engine detecting intents and maintaining a knowledge base.
- Comprehensive audit logging of all requests.
- Ready for deployment (Procfile included).

## Setup
1. Clone the repository.
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set `JWT_SECRET_KEY`.
6. Run tests: `pytest tests/ -v`
7. Start server: `python app.py`

## Documentation
Check the `docs/` folder for architecture details, API reference, and research paper draft.
