# Installation

This guide covers how to install and set up Mole for development and deployment.

## Prerequisites

### Required (All Platforms)

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/)

### Recommended (macOS via Homebrew)

If you are developing or running tests locally on macOS, install the following using **Homebrew**:

```bash
brew install docker docker-compose
brew install python@3.12
brew install node
brew install git
```

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/coccinella-labs/mole.git
cd mole
```

### 2. Choose Your Installation Method

#### Option A: Docker Deployment (Recommended)

No additional setup required. Docker handles all dependencies.

#### Option B: Local Development Setup

##### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main  # Starts on http://localhost:8000
```

`python -m src.main` is the working form. `src/main.py` uses relative imports
(`from .config import settings`), so running the file directly with
`python src/main.py` fails with `ImportError: attempted relative import with no
known parent package`.

##### API Key Setup

The backend requires an API key for authentication. Generate a secure key:

```bash
openssl rand -hex 32
```

For Docker: Set `API_KEY=your-generated-key` in your environment or create a `.env` file.

For Local: Copy `backend/.env.example` to `backend/.env` and set `API_KEY=your-generated-key`.

##### Frontend Setup (Run in Separate Terminal)
```bash
cd frontend
npm ci
npm run dev  # Vite dev server on http://localhost:3000
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration](configuration.md)
