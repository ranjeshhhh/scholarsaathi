# ScholarSaathi

ScholarSaathi is a full-stack prototype for SIH problem statement **SIH26239: AI-Enabled Scholarship and Fellowship Management System for Scheduled Tribes**. The experience is designed around a clear flow: profile → opportunity discovery → eligibility explanation → documents → application tracking.

## Data integrity

This project does not include verified, currently open government scholarship data. The sample catalogue is deliberately labelled **Demo**. It has no invented application deadlines or award amounts and cannot be treated as a live government listing. Sample source links go to the relevant ministry/portal homepages, not to a claim that a specific scheme is accepting applications. Each record exposes a verification state and source URL. The API marks a record closed when its recorded deadline has passed; it never silently refreshes an old record.

## What works in this prototype

- Responsive React/TypeScript interface with overview, opportunity search, filters, details, official-source links, saved records, application tracker, profile editor, document checklist, conversational guidance and local admin record entry.
- Demo mode stores browser interactions in local storage. This is for a presentation on one device and is not a multi-user or secure account system.
- FastAPI REST service with password hashing, signed bearer tokens, role checks, student profiles, searchable opportunities, deterministic eligibility explanations, application tracking, saved opportunities, reminder records and admin verification/archive endpoints.
- SQLAlchemy models use PostgreSQL when configured and SQLite for local setup. The current bootstrap creates schema tables automatically; move to Alembic migrations before production.
- API documentation is available at `/docs` while the backend is running.

The web UI currently runs in local demo mode; it does not send student profile or application data to the API. Secure document upload, email/SMS reminder delivery, password reset, verified data feeds, Hindi translation, institution workflows and external LLM integration are not configured. The assistant clearly identifies its limited demo knowledge source. Do not deploy this prototype with real student data until those paths and deployment controls are implemented.

## Container deployment

The included Compose stack runs PostgreSQL, the FastAPI service and an Nginx-served frontend behind one port. The web container proxies `/api/*` to the API and `/docs` to FastAPI. This is suitable for a private demo or deployment rehearsal; it is not a hardened production hosting setup.

1. Install Docker Desktop (or Docker Engine with the Compose plugin) and start it.
2. From this `outputs` directory, copy `.env.example` to `.env`.
3. Replace both secrets. Use URL-safe hex values so the PostgreSQL URL parses cleanly. For example, generate separate values with `openssl rand -hex 32`.
4. Build and start the stack: `docker compose up --build -d`.
5. Open `http://localhost:8080`. Check `http://localhost:8080/api/health` and the API docs at `http://localhost:8080/docs`.
6. Create the first administrator interactively with `docker compose exec api python -m app.create_admin`.

PostgreSQL data persists in the `postgres_data` volume. `docker compose down` stops containers and keeps the volume. Back up the database before upgrading or moving hosts. Do not commit `.env`. For a public deployment, put TLS and a domain in front of Nginx, restrict network access, move secrets into the hosting platform’s secret store, configure backups/monitoring, add database migrations, and review security/privacy controls. The API currently creates its tables at startup for prototype convenience.

Docker is not installed in the authoring environment, so the Compose deployment itself was not executed here. The frontend production build and backend API tests were verified separately.

## Run locally

Requirements: Node.js 20+, Python 3.11+, and (optionally) PostgreSQL.

### API

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:JWT_SECRET_KEY = "replace-with-a-long-random-secret"
$env:CORS_ORIGINS = "http://localhost:5173"
uvicorn app.main:app --reload
```

SQLite is the default and creates `backend/scholarsaathi.db`. For PostgreSQL set `DATABASE_URL` to `postgresql+psycopg://user:password@localhost:5432/scholarsaathi`. Create the first administrator from the backend directory with `py -m app.create_admin`.

### Web app

In a second terminal:

```powershell
cd outputs
npm install
npm run dev
```

Open the local Vite URL shown in the terminal. The frontend does not require the API for its local demo interactions.

### API checks

```powershell
cd backend
pip install httpx pytest
pytest
```

## Main API routes

| Route | Purpose |
|---|---|
| `POST /auth/register`, `POST /auth/login` | Student registration and JWT login |
| `GET/PATCH /profile` | Authenticated student profile |
| `GET /scholarships`, `GET /fellowships`, `GET /scholarships/{id}` | Public, paginated discovery and details |
| `POST /eligibility/check`, `GET /recommendations` | Rule-based comparison and missing information |
| `POST/GET /applications`, `PATCH /applications/{id}` | Application tracking |
| `POST/DELETE /saved-scholarships` | Save or remove an opportunity |
| `POST /reminders`, `GET /notifications` | Store reminder dates (no outbound delivery configured) |
| `POST /ai/chat` | Catalogue-grounded deterministic demo answer |
| `POST/PATCH/DELETE /admin/scholarships` | Admin create, edit and archive |
| `POST /admin/verify/{id}` | Admin verification action and verification date |

## Data model and security notes

Separate relational tables cover users, student profiles, providers, scholarships, applications, saved opportunities and reminders. Passwords use Argon2 hashing; access tokens expire after 12 hours; admin endpoints use role checks; Pydantic validates input; SQLAlchemy parameterizes database access; CORS is configurable. Set a strong secret, HTTPS, production database, backup policy, rate limiting, audit logs, least-privilege storage and privacy retention rules before deployment. No credentials belong in the frontend.

There are no demo login credentials. Register a student through the API. Create an administrator with the local CLI command above. Do not expose the admin bootstrap process in a public deployment.

## Deployment direction

Build the web client with `npm run build`, serve the generated `dist` directory using a static host, and run the API with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Configure PostgreSQL, `DATABASE_URL`, a strong `JWT_SECRET_KEY`, and `CORS_ORIGINS` in the hosting provider’s secret manager. Use HTTPS and a managed database. Add reviewed Alembic migrations and operational monitoring before production use.

## Future work

Add official source provider adapters with provenance and scheduled re-verification; publish only opportunities confirmed by source owners; connect the web client to the API and authentication; add institutional verification workflow; implement encrypted private document storage and consent controls; configure reminder delivery; and add a backend LLM integration with retrieval, prompt-injection controls and source citations. Any live record should include its provider, official URL, last verified date, current status and evidence of verification.

