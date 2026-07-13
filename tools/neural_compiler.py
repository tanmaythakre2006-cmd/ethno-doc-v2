import ast
import json
from pathlib import Path

def analyze_workspace(target_dir: str):
    target_path = Path(target_dir).resolve()

    base_dir = Path(__file__).resolve().parent.parent
    ledger_path = base_dir / ".system" / "neural_ledger.json"

    if not ledger_path.exists():
        print(f"Ledger file {ledger_path} not found.")
        return

    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = json.load(f)

    for py_file in target_path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))

            imports = []
            classes = []
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{node.module}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)

            rel_path = str(py_file.relative_to(base_dir))
            ledger["ast_dependencies"][rel_path] = {
                "imports": imports,
                "classes": classes,
                "functions": functions
            }
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    with open(ledger_path, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, indent=2)
    print("AST dependencies written to ledger.")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    backend_dir = base_dir / "backend"
    analyze_workspace(str(backend_dir))
