ENTRY_MARKERS = frozenset({"main.py", "app.py", "manage.py"})

PACKAGE_MARKERS = frozenset({
    "pyproject.toml", "setup.py", "package.json",
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "Dockerfile",
})

SOURCE_EXTENSIONS = frozenset({
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb",
})
