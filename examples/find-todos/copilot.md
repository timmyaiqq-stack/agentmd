---
applyTo: "**/*"
---
# Find TODO comments

When asked to surface pending work in this repository, scan all source
files for `TODO`, `FIXME`, `HACK`, and `XXX` markers and produce a report
grouped by file.

## Scope

- Search every tracked source file. Skip `node_modules/`, `.venv/`,
  `dist/`, `build/`, generated lock files, and anything ignored by git.
- Match marker tokens case-insensitively.

## Output format

```
## <relative/path/to/file>
- L<line>: <comment text>
```

- Sort files alphabetically. Sort lines numerically.
- Strip the leading comment chars (`#`, `//`, `/*`, `*`) from the
  displayed text.
- Finish with: `Total: N TODOs across M files.`

## Rules

- Never invent matches. If nothing is found, say so.
- Do not modify any files — this is a read-only audit.
