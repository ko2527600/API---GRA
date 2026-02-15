# Quick Start Guide - GRA External Integration API

## 5-Minute Setup

### Windows
```bash
setup.bat
venv\Scripts\activate.bat
uvicorn app.main:app --reload
```

### Linux/Mac
```bash
bash setup.sh
source venv/bin/activate
uvicorn app.main:app --reload
```

## Access the API

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure at a Glance

```
app/
├── main.py          → FastAPI app entry point
├── config.py        → Environment configuration
├── constants.py     → GRA error codes & constants
├── logger.py        → Logging setup
├── api/             → API endpoints (to be implemented)
├── models/          → Database models (to be implemented)
├── schemas/         → Pydantic schemas
├── services/        → Business logic (to be implemented)
└── utils/           → Utilities (encryption, validation, tax calc)
```

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application |
| `app/config.py` | Configuration from .env |
| `app/constants.py` | GRA error codes, endpoints, constants |
| `app/utils/validators.py` | GRA validation rules |
| `app/utils/tax_calculator.py` | Tax/levy calculations |
| `app/utils/encryption.py` | Encryption utilities |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment template |

## Common Commands

```bash
# Run the app
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Format code
black app tests

# Lint code
flake8 app tests

# Type checking
mypy app
```

## Configuration

Edit `.env` file to configure:
- Database connection
- GRA API endpoint
- Security keys
- Logging level
- Rate limiting

## Next Phase

Phase 1.2: Database Setup
- Create PostgreSQL schema
- Design database tables
- Set up migrations

See `SETUP.md` for detailed instructions.
