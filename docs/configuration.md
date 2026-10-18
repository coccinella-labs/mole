# Configuration

Configure Mole using environment variables.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values:

```bash
cp .env.example .env
```

### Backend Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | Bearer token required by every endpoint | `your-secret-api-key` |

PostgreSQL and Redis were removed along with the unused Celery stack; there is
no database or broker behind this service. See issue [#101](https://github.com/coccinella-labs/mole/issues/101).

### Frontend Variables

Frontend variables use the `VITE_` prefix. Vite inlines any variable with that
prefix into the client bundle at build time, so these are build arguments rather
than runtime settings; see the Vite migration in
[#110](https://github.com/coccinella-labs/mole/pull/110).

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_BACKEND_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_API_KEY` | Bearer token sent by the frontend | none |

## Docker Configuration

When using Docker Compose, environment variables are set in the `docker-compose.yml` file.

## Local Development

For local development without Docker:

1. **Backend:** Set environment variables or create `.env` file in `backend/` directory
2. **Frontend:** Set `VITE_BACKEND_URL` and `VITE_API_KEY` in `frontend/.env` or the environment. Only the `VITE_` prefix is exposed to the bundle; other variables are not readable from client code.

## Security Notes

- Never commit `.env` files to version control
- Use strong passwords in production
- Configure HTTPS in production deployments
