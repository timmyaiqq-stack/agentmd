---
name: find-todos
description: Find all TODO comments in the repo and group them by file
---
Audit the current workspace for pending-work markers and produce a grouped
report.

Scan every tracked source file for `TODO`, `FIXME`, `HACK`, and `XXX`
(case-insensitive). Skip dependency and build directories
(`node_modules/`, `.venv/`, `dist/`, `build/`) plus anything in
`.gitignore`.

For each match record:

- relative file path
- line number
- comment text (strip leading `#`, `//`, `/*`, `*`)

Group by file. Within each file, sort by line ascending. Render as:

```
## <relative/path/to/file>
- L<line>: <comment>
```

End with `Total: N TODOs across M files.` If there are zero matches,
state that plainly. Do not invent or guess at matches.
