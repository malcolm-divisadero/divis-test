# Architecture Documentation

## Overview

This document outlines the architecture rules and patterns for the Divisadero project.

## Architecture Pattern

```
Frontend (React) → Backend API (FastAPI) → Supabase Database
```

The application follows a **three-tier architecture** where:
- **Frontend**: React application that communicates only with the backend API
- **Backend**: FastAPI server that handles all database operations and business logic
- **Database**: Supabase (PostgreSQL) for data storage

## Core Rules

### 1. Frontend → Backend Communication

**Rule: Frontend MUST only connect to backend API endpoints. NO direct Supabase connections from the frontend.**

✅ **Allowed:**
- Frontend makes HTTP requests to backend endpoints (e.g., `GET /brands`, `POST /org`)
- Frontend uses `fetch()` or similar HTTP clients to call backend APIs
- Frontend receives JSON responses from backend

❌ **NOT Allowed:**
- Direct Supabase client calls from frontend code
- Importing `@supabase/supabase-js` in frontend components
- Querying Supabase tables directly from React components
- Using Supabase real-time subscriptions from frontend (unless explicitly approved)

**Exception:** Supabase Auth client may be used in the frontend for authentication flows only, but all data operations must go through the backend.

### 2. Backend → Supabase Communication

**Rule: Backend is the ONLY layer that connects to Supabase for data operations.**

✅ **Allowed:**
- Backend uses Supabase Python client (`supabase` package)
- Backend queries, inserts, updates, and deletes data in Supabase
- Backend handles all database operations and business logic
- Backend can use service_role key for admin operations

### 3. API Endpoints

**Rule: All data operations must be exposed through RESTful API endpoints.**

**Pattern:**
```
GET    /resource          → List all resources
GET    /resource/{id}     → Get specific resource
POST   /resource          → Create new resource
PUT    /resource/{id}     → Update resource
DELETE /resource/{id}     → Delete resource
```

**Example:**
- `GET /brands` → Returns all brands
- `GET /brands/{slug}` → Returns specific brand by slug
- `POST /brands` → Creates a new brand (superuser only)

## File Structure

```
divis-test/
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── lib/
│   │   │   └── supabase.js    # ⚠️ DO NOT USE for data operations
│   │   └── App.jsx            # Uses fetch() to call backend APIs
│   └── .env                   # Frontend environment variables
│
├── backend/               # FastAPI backend application
│   ├── main.py                # API endpoints
│   ├── database.py             # Supabase connection utilities
│   ├── migrations/             # SQL migration files
│   └── .env                    # Backend environment variables (Supabase keys)
│
└── doc/                   # Documentation
    ├── ARCHITECTURE.md         # This file
    ├── product_requirements.md  # Product requirements
    └── SUPABASE_SETUP.md       # Supabase setup guide
```

## Adding New Features

### Frontend Feature Checklist

When adding a new feature that needs data:

1. ✅ Identify the data you need
2. ✅ Check if a backend endpoint exists (`GET /resource`)
3. ✅ If not, create the backend endpoint first
4. ✅ Use `fetch()` in frontend to call the backend endpoint
5. ✅ Handle loading and error states
6. ❌ DO NOT create a Supabase query in the frontend

**Example - Adding a Categories Feature:**

```javascript
// ✅ CORRECT: Frontend calls backend API
const fetchCategories = async () => {
  const response = await fetch('http://localhost:8000/categories')
  const data = await response.json()
  setCategories(data.categories)
}

// ❌ WRONG: Direct Supabase call
import { supabase } from './lib/supabase'
const { data } = await supabase.from('categories').select('*')
```

### Backend Feature Checklist

When adding a new backend endpoint:

1. ✅ Create the endpoint in `backend/main.py`
2. ✅ Use `get_client()` from `database.py` to get Supabase client
3. ✅ Query Supabase using the client
4. ✅ Add error handling
5. ✅ Return JSON response
6. ✅ Update API documentation if needed

**Example:**

```python
@app.get("/categories")
async def get_categories():
    """Get all categories"""
    try:
        supabase_client = get_client(use_service_role=False)
        response = supabase_client.table("categories").select("*").execute()
        return {
            "status": "success",
            "count": len(response.data) if response.data else 0,
            "categories": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

## Benefits of This Architecture

1. **Security**: Database credentials and structure are not exposed to the frontend
2. **Centralized Logic**: Business logic lives in one place (backend)
3. **Validation**: Data validation happens server-side before database operations
4. **Caching**: Backend can implement caching strategies
5. **Rate Limiting**: Can be implemented at the API level
6. **Testing**: Easier to test backend logic independently
7. **Scalability**: Can add multiple frontends (web, mobile) using the same API

## Environment Variables

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
# NO Supabase keys in frontend .env
```

### Backend (.env)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Common Patterns

### Fetching Data in Frontend

```javascript
const [data, setData] = useState([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)

const fetchData = async () => {
  setLoading(true)
  setError(null)
  try {
    const response = await fetch(`${API_URL}/resource`)
    const result = await response.json()
    if (result.status === 'success') {
      setData(result.data)
    } else {
      setError(result.error)
    }
  } catch (err) {
    setError(err.message)
  } finally {
    setLoading(false)
  }
}
```

### Creating Data via Backend

```javascript
const createResource = async (resourceData) => {
  try {
    const response = await fetch(`${API_URL}/resource`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(resourceData)
    })
    const result = await response.json()
    return result
  } catch (error) {
    console.error('Error creating resource:', error)
    throw error
  }
}
```

## Migration Guide

If you find code that violates these rules:

1. **Identify**: Find direct Supabase calls in frontend
2. **Create Backend Endpoint**: Add the equivalent endpoint in `backend/main.py`
3. **Update Frontend**: Replace Supabase calls with `fetch()` calls to backend
4. **Test**: Verify the functionality works the same way
5. **Remove**: Delete unused Supabase imports from frontend

## Questions?

If you're unsure whether something follows the architecture rules, ask:
- "Does this make a direct Supabase call from the frontend?" → If yes, refactor it
- "Is there a backend endpoint for this?" → If no, create one first
- "Can I add this logic in the backend instead?" → Usually yes!

## Enforcement

- Code reviews should check for direct Supabase usage in frontend
- Linting rules can be added to prevent Supabase imports in frontend
- Documentation should always show backend API usage, not direct Supabase calls


