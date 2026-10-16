# Testing

Comprehensive testing ensures mol-platform works correctly.

## Test Structure

```
tests/
├── api_test.py          # API integration tests
├── test_molecule_generation.py  # Unit tests for core logic
├── e2e/
│   └── test_api_e2e.py  # End-to-end API tests
```

## Running Tests

### Backend Tests

```bash
cd backend

# Unit tests
python -m pytest tests/test_molecule_generation.py -v

# E2E tests
python -m pytest tests/e2e/ -v

# All tests
python -m pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Docker Tests

```bash
# Build and run tests in containers
docker-compose up --build
# Then run tests in separate terminals
```

## Test Coverage

Current test coverage includes:

- Molecule generation with various mutations
- Property calculation
- API endpoints (health, generation)
- Input validation
- Error handling

## Writing Tests

### Backend (pytest)

```python
import pytest
from src.main import MoleculeGenerator


def test_example():
    generator = MoleculeGenerator()
    result = generator.generate_random_molecule("CCO")
    assert result is not None
```

### Frontend (Jest/React Testing Library)

```javascript
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app', () => {
  render(<App />);
  expect(screen.getByText('mol-platform')).toBeInTheDocument();
});
```

## CI/CD Testing

Tests run automatically on:
- Push to main branch
- Pull requests

See [CI/CD](cicd.md) for details.
