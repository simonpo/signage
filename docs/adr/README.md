# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Signage project.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: What is the issue that we're seeing?
- **Decision**: What is the change that we're proposing?
- **Consequences**: What becomes easier or harder to do?

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-plugin-system-architecture.md) | Plugin System Architecture | Proposed | 2025-11-29 |

## Creating a New ADR

1. Copy template (if exists) or follow the structure of existing ADRs
2. Number sequentially (0002, 0003, etc.)
3. Use format: `NNNN-title-in-kebab-case.md`
4. Update this index
5. Reference the ADR in relevant code/docs

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [When to write an ADR](https://github.com/joelparkerhenderson/architecture-decision-record#when-to-write-an-adr)
