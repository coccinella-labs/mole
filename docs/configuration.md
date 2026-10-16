# Configuration

Configure mol-platform using environment variables.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values:

```bash
cp .env.example .env
```

### Backend Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@database/mol_platform` |
| `CELERY_BROKER_URL` | Redis URL for Celery broker | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery results | `redis://redis:6379/0` |

### Frontend Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_BACKEND_URL` | Backend API URL | `http://localhost:8000` |

## Docker Configuration

When using Docker Compose, environment variables are set in the `docker-compose.yml` file.

## Local Development

For local development without Docker:

1. **Backend:** Set environment variables or create `.env` file in `backend/` directory
2. **Frontend:** Set `REACT_APP_BACKEND_URL` in `frontend/.env` or environment

## Security Notes

- Never commit `.env` files to version control
- Use strong passwords in production
- Configure HTTPS in production deployments
