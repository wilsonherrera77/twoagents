import argparse
from pathlib import Path

TEMPLATE_README = """# {project_name}\n\nProyecto base generado automáticamente.\n"""
TEMPLATE_MAIN = '''def main():
    """Función principal de ejemplo"""
    pass

if __name__ == "__main__":
    main()
'''
TEMPLATE_TEST = """from src import main\n\n\ndef test_main():\n    assert main.main() is None\n"""


def init_workspace(base_dir: Path):
    src_dir = base_dir / "src"
    tests_dir = base_dir / "tests"

    # Create directories
    src_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Create README
    readme = base_dir / "README.md"
    if not readme.exists():
        readme.write_text(TEMPLATE_README.format(project_name=base_dir.name), encoding="utf-8")

    # Create main module
    main_py = src_dir / "main.py"
    if not main_py.exists():
        main_py.write_text(TEMPLATE_MAIN, encoding="utf-8")
    init_py = src_dir / "__init__.py"
    if not init_py.exists():
        init_py.write_text("", encoding="utf-8")

    # Create tests
    test_file = tests_dir / "test_main.py"
    if not test_file.exists():
        test_file.write_text(TEMPLATE_TEST, encoding="utf-8")
    tests_init = tests_dir / "__init__.py"
    if not tests_init.exists():
        tests_init.write_text("", encoding="utf-8")

    print(f"Workspace initialized at {base_dir}")


def main():
    parser = argparse.ArgumentParser(description="Inicializa la carpeta workspace con estructura base")
    parser.add_argument("name", nargs="?", default="project", help="Nombre del proyecto dentro de workspace")
    args = parser.parse_args()

    repo_root = Path(__file__).parent
    workspace_root = repo_root / "workspace" / args.name
    init_workspace(workspace_root)


if __name__ == "__main__":
    main()
