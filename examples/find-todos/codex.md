---
title: Find TODO comments grouped by file
---
1. **Determine scope.** Resolve the working tree root. Build the ignore
   set from `.gitignore` plus the defaults `node_modules`, `.venv`,
   `dist`, `build`, `.cache`.
2. **Scan.** Walk all remaining files. For each line, run a
   case-insensitive match for the patterns `TODO`, `FIXME`, `HACK`,
   `XXX`. Capture file path, line number, and the comment body with
   leading `#`, `//`, `/*`, `*` characters stripped.
3. **Group.** Bucket matches by relative file path. Sort files
   alphabetically; sort entries inside each file by line number
   ascending.
4. **Render.** Emit a markdown report:

   ```
   ## <path>
   - L<line>: <comment>
   ```

5. **Summarize.** Append a final line: `Total: N TODOs across M files.`
6. **Halt.** Do not propose fixes or open files for editing. The
   workflow ends with the report.
