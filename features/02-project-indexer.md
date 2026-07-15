# F02 — Project indexer

Depends on: F01
Deliverable: `agents/tracer_agent/services/analysis/project_indexer.py` + models
Replaces: `AstService.extract_signatures`, `AstService.build_import_graph` (uppercase
heuristics), class-name identity throughout.

## Why

Everything downstream needs one authoritative, function-level symbol table with real
qualified names. The current pipeline's "any uppercase word is a class" heuristic
mangles module functions, `main()`s, and same-named classes in different packages.

## Spec

Input: `dict[relpath, source]` (from the existing `FileFetchService`). Output:
`ProjectIndex`. Pure function of its input; parse each file exactly once.

```python
@dataclass(frozen=True)
class FunctionRecord:
    fqn: str                       # "agents.layout_agent.services.planning.view_planner.ViewPlanner.plan"
    module: str
    cls: str | None
    name: str
    params: tuple[ParamRecord, ...]   # (name, annotation_fqn | None)
    returns: str | None
    span: SourceRef
    is_async: bool
    decorators: tuple[str, ...]       # resolved decorator fqns where possible
    body: ast.AST                     # retained in-memory for F03/F04; never serialized

@dataclass(frozen=True)
class ClassRecord:
    fqn: str
    bases: tuple[str, ...]            # resolved fqns where possible
    methods: tuple[str, ...]
    attr_types: Mapping[str, str]     # self._dep -> annotation fqn (see below)
    span: SourceRef

@dataclass(frozen=True)
class ModuleRecord:
    fqn: str                          # derived from relpath, "/"->"." minus .py
    bindings: Mapping[str, str]       # local alias -> imported symbol fqn
    classes: tuple[str, ...]
    functions: tuple[str, ...]        # includes "<module>" synthetic function for body code

class ProjectIndex:
    modules / classes / functions: Mapping[str, ...]
    implementations(base_fqn) -> tuple[str, ...]   # concrete subclasses, transitive
    resolve(module_fqn, name) -> str | None        # name through bindings to a project fqn
```

Details:
- **Synthetic `<module>` function** per module wraps top-level statements, so script
  bodies and FastAPI `app = create_app()` wiring participate in flows.
- **`attr_types`**: walk `__init__`; for `self.x = param`, record the param's
  annotation fqn. Also record class-body annotated attributes. This is the substrate
  for DI resolution in F03.
- **Subclass index**: map each resolved base fqn to its concrete (non-ABC,
  no-abstractmethod) project subclasses, transitively.
- **Bindings**: handle `import a.b`, `import a.b as c`, `from a import b as c`,
  relative imports resolved against the module's package. Star imports: record the
  source module; resolution through them is `inferred`-tier only (F03).
- Third-party/stdlib names resolve to a sentinel `ext:<root>` (e.g. `ext:httpx`) —
  needed by F05's effect registry.
- All mappings sorted by key at build time.

## Non-goals

No call extraction (F03), no branch analysis (F04), no cross-file type inference
beyond annotations and literal assignments.

## Acceptance

Run on CodeFlow: `ViewPlanner.plan` has params with annotation fqns pointing at real
project classes; `shared.models` classes indexed once each under distinct fqns;
`implementations("...user_store.UserStore")` returns exactly `NeonUserStore`;
`agents.tracer_agent.main.<module>` exists with the FastAPI wiring in its body.
