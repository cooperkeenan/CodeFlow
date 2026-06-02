# CodeFlow — Claude Code Guidelines

## Design Principles
- SOLID principles on every file:
  - Single Responsibility: one class, one reason to change
  - Open/Closed: extend via new classes, not by modifying existing ones
  - Liskov Substitution: subtypes must be substitutable for their base types
  - Interface Segregation: small focused interfaces over large ones
  - Dependency Inversion: depend on abstractions, inject concretions

## Code Standards
- Max 150 lines per file — split if exceeded
- Type annotations on all function signatures
- Constructor injection only — no global state, no service locator
- No markdown docstrings or inline comments explaining what code does
- No unsolicited tests
- No unused imports
- Prefer dataclasses for value objects
- Follow existing patterns before introducing new ones

## Naming
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private methods: prefix with _

## File Structure
- One class per file unless the secondary class is a private implementation detail
- Services take all dependencies in __init__ via constructor injection
- Tools wrap exactly one service method — no logic in tool handlers
- Schemas live next to the tool they describe (same file)

## What Not To Do
- Do not modify frontend/ unless the PBI explicitly says so
- Do not create test files unless asked
- Do not refactor files that are not in scope for the current PBI
- Do not add logging statements beyond what already exists in the file being modified
- Do not use global variables or module-level mutable state