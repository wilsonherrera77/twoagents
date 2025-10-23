#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Generator - Template-Based Code Generation
================================================

Genera codigo funcional usando templates pragmaticos.
Sin LLM, sin GPU - solo Python + templates inteligentes.

Soporta:
- REST APIs (FastAPI)
- Web Scrapers
- Simple Games (Pygame)
- CRUD applications
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def generate_project(
    objective: str,
    architecture: Dict[str, Any],
    output_dir: Path
) -> List[str]:
    """
    Generar proyecto completo basado en arquitectura.

    Args:
        objective: Objetivo del proyecto
        architecture: Dict con approach, modules, etc
        output_dir: Directorio de salida

    Returns:
        files_created: Lista de paths creados
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detectar tipo de proyecto
    obj_lower = objective.lower()

    if "api" in obj_lower or "rest" in obj_lower:
        return generate_rest_api(objective, architecture, output_dir)
    elif "scrap" in obj_lower:
        return generate_web_scraper(objective, architecture, output_dir)
    elif "game" in obj_lower or "juego" in obj_lower:
        return generate_simple_game(objective, architecture, output_dir)
    else:
        return generate_generic_app(objective, architecture, output_dir)


# ============================================================================
# REST API GENERATOR
# ============================================================================

def generate_rest_api(
    objective: str,
    architecture: Dict[str, Any],
    output_dir: Path
) -> List[str]:
    """Generar API REST con FastAPI"""
    files = []

    # Leer configuracion de arquitectura (V4 enhanced)
    config = architecture.get("config", {})
    modules = architecture.get("modules", [])

    # Detectar features desde config O desde objective (fallback)
    has_auth = config.get("auth") == "JWT" or "auth" in objective.lower() or "jwt" in objective.lower()
    has_db = config.get("orm") == "sqlalchemy" or any(kw in objective.lower() for kw in ["database", "bd", "postgres", "sqlite"])
    has_rate_limit = "rate_limit" in config
    has_metrics = config.get("metrics") == "prometheus"
    has_logging = config.get("logging") == "structured_json"
    has_docker = config.get("containerization") == "docker"
    has_ci_cd = config.get("ci_cd") in ["github_actions", "gitlab_ci"]
    has_load_tests = config.get("load_testing") == "locust"
    coverage_target = config.get("coverage_target", 70)

    # main.py
    cors_config = config.get("cors", "restricted")
    main_content = generate_fastapi_main(has_auth, has_db, has_rate_limit, has_metrics, cors_config)
    main_file = output_dir / "main.py"
    main_file.write_text(main_content, encoding='utf-8')
    files.append(str(main_file))

    # config.py
    config_content = generate_config(has_auth)
    config_file = output_dir / "config.py"
    config_file.write_text(config_content, encoding='utf-8')
    files.append(str(config_file))

    if has_db:
        # database.py
        db_content = generate_database()
        db_file = output_dir / "database.py"
        db_file.write_text(db_content, encoding='utf-8')
        files.append(str(db_file))

        # models.py
        models_content = generate_models(has_auth)
        models_file = output_dir / "models.py"
        models_file.write_text(models_content, encoding='utf-8')
        files.append(str(models_file))

        # alembic.ini
        alembic_content = generate_alembic_ini()
        alembic_file = output_dir / "alembic.ini"
        alembic_file.write_text(alembic_content, encoding='utf-8')
        files.append(str(alembic_file))

    # routes.py
    routes_content = generate_routes(has_auth, has_db)
    routes_file = output_dir / "routes.py"
    routes_file.write_text(routes_content, encoding='utf-8')
    files.append(str(routes_file))

    if has_auth:
        # auth.py
        auth_content = generate_auth()
        auth_file = output_dir / "auth.py"
        auth_file.write_text(auth_content, encoding='utf-8')
        files.append(str(auth_file))

    # tests/ directory with comprehensive tests
    tests_dir = output_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # tests/__init__.py
    (tests_dir / "__init__.py").write_text("", encoding='utf-8')
    files.append(str(tests_dir / "__init__.py"))

    # tests/test_api.py
    test_api_content = generate_api_tests(has_auth)
    test_api_file = tests_dir / "test_api.py"
    test_api_file.write_text(test_api_content, encoding='utf-8')
    files.append(str(test_api_file))

    # tests/test_integration.py
    test_integration_content = generate_integration_tests(has_auth, has_db)
    test_integration_file = tests_dir / "test_integration.py"
    test_integration_file.write_text(test_integration_content, encoding='utf-8')
    files.append(str(test_integration_file))

    # tests/conftest.py
    conftest_content = generate_conftest(has_db)
    conftest_file = tests_dir / "conftest.py"
    conftest_file.write_text(conftest_content, encoding='utf-8')
    files.append(str(conftest_file))

    # pytest.ini
    pytest_ini_content = f'''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under={coverage_target}
'''
    pytest_ini_file = output_dir / "pytest.ini"
    pytest_ini_file.write_text(pytest_ini_content, encoding='utf-8')
    files.append(str(pytest_ini_file))

    # .coveragerc
    coveragerc_content = '''[run]
source = .
omit =
    tests/*
    */__pycache__/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
'''
    coveragerc_file = output_dir / ".coveragerc"
    coveragerc_file.write_text(coveragerc_content, encoding='utf-8')
    files.append(str(coveragerc_file))

    # Load tests if enabled
    if has_load_tests:
        locustfile_content = generate_locustfile()
        locustfile = output_dir / "locustfile.py"
        locustfile.write_text(locustfile_content, encoding='utf-8')
        files.append(str(locustfile))

    # Docker files
    if has_docker:
        dockerfile_content = generate_dockerfile()
        dockerfile = output_dir / "Dockerfile"
        dockerfile.write_text(dockerfile_content, encoding='utf-8')
        files.append(str(dockerfile))

        dockercompose_content = generate_docker_compose(has_db)
        dockercompose_file = output_dir / "docker-compose.yml"
        dockercompose_file.write_text(dockercompose_content, encoding='utf-8')
        files.append(str(dockercompose_file))

        dockerignore_content = '''__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.git
.gitignore
README.md
.coverage
htmlcov/
.pytest_cache/
'''
        dockerignore_file = output_dir / ".dockerignore"
        dockerignore_file.write_text(dockerignore_content, encoding='utf-8')
        files.append(str(dockerignore_file))

    # CI/CD files
    if has_ci_cd:
        # GitHub Actions
        github_dir = output_dir / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)

        ci_yml_content = generate_github_actions_ci(coverage_target)
        ci_yml_file = github_dir / "ci.yml"
        ci_yml_file.write_text(ci_yml_content, encoding='utf-8')
        files.append(str(ci_yml_file))

    # requirements.txt
    reqs_content = generate_api_requirements(has_auth, has_db, has_rate_limit, has_metrics, has_load_tests)
    reqs_file = output_dir / "requirements.txt"
    reqs_file.write_text(reqs_content, encoding='utf-8')
    files.append(str(reqs_file))

    # README.md
    readme_content = generate_api_readme(objective, has_auth, has_db)
    readme_file = output_dir / "README.md"
    readme_file.write_text(readme_content, encoding='utf-8')
    files.append(str(readme_file))

    return files


def generate_fastapi_main(has_auth: bool, has_db: bool, has_rate_limit: bool = False, has_metrics: bool = False, cors_config: str = "restricted") -> str:
    """Template FastAPI main.py with enterprise features"""

    # CORS configuration
    if cors_config == "restricted":
        cors_origins = '["http://localhost:3000", "http://localhost:8080"]'
    else:
        cors_origins = '["*"]'

    metrics_import = "from prometheus_client import make_asgi_app" if has_metrics else ""
    rate_limit_import = "from slowapi import Limiter, _rate_limit_exceeded_handler\nfrom slowapi.util import get_remote_address\nfrom slowapi.errors import RateLimitExceeded" if has_rate_limit else ""

    limiter_init = '''
limiter = Limiter(key_func=get_remote_address)
''' if has_rate_limit else ""

    rate_limit_middleware = '''
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
''' if has_rate_limit else ""

    metrics_mount = '''
# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
''' if has_metrics else ""

    return f'''"""
