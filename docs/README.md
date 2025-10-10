# Acadexa — Voice-Controlled LMS (Starter)

## Quick start (local)
1. Create virtual env: `python -m venv venv`
2. Activate venv:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
3. Install dependencies:
   `pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose passlib[bcrypt]`
4. Run backend:
   `uvicorn backend.main:app --reload --port 8000`
5. Open `web/index.html` in browser for simple voice test.

## Structure
- backend/  — FastAPI app
- nlp/      — intent parsing rules
- web/      — frontend demo
- db/       — schema & seed
- docs/     — documentation
