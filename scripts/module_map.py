"""
List packages, modules, routers, and top-level classes/functions for a quick map of the codebase.
Run: uv run python scripts/module_map.py
"""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def parse_module(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"classes": [], "functions": [], "routers": []}

    classes, functions, routers = [], [], []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.Assign):
            # rudimentary search for APIRouter instances
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                    if getattr(getattr(node.value.func, 'id', None), 'lower', lambda: '' )().lower() == 'apirouter' or \
                       getattr(getattr(node.value.func, 'attr', None), 'lower', lambda: '' )().lower() == 'apirouter':
                        routers.append(target.id)
    return {"classes": classes, "functions": functions, "routers": routers}


def main():
    print(f"Scanning {APP}...\n")
    for pkg in sorted([p for p in APP.iterdir() if p.is_dir() and p.name not in {"__pycache__"} ]):
        print(f"[Package] {pkg.relative_to(ROOT)}")
        py_files = sorted(pkg.rglob("*.py"))
        for f in py_files:
            rel = f.relative_to(ROOT)
            info = parse_module(f)
            class_s = ", ".join(info["classes"]) or "-"
            func_s = ", ".join([fn for fn in info["functions"] if not fn.startswith("_")]) or "-"
            router_s = ", ".join(info["routers"]) or "-"
            print(f"  - {rel}")
            print(f"      classes: {class_s}")
            print(f"      functions: {func_s}")
            print(f"      routers: {router_s}")
        print()


if __name__ == "__main__":
    main()
