# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Data is one YAML file per entry in `sources/<field>/`, `ai-records/` and `pending/`, validated by `schema/*.schema.json`. README.md, `dist/problems.json` and `llms.txt` are generated: edit the YAML or `templates/`, then run `python scripts/build.py` (deps in `requirements.txt`) and commit the outputs. CI runs `python scripts/build.py --check` and `python -m unittest discover -s scripts`.
- Never add or change an entry without opening its URL and confirming the facts that day; set `last_checked` and `size.as_of`. Unconfirmed candidates go to `pending/`. AI-claim rules (evidence ladder, `secondhand`, `disputed`, no ranking by AI success) are in CONTRIBUTING.md.
- YAML sharp edge: an unquoted ` #` starts a comment and silently truncates a value (`Erdős #728`); quote such values. The build rejects them.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
