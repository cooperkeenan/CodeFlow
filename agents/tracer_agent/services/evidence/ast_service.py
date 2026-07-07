import ast
import logging

from services.evidence.http_visitor import HttpCallVisitor

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

    def extract_signatures(self, filepath: str, content: str) -> dict:
        logger.info("Extracting signatures for %s", filepath)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {}
        upper_imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
            if alias.name and alias.name[0].isupper()
        ]
        result = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods = []
            for item in node.body:
                if not isinstance(item, ast.FunctionDef) or item.name.startswith("_"):
                    continue
                params = [
                    {
                        "name": arg.arg,
                        "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
                    }
                    for arg in item.args.args
                    if arg.arg != "self"
                ]
                returns = ast.unparse(item.returns) if item.returns else None
                methods.append({"name": item.name, "params": params, "returns": returns})
            result[node.name] = {
                "file_path": filepath,
                "public_methods": methods,
                "imports": upper_imports,
                "start_line": node.lineno,
                "end_line": node.end_lineno,
            }
        return result

    def build_import_graph(self, files: dict[str, str]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for content in files.values():
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            class_names = [
                node.name for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            ]
            upper_imports = [
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
                if alias.name and alias.name[0].isupper()
            ]
            for class_name in class_names:
                graph[class_name] = upper_imports
        return graph

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

    def extract_http_calls(self, filepath: str, content: str) -> list[dict]:
        logger.info("Extracting HTTP calls for %s", filepath)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        visitor = HttpCallVisitor()
        visitor.visit(tree)
        return visitor.calls
