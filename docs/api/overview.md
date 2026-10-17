# API Overview

Mole provides a RESTful API for molecular generation and analysis.

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** Configure as needed

## Authentication

Currently, no authentication is required. Add authentication headers in production.

## Response Format

All responses are in JSON format.

## Error Handling

- `200`: Success
- `400`: Bad Request (invalid input)
- `500`: Internal Server Error

## API Documentation

Interactive API documentation available at `/docs` when the server is running.

## Rate Limiting

Not implemented. Consider adding rate limiting for production use.
