# divis-test
# divisadero

## FastAPI Application

A basic FastAPI application for Divisadero.

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

### Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint
