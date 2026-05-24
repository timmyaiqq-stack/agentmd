---
description: Find all TODO comments in the repo and group them by file
---
Scan the current repository for every TODO marker and produce a grouped report.

1. Search the working tree for `TODO`, `FIXME`, `HACK`, and `XXX` markers
   (case-insensitive) in source files. Skip `node_modules/`, `.venv/`,
   `dist/`, `build/`, and any path listed in `.gitignore`.
2. For each match capture:
   - relative file path
   - line number
   - the full comment text (trim leading comment chars: `#`, `//`, `/*`, `*`)
3. Group results by file. Within each file, sort by line number ascending.
4. Output a markdown report:

   ```
   ## <relative/path/to/file>
   - L<line>: <comment text>
   ```

5. End with a summary line: `Total: N TODOs across M files.`

If `$ARGUMENTS` is non-empty, treat it as an additional regex to OR into the
search pattern (e.g. `OPTIMIZE`, `REVIEW`).
