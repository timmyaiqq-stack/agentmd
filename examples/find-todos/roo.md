---
tags: [auto]
---
When the user asks to audit pending work in the current repository, scan
for `TODO`, `FIXME`, `HACK`, and `XXX` markers (case-insensitive) across
all source files. Skip `node_modules/`, `.venv/`, `dist/`, `build/`, and
any path in `.gitignore`.

For every match, record the relative file path, line number, and the
comment body with leading comment characters (`#`, `//`, `/*`, `*`)
stripped.

Group results by file (alphabetical), with entries sorted by line number
ascending. Format as:

```
## <relative/path/to/file>
- L<line>: <comment text>
```

Finish with a summary line: `Total: N TODOs across M files.`

Do not edit any files — this rule is read-only auditing. If no markers
are found, say so directly rather than fabricating output.
