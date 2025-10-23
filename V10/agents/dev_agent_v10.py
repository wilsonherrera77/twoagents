#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev Agent V10 - Developer con generación de código
===================================================

Responsabilidades:
- Leer arquitectura propuesta por PM
- Generar código Python completo
- Validar sintaxis con ast.parse()
- Crear estructura de proyecto
- Escribir todos los archivos

Modo Híbrido:
- Lee arquitectura de filesystem
- En producción: Espera que Claude (otro terminal) genere código
- En test: Usa templates simples
"""

import sys
import ast
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Imports de infraestructura V10
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import create_logger
from protocols_v10 import Architecture, Implementation


class DevAgentV10:
    """
    Developer Agent V10 - Genera código basado en arquitectura.

    Responsabilidades:
    1. Leer arquitectura del PM
    2. Generar código Python para cada módulo
    3. Validar sintaxis
    4. Crear estructura de proyecto
    5. Escribir archivos
    """

    def __init__(self, workspace_dir: str = "workspace"):
        """
        Inicializa Dev Agent V10.

        Args:
            workspace_dir: Directorio donde crear proyectos
        """
        self.logger = create_logger("DEV_AGENT_V10")
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)

        self.logger.set_state("INITIALIZED")
        self.logger.info("Dev Agent V10 initialized")
        self.logger.info(f"Workspace: {self.workspace.absolute()}")

    def generate_project(self, architecture: Architecture, project_name: str = None) -> Optional[Implementation]:
        """
        Genera proyecto completo basado en arquitectura.

        Args:
            architecture: Arquitectura propuesta por PM
            project_name: Nombre del proyecto (auto-generado si None)

        Returns:
            Implementation object si exitoso, None si falla
        """
        self.logger.set_state("GENERATING")
        start_time = datetime.now()

        # Crear directorio de proyecto
        if not project_name:
            project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        project_dir = self.workspace / project_name
        self.logger.set_task(f"Generating project: {project_name}")

        try:
            # Crear estructura de directorios
            self._create_project_structure(project_dir)

            # Generar código para cada módulo
            files_created = []

            # Generar módulos principales
            for module in architecture.proposed_modules:
                file_path = self._generate_module(
                    project_dir,
                    module,
                    architecture
                )
                if file_path:
                    files_created.append(str(file_path.relative_to(project_dir)))

            # Generar archivos de configuración
            config_files = self._generate_config_files(project_dir, architecture)
            files_created.extend(config_files)

            # Generar README
            readme_path = self._generate_readme(project_dir, architecture)
            if readme_path:
                files_created.append(str(readme_path.relative_to(project_dir)))

            # Generar requirements.txt
            req_path = self._generate_requirements(project_dir, architecture)
            if req_path:
                files_created.append(str(req_path.relative_to(project_dir)))

            duration = self.logger.measure_time("Project generation", start_time)

            self.logger.success(
                f"Project generated successfully",
                {
                    "project": project_name,
                    "files_count": len(files_created),
                    "duration": duration
                }
            )

            self.logger.set_state("SUCCESS")

            return Implementation(
                project_dir=str(project_dir.absolute()),
                files_created=files_created,
                files_count=len(files_created),
                technologies=architecture.technologies,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(
                "Project generation failed",
                {"error": str(e), "type": type(e).__name__}
            )
            self.logger.set_state("FAILED")
            return None

    def _create_project_structure(self, project_dir: Path):
        """Crea estructura de directorios del proyecto."""
        self.logger.info(f"Creating project structure: {project_dir.name}")

        # Crear directorios principales
        dirs = [
            project_dir,
            project_dir / "src",
            project_dir / "tests",
            project_dir / "docs",
            project_dir / "config"
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.logger.success(f"Created {len(dirs)} directories")

    def _generate_module(self, project_dir: Path, module_name: str, architecture: Architecture) -> Optional[Path]:
        """
        Genera código para un módulo.

        En modo híbrido, esto sería reemplazado por código generado por Claude.
        Por ahora, genera templates básicos.
        """
        self.logger.info(f"Generating module: {module_name}")

        # Determinar tipo de módulo por nombre
        if "auth" in module_name.lower() or "jwt" in module_name.lower():
            code = self._generate_auth_module(module_name, architecture)
        elif "api" in module_name.lower() or "main" in module_name.lower():
            code = self._generate_api_module(module_name, architecture)
        elif "model" in module_name.lower() or "database" in module_name.lower():
            code = self._generate_model_module(module_name, architecture)
        elif "config" in module_name.lower():
            code = self._generate_config_module(module_name, architecture)
        else:
            code = self._generate_generic_module(module_name, architecture)

        # Validar sintaxis
        try:
            ast.parse(code)
            self.logger.success(f"Module syntax validated: {module_name}")
        except SyntaxError as e:
            self.logger.error(
                f"Syntax error in {module_name}",
                {"error": str(e), "line": e.lineno}
            )
            return None

        # Escribir archivo
        file_path = project_dir / "src" / module_name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        self.logger.success(f"Module written: {module_name}")
        return file_path

    def _generate_auth_module(self, module_name: str, architecture: Architecture) -> str:
        """Genera módulo de autenticación JWT."""
        return '''#!/usr/bin/env python3
"""
Authentication module with JWT support.
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    import bcrypt
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
'''

    def _generate_api_module(self, module_name: str, architecture: Architecture) -> str:
        """Genera módulo API principal."""
        framework = architecture.technologies.get("framework", "FastAPI")

        if "fastapi" in framework.lower():
            return '''#!/usr/bin/env python3
