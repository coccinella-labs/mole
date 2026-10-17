# API Authentication

Mole uses API key authentication to secure access to all endpoints.

## Setup

1. Generate a secure API key:
   ```bash
   openssl rand -hex 32
   ```

2. Set the key in the backend environment:
   - For Docker: `API_KEY=your-key docker-compose up`
   - For local: Add `API_KEY=your-key` to `backend/.env`

## Usage

Include the API key in requests:

- **Header**: `Authorization: Bearer your-api-key`
- **CLI**: `mol-platform --api-key your-api-key --health`

## Security Notes

- Keep API keys secret and rotate regularly.
- Use strong, random keys (32+ characters).
- In production, store keys in secure secret managers.
- Monitor for unauthorized access attempts.
