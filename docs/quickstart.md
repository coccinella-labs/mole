# Quick Start

Get Mole up and running quickly with Docker.

## Docker Deployment (Recommended)

1. **Start the services:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - **Frontend:** http://localhost:3000
   - **API Documentation:** http://localhost:8000/docs
   - **API Health:** http://localhost:8000/health

3. **Stop the services:**
   ```bash
   docker-compose down
   ```

## Local Development

### Backend
```bash
cd backend
source venv/bin/activate
python src/main.py
```
API available at http://localhost:8000

### Frontend
```bash
cd frontend
npm start
```
Frontend available at http://localhost:3000

## Testing

Run the test suite:
```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## CLI Usage

Once the backend is running, install and use the CLI for command-line access:

```bash
# Install CLI
cd backend
python3 -m venv venv && source venv/bin/activate && pip install build && python -m build
pipx install dist/mol_platform-*-py3-none-any.whl

# Test health
mol-platform --api-key your-key --health

# Generate molecule
mol-platform --api-key your-key --generate "CCO"
```

## What's Next?

- [API Documentation](../api/overview.md)
- [Configuration](configuration.md)
- [Contributing](../contributing.md)