"""
Main API module.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional


app = FastAPI(
    title="API",
    description="Generated API with JWT authentication",
    version="1.0.0"
)

security = HTTPBearer()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Add your endpoints here
'''
        else:
            return '''#!/usr/bin/env python3
"""
Main API module.
"""

def main():
    """Main entry point."""
    print("API starting...")
    # Add your API logic here
    pass


if __name__ == "__main__":
    main()
'''

    def _generate_model_module(self, module_name: str, architecture: Architecture) -> str:
        """Genera módulo de modelos de base de datos."""
        return '''#!/usr/bin/env python3
"""
Database models.
"""

from datetime import datetime
from typing import Optional


class BaseModel:
    """Base model with common fields."""

    def __init__(self):
        self.id: Optional[int] = None
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Add your models here
'''

    def _generate_config_module(self, module_name: str, architecture: Architecture) -> str:
        """Genera módulo de configuración."""
        return '''#!/usr/bin/env python3
"""
Configuration module.
"""

import os
from typing import Any


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(cls, key, default)


config = Config()
'''

    def _generate_generic_module(self, module_name: str, architecture: Architecture) -> str:
        """Genera módulo genérico."""
        class_name = module_name.replace(".py", "").replace("_", " ").title().replace(" ", "")

        return f'''#!/usr/bin/env python3
"""
{module_name} - Generated module.
"""

from typing import Optional, Dict, Any


class {class_name}:
    """
    {class_name} class.

    TODO: Implement functionality
    """

    def __init__(self):
        """Initialize {class_name}."""
        pass

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data.

        Args:
            data: Input data

        Returns:
            Processed data
        """
        # TODO: Implement processing logic
        return data


def main():
    """Main entry point."""
    instance = {class_name}()
    print(f"{{instance.__class__.__name__}} initialized")


if __name__ == "__main__":
    main()
