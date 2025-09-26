"""
List FastAPI endpoints (path, method, name, tags) by importing the app.
Run: uv run python scripts/endpoint_map.py
"""
from importlib import import_module

def main():
    app_module = import_module('app.main')
    app = getattr(app_module, 'app')
    routes = []
    for r in app.routes:
        if hasattr(r, 'methods') and hasattr(r, 'path'):
            methods = ','.join(sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}))
            name = getattr(r, 'name', '')
            tags = getattr(r, 'tags', [])
            routes.append((r.path, methods, name, ','.join(tags)))

    routes.sort(key=lambda x: x[0])
    print("Path\tMethods\tName\tTags")
    for path, methods, name, tags in routes:
        print(f"{path}\t{methods}\t{name}\t{tags}")


if __name__ == "__main__":
    main()