FastAPI Application - Generated {datetime.now().strftime("%Y-%m-%d")}
Enterprise-grade with security, metrics, and scalability
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
{"from database import engine, Base" if has_db else ""}
{"from auth import router as auth_router" if has_auth else ""}
from routes import router
from config import settings
{metrics_import}
{rate_limit_import}

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

{limiter_init}

# CORS - Secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins={cors_origins},
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

{rate_limit_middleware}

{"# Database" if has_db else ""}
{"Base.metadata.create_all(bind=engine)" if has_db else ""}

# Routes
{"app.include_router(auth_router, prefix='/auth', tags=['auth'])" if has_auth else ""}
app.include_router(router, prefix='/api', tags=['api'])

{metrics_mount}

@app.get("/")
def root():
    return {{"message": "API is running", "version": "1.0.0", "status": "healthy"}}


@app.get("/health")
def health():
    return {{"status": "healthy", "service": settings.APP_NAME}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
'''


def generate_config(has_auth: bool) -> str:
    """Template config.py"""
    return f'''"""
Configuration - Environment variables
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Application"
    DEBUG: bool = True

    {"# JWT" if has_auth else ""}
    {"SECRET_KEY: str = 'your-secret-key-change-in-production'" if has_auth else ""}
    {"ALGORITHM: str = 'HS256'" if has_auth else ""}
    {"ACCESS_TOKEN_EXPIRE_MINUTES: int = 30" if has_auth else ""}

    class Config:
        env_file = ".env"


settings = Settings()
'''


def generate_database() -> str:
    """Template database.py"""
    return '''"""
Database configuration - SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''


def generate_models(has_auth: bool) -> str:
    """Template models.py"""
    user_model = '''
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
''' if has_auth else ""

    return f'''"""
Database Models - SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

{user_model}

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    {"owner_id = Column(Integer, ForeignKey('users.id'))" if has_auth else ""}
    created_at = Column(DateTime, default=datetime.utcnow)

    {"owner = relationship('User')" if has_auth else ""}
'''


def generate_routes(has_auth: bool, has_db: bool = False) -> str:
    """Template routes.py"""
    if has_db:
        # Use SQLAlchemy ORM
        return f'''"""
API Routes - CRUD operations with SQLAlchemy
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from models import Item
{"from auth import get_current_user" if has_auth else ""}

router = APIRouter()


class ItemCreate(BaseModel):
    title: str
    description: str = None


class ItemResponse(BaseModel):
    id: int
    title: str
    description: str = None

    class Config:
        from_attributes = True


@router.post("/items", response_model=ItemResponse)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db){", current_user = Depends(get_current_user)" if has_auth else ""}
):
    """Create new item"""
    db_item = Item(title=item.title, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/items", response_model=List[ItemResponse])
def list_items(
    db: Session = Depends(get_db){", current_user = Depends(get_current_user)" if has_auth else ""}
):
    """List all items"""
    items = db.query(Item).all()
    return items


@router.get("/items/{{item_id}}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db){", current_user = Depends(get_current_user)" if has_auth else ""}
):
    """Get item by ID"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.put("/items/{{item_id}}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item: ItemCreate,
    db: Session = Depends(get_db){", current_user = Depends(get_current_user)" if has_auth else ""}
):
    """Update item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    db_item.title = item.title
    db_item.description = item.description
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/items/{{item_id}}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db){", current_user = Depends(get_current_user)" if has_auth else ""}
):
    """Delete item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {{"message": "Item deleted"}}
'''
    else:
        # In-memory fallback
        auth_dep = ", current_user = Depends(get_current_user)" if has_auth else ""

        return f'''"""
API Routes - CRUD operations
"""

from fastapi import APIRouter, HTTPException{", Depends" if has_auth else ""}
from pydantic import BaseModel
from typing import List
{"from auth import get_current_user" if has_auth else ""}

router = APIRouter()


class ItemCreate(BaseModel):
    title: str
    description: str = None


class ItemResponse(BaseModel):
    id: int
    title: str
    description: str = None

    class Config:
        from_attributes = True


# In-memory storage (replace with database in production)
items_db = {{}}
item_id_counter = 1


@router.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate{auth_dep}):
    """Create new item"""
    global item_id_counter

    new_item = {{
        "id": item_id_counter,
        "title": item.title,
        "description": item.description
    }}

    items_db[item_id_counter] = new_item
    item_id_counter += 1

    return new_item


@router.get("/items", response_model=List[ItemResponse])
def list_items({auth_dep.lstrip(", ") if auth_dep else ""}):
    """List all items"""
    return list(items_db.values())


@router.get("/items/{{item_id}}", response_model=ItemResponse)
def get_item(item_id: int{auth_dep}):
    """Get item by ID"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    return items_db[item_id]


@router.put("/items/{{item_id}}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate{auth_dep}):
    """Update item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    items_db[item_id].update({{
        "title": item.title,
        "description": item.description
    }})

    return items_db[item_id]


@router.delete("/items/{{item_id}}")
def delete_item(item_id: int{auth_dep}):
    """Delete item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    del items_db[item_id]

    return {{"message": "Item deleted"}}
'''


def generate_auth() -> str:
    """Template auth.py"""
    return '''"""
Authentication - JWT tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from config import settings

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# In-memory users (replace with database)
users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "hashed_password": pwd_context.hash("password123"),
        "is_active": True
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    email: str
    is_active: bool = True


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = users_db.get(email)
    if user is None:
        raise credentials_exception

    return User(**user)


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = users_db.get(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["email"]})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user"""
    return current_user
'''


def generate_api_tests(has_auth: bool) -> str:
    """Template tests.py"""
    return f'''"""
Tests - pytest
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


{"def test_login():" if has_auth else ""}
{"    response = client.post(" if has_auth else ""}
{"        '/auth/token'," if has_auth else ""}
{"        data={'username': 'test@example.com', 'password': 'password123'}" if has_auth else ""}
{"    )" if has_auth else ""}
{"    assert response.status_code == 200" if has_auth else ""}
{"    assert 'access_token' in response.json()" if has_auth else ""}


def test_create_item():
    response = client.post(
        "/api/items",
        json={{"title": "Test Item", "description": "Test description"}}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Test Item"


def test_list_items():
    response = client.get("/api/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
'''


def generate_api_requirements(has_auth: bool, has_db: bool, has_rate_limit: bool = False, has_metrics: bool = False, has_load_tests: bool = False) -> str:
    """Template requirements.txt with enterprise dependencies"""
    base = "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.0\npydantic-settings==2.1.0\npython-multipart==0.0.6"

    auth_deps = "\npasslib[bcrypt]==1.7.4\npython-jose[cryptography]==3.3.0" if has_auth else ""
    db_deps = "\nsqlalchemy==2.0.23\nalembic==1.12.1" if has_db else ""
    rate_limit_deps = "\nslowapi==0.1.9" if has_rate_limit else ""
    metrics_deps = "\nprometheus-client==0.19.0" if has_metrics else ""
    test_deps = "\npytest==7.4.3\npytest-cov==4.1.0\npytest-asyncio==0.21.1\nhttpx==0.25.2"
    load_test_deps = "\nlocust==2.18.0" if has_load_tests else ""

    return base + auth_deps + db_deps + rate_limit_deps + metrics_deps + test_deps + load_test_deps


def generate_api_readme(objective: str, has_auth: bool, has_db: bool) -> str:
    """Template README.md"""
    auth_section = """
## Authentication

Login to get access token:

```bash
curl -X POST http://localhost:8000/auth/token \\
  -d "username=test@example.com&password=password123"
```

Use token in requests:

```bash
curl http://localhost:8000/api/items \\
  -H "Authorization: Bearer YOUR_TOKEN"
```
""" if has_auth else ""

    return f'''# {objective}

Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

API will be available at: http://localhost:8000

## API Documentation

Interactive docs: http://localhost:8000/docs

{auth_section}

## Endpoints

- `GET /` - Root
- `GET /health` - Health check
{"- `POST /auth/token` - Login" if has_auth else ""}
- `POST /api/items` - Create item
- `GET /api/items` - List items
- `GET /api/items/{{id}}` - Get item
- `PUT /api/items/{{id}}` - Update item
- `DELETE /api/items/{{id}}` - Delete item

## Tests

```bash
pytest tests.py -v
```

## Features

- ✅ REST API with FastAPI
{"- ✅ JWT Authentication" if has_auth else ""}
{"- ✅ SQLAlchemy ORM" if has_db else ""}
- ✅ CORS enabled
- ✅ Input validation (Pydantic)
- ✅ Tests with pytest
- ✅ Interactive API docs
'''


# ============================================================================
# WEB SCRAPER GENERATOR
# ============================================================================

def generate_web_scraper(
    objective: str,
    architecture: Dict[str, Any],
    output_dir: Path
) -> List[str]:
    """Generar web scraper"""
    files = []

    # Detectar features
    has_selenium = "javascript" in objective.lower() or "dynamic" in objective.lower()

    # main.py
    main_content = '''"""
Web Scraper - Generated
"""

from scraper import Scraper
from storage import Storage
from config import Config


def main():
    config = Config()
    scraper = Scraper(config)
    storage = Storage(config)

    print("Starting scraper...")

    # Scrape
    results = scraper.scrape(config.TARGET_URL)

    print(f"Scraped {len(results)} items")

    # Store
    storage.save(results)

    print("Done!")


if __name__ == "__main__":
    main()
'''

    main_file = output_dir / "main.py"
    main_file.write_text(main_content, encoding='utf-8')
    files.append(str(main_file))

    # scraper.py
    scraper_content = generate_scraper_template(has_selenium)
    scraper_file = output_dir / "scraper.py"
    scraper_file.write_text(scraper_content, encoding='utf-8')
    files.append(str(scraper_file))

    # storage.py
    storage_content = '''"""
Storage - Save scraped data
"""

import json
from pathlib import Path


class Storage:
    def __init__(self, config):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def save(self, data):
        """Save data to JSON file"""
        output_file = self.output_dir / "scraped_data.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved to {output_file}")
'''

    storage_file = output_dir / "storage.py"
    storage_file.write_text(storage_content, encoding='utf-8')
    files.append(str(storage_file))

    # config.py
    config_content = '''"""
Configuration
"""

class Config:
    TARGET_URL = "https://example.com"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    TIMEOUT = 30
'''

    config_file = output_dir / "config.py"
    config_file.write_text(config_content, encoding='utf-8')
    files.append(str(config_file))

    # requirements.txt
    reqs = "requests==2.31.0\nbeautifulsoup4==4.12.2\nlxml==4.9.3"
    if has_selenium:
        reqs += "\nselenium==4.15.2"

    reqs_file = output_dir / "requirements.txt"
    reqs_file.write_text(reqs, encoding='utf-8')
    files.append(str(reqs_file))

    # README.md
    readme_file = output_dir / "README.md"
    readme_file.write_text(f"# {objective}\n\nWeb scraper generated on {datetime.now().strftime('%Y-%m-%d')}\n", encoding='utf-8')
    files.append(str(readme_file))

    return files


def generate_scraper_template(has_selenium: bool) -> str:
    """Template scraper.py"""
    if has_selenium:
        return '''"""
Scraper - Selenium for dynamic content
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self, config):
        self.config = config
        self.driver = None

    def scrape(self, url):
        """Scrape URL with Selenium"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument(f'user-agent={self.config.USER_AGENT}')

        self.driver = webdriver.Chrome(options=options)

        try:
            self.driver.get(url)

            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            soup = BeautifulSoup(self.driver.page_source, 'lxml')

            # Parse content
            results = []
            for item in soup.find_all('article'):  # Adjust selector
                results.append({
                    'title': item.get_text(strip=True)
                })

            return results

        finally:
            if self.driver:
                self.driver.quit()
'''
    else:
        return '''"""
Scraper - Requests + BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })

    def scrape(self, url):
        """Scrape URL"""
        response = self.session.get(url, timeout=self.config.TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Parse content
        results = []
        for item in soup.find_all('article'):  # Adjust selector
            results.append({
                'title': item.get_text(strip=True)
            })

        return results
'''


# ============================================================================
# SIMPLE GAME GENERATOR
# ============================================================================

def generate_simple_game(
    objective: str,
    architecture: Dict[str, Any],
    output_dir: Path
) -> List[str]:
    """Generar juego simple con Pygame"""
    files = []

    # main.py
    game_content = '''"""
Simple Game - Pygame
"""

import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Game")
clock = pygame.time.Clock()

# Player
player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT // 2
player_speed = 5


def main():
    global player_x, player_y

    running = True

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Handle keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_UP]:
            player_y -= player_speed
        if keys[pygame.K_DOWN]:
            player_y += player_speed

        # Keep player on screen
        player_x = max(0, min(player_x, SCREEN_WIDTH - 50))
        player_y = max(0, min(player_y, SCREEN_HEIGHT - 50))

        # Draw
        screen.fill(WHITE)
        pygame.draw.rect(screen, RED, (player_x, player_y, 50, 50))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
'''

    main_file = output_dir / "main.py"
    main_file.write_text(game_content, encoding='utf-8')
    files.append(str(main_file))

    # requirements.txt
    reqs_file = output_dir / "requirements.txt"
    reqs_file.write_text("pygame==2.5.2", encoding='utf-8')
    files.append(str(reqs_file))

    # README.md
    readme_file = output_dir / "README.md"
    readme_file.write_text(f"# {objective}\n\nSimple game. Use arrow keys to move.\n\n```bash\npip install pygame\npython main.py\n```\n", encoding='utf-8')
    files.append(str(readme_file))

    return files


# ============================================================================
# GENERIC APP GENERATOR
# ============================================================================

def generate_generic_app(
    objective: str,
    architecture: Dict[str, Any],
    output_dir: Path
) -> List[str]:
    """Generar aplicacion generica"""
    files = []

    # main.py
    main_content = f'''"""
{objective}

Generated on {datetime.now().strftime("%Y-%m-%d")}
"""


def main():
    print("Application running...")
    print("Objective: {objective}")

    # TODO: Implement core functionality

    print("Done!")


if __name__ == "__main__":
    main()
'''

    main_file = output_dir / "main.py"
    main_file.write_text(main_content, encoding='utf-8')
    files.append(str(main_file))

    # config.py
    config_file = output_dir / "config.py"
    config_file.write_text('"""Configuration"""\n\nDEBUG = True\n', encoding='utf-8')
    files.append(str(config_file))

    # README.md
    readme_file = output_dir / "README.md"
    readme_file.write_text(f"# {objective}\n\nGenerated on {datetime.now().strftime('%Y-%m-%d')}\n", encoding='utf-8')
    files.append(str(readme_file))

    return files


# ============================================================================
# ENTERPRISE HELPER FUNCTIONS
# ============================================================================

def generate_integration_tests(has_auth: bool, has_db: bool) -> str:
    """Generate integration tests"""
    return f'''"""
Integration Tests - Full workflow testing
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_full_crud_workflow():
    """Test complete CRUD workflow"""
    # Create
    response = client.post(
        "/api/items",
        json={{"title": "Integration Test", "description": "Test item"}}
    )
    assert response.status_code == 200
    item_id = response.json()["id"]

    # Read
    response = client.get(f"/api/items/{{item_id}}")
    assert response.status_code == 200
    assert response.json()["title"] == "Integration Test"

    # Update
    response = client.put(
        f"/api/items/{{item_id}}",
        json={{"title": "Updated", "description": "Updated desc"}}
    )
    assert response.status_code == 200

    # Delete
    response = client.delete(f"/api/items/{{item_id}}")
    assert response.status_code == 200


def test_error_handling():
    """Test error responses"""
    # 404 for non-existent item
    response = client.get("/api/items/99999")
    assert response.status_code == 404


def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


{'def test_auth_protected_endpoints():' if has_auth else ''}
{'    """Test that endpoints require authentication"""' if has_auth else ''}
{'    response = client.get("/api/items")' if has_auth else ''}
{'    assert response.status_code == 401' if has_auth else ''}
'''


def generate_conftest(has_db: bool) -> str:
    """Generate pytest conftest.py"""
    return '''"""
Pytest Configuration and Fixtures
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_item():
    """Sample item for testing"""
    return {
        "title": "Test Item",
        "description": "Test description"
    }
'''


def generate_locustfile() -> str:
    """Generate locustfile.py for load testing"""
    return '''"""
Load Tests - Locust
Run: locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between


class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_root(self):
        """Test root endpoint"""
        self.client.get("/")

    @task(2)
    def get_health(self):
        """Test health endpoint"""
        self.client.get("/health")

    @task(5)
    def list_items(self):
        """Test list items"""
        self.client.get("/api/items")

    @task(1)
    def create_item(self):
        """Test create item"""
        self.client.post(
            "/api/items",
            json={"title": "Load Test Item", "description": "Test"}
        )
'''


def generate_dockerfile() -> str:
    """Generate Dockerfile"""
    return '''# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Make sure scripts are executable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


def generate_docker_compose(has_db: bool) -> str:
    """Generate docker-compose.yml"""
    db_service = '''
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
''' if has_db else ""

    volumes = '''
volumes:
  postgres_data:
''' if has_db else ""

    return f'''version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    {"depends_on:" if has_db else ""}
      {"db:" if has_db else ""}
        {"condition: service_healthy" if has_db else ""}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
{db_service}
{volumes}
'''


def generate_github_actions_ci(coverage_target: int) -> str:
    """Generate GitHub Actions CI workflow"""
    return f'''name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('requirements.txt') }}}}
        restore-keys: |
          ${{{{ runner.os }}}}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term --cov-fail-under={coverage_target}

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run security scan
      uses: pyupio/safety@v1
      with:
        api-key: ${{{{ secrets.SAFETY_API_KEY }}}}

  build:
    runs-on: ubuntu-latest
    needs: [test, security]

    steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: docker build -t app:latest .

    - name: Test Docker image
      run: |
        docker run -d -p 8000:8000 --name test-container app:latest
        sleep 10
        curl -f http://localhost:8000/health || exit 1
        docker stop test-container
'''



def generate_alembic_ini() -> str:
    """Generate alembic.ini configuration"""
    return '''[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///./app.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''