'''

    def _generate_config_files(self, project_dir: Path, architecture: Architecture) -> List[str]:
        """Genera archivos de configuración."""
        files = []

        # .env.example
        env_example = project_dir / ".env.example"
        with open(env_example, "w") as f:
            f.write("""# Database
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
""")
        files.append(str(env_example.relative_to(project_dir)))

        # .gitignore
        gitignore = project_dir / ".gitignore"
        with open(gitignore, "w") as f:
            f.write("""__pycache__/
*.py[cod]
*$py.class
.env
.venv
venv/
*.db
*.log
.DS_Store
""")
        files.append(str(gitignore.relative_to(project_dir)))

        return files

    def _generate_readme(self, project_dir: Path, architecture: Architecture) -> Optional[Path]:
        """Genera README.md."""
        readme_path = project_dir / "README.md"

        modules_list = "\n".join([f"- {m}" for m in architecture.proposed_modules])
        tech_list = "\n".join([f"- **{k}**: {v}" for k, v in architecture.technologies.items()])

        content = f"""# {project_dir.name}

Generated by Discovery Motor V10

## Architecture

### Modules
{modules_list}

### Technologies
{tech_list}

## Analysis

{architecture.analysis}

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run the application:
```bash
python src/main_api.py
```

## Project Structure

```
{project_dir.name}/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── config/        # Configuration files
└── README.md      # This file
```

## Development

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

        return readme_path

    def _generate_requirements(self, project_dir: Path, architecture: Architecture) -> Optional[Path]:
        """Genera requirements.txt."""
        req_path = project_dir / "requirements.txt"

        framework = architecture.technologies.get("framework", "").lower()

        requirements = []

        if "fastapi" in framework:
            requirements.extend([
                "fastapi>=0.104.0",
                "uvicorn[standard]>=0.24.0",
                "pydantic>=2.5.0"
            ])

        if "jwt" in str(architecture.technologies).lower():
            requirements.append("pyjwt>=2.8.0")
            requirements.append("bcrypt>=4.1.0")

        if "pytest" in str(architecture.technologies).lower():
            requirements.append("pytest>=7.4.0")

        # Agregar dependencias comunes
        requirements.extend([
            "python-dotenv>=1.0.0",
            "requests>=2.31.0"
        ])

        with open(req_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(set(requirements))) + "\n")

        return req_path

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas del agente."""
        return {
            "dev_agent": self.logger.get_metrics(),
            "workspace": str(self.workspace.absolute())
        }


def main():
    """Test del Dev Agent V10."""
    import argparse

    parser = argparse.ArgumentParser(description="Dev Agent V10 - Code Generation")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test with sample architecture"
    )
    parser.add_argument(
        "--architecture",
        type=str,
        help="Path to architecture JSON file"
    )

    args = parser.parse_args()

    if args.test:
        # Test con arquitectura de ejemplo
        print("\n[TEST MODE] Using sample architecture\n")

        sample_arch = Architecture(
            proposed_modules=[
                "auth_service.py",
                "main_api.py",
                "database_models.py",
                "config.py"
            ],
            database_schema={
                "users": {
                    "id": "INTEGER PRIMARY KEY",
                    "email": "TEXT UNIQUE NOT NULL",
                    "password_hash": "TEXT NOT NULL"
                }
            },
            technologies={
                "framework": "FastAPI",
                "database": "SQLite",
                "auth": "JWT",
                "testing": "pytest"
            },
            analysis="Simple REST API with JWT authentication",
            reasoning="FastAPI provides automatic validation and documentation"
        )

        agent = DevAgentV10()
        implementation = agent.generate_project(sample_arch, "test_project")

        if implementation:
            print("\n[SUCCESS] Project generated!\n")
            print(f"Directory: {implementation.project_dir}")
            print(f"Files: {implementation.files_count}")
            print("\nFiles created:")
            for file in implementation.files_created:
                print(f"  - {file}")

            agent.logger.print_summary()
            sys.exit(0)
        else:
            print("\n[FAILED] Project generation failed")
            agent.logger.print_summary()
            sys.exit(1)

    elif args.architecture:
        # Cargar arquitectura desde archivo
        with open(args.architecture, "r") as f:
            arch_data = json.load(f)

        architecture = Architecture(**arch_data)

        agent = DevAgentV10()
        implementation = agent.generate_project(architecture)

        if implementation:
            print(f"\n[SUCCESS] Project: {implementation.project_dir}\n")
            sys.exit(0)
        else:
            print("\n[FAILED]\n")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
