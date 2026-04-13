import ast
import logging

logger = logging.getLogger(__name__)


class AstService:
    def parse_file(self, filepath: str, content: str) -> dict:
        logger.info("Parsing AST for %s", filepath)
        try:
            tree = ast.parse(content)
            return {
                "filepath": filepath,
                "imports": self._extract_imports(tree),
                "functions": self._extract_functions(tree),
                "classes": self._extract_classes(tree),
                "calls": self._extract_calls(tree),
            }
        except Exception as e:
            logger.error("Failed to parse %s: %s", filepath, e)
            return {"filepath": filepath, "error": str(e)}

    def _extract_imports(self, tree: ast.AST) -> list[dict]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"module": alias.name})
            elif isinstance(node, ast.ImportFrom):
                imports.append({
                    "from": node.module or "",
                    "import": ", ".join(a.name for a in node.names),
                })
        return imports

    def _extract_functions(self, tree: ast.AST) -> list[str]:
        return [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]

    def _extract_classes(self, tree: ast.AST) -> list[dict]:
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "methods": [
                        n.name for n in node.body
                        if isinstance(n, ast.FunctionDef)
                    ],
                })
        return classes

    def _extract_calls(self, tree: ast.AST) -> list[str]:
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
                elif isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
        return calls