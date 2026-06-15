# Backend API

FastAPI-based REST API server providing endpoints for schematic parsing, placement optimization, routing, validation, and Gerber generation.

## 🚀 Quick Start

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

API documentation will be available at: `http://localhost:8000/docs`

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/refresh` - Refresh access token

### Projects
- `GET /projects` - List all projects
- `POST /projects` - Create new project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Schematics
- `POST /schematics/upload` - Upload schematic file (.sch, .kicad_sch, .json)
- `POST /schematics/parse` - Parse uploaded schematic
- `GET /schematics/{id}/components` - List components
- `GET /schematics/{id}/nets` - List nets

### Placement
- `POST /placement/optimize` - Run auto-placement algorithm
- `PUT /placement/manual` - Update manual component positions
- `POST /placement/validate` - Validate placement against rules

### Routing
- `POST /routing/auto` - Run deterministic A* router
- `POST /routing/differential` - Route differential pairs
- `POST /routing/impedance` - Route with impedance control
- `POST /routing/validate` - Validate routes (DRC)

### Calculations
- `POST /calculations/impedance` - Calculate impedance for trace geometry
- `POST /calculations/trace-width` - Calculate required trace width for current
- `POST /calculations/clearance` - Calculate minimum clearance for voltage

### Manufacturing
- `POST /gerber/generate` - Generate Gerber files from design
- `GET /gerber/{id}/download` - Download Gerber ZIP package
- `POST /gerber/validate` - Validate Gerber files against fab capabilities

## 🔑 Authentication

All endpoints (except register/login) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## 📝 Example Usage

### Create a Project
```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "My PCB", "description": "Test board"}'
```

### Upload Schematic
```bash
curl -X POST "http://localhost:8000/schematics/upload" \
  -F "file=@schematic.sch" \
  -F "project_id=123"
```

### Run Auto-Router
```bash
curl -X POST "http://localhost:8000/routing/auto" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 123, "strategy": "optimized"}'
```

### Generate Gerbers
```bash
curl -X POST "http://localhost:8000/gerber/generate" \
  -H "Authorization: Bearer <token>" \
  -d '{"project_id": 123}'
```

## 🗄️ Database

The API uses SQLite for development and supports PostgreSQL for production. Configure via environment variables:

```bash
export DATABASE_URL="sqlite:///./pcb_design.db"
# or for production:
export DATABASE_URL="postgresql://user:pass@localhost:5432/pcb_design"
```

## 🧪 Testing

Run API tests:
```bash
pytest tests/test_api.py -v
```

## ⚙️ Configuration

Environment variables:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT signing key (required)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

## 📚 Dependencies

See `requirements.txt` for full list. Key dependencies:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `sqlalchemy`: ORM
- `pydantic`: Data validation
- `python-jose`: JWT handling
