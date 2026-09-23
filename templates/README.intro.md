# awesome-breakthroughs

A curated list of places where open problems wait to be solved and where a solution can be checked: problem databases, record tables, benchmarks of unsolved problems, and blind competitions, across fields.
It is written for people and for AI agents looking for problems where progress can be verified.

Each entry was opened and checked by hand on the date in its `Checked` column. Problem counts change often, so every size in the data carries its own date.
The data is also available as [`dist/problems.json`](dist/problems.json) and [`llms.txt`](llms.txt).

**How this differs from [Open Challenge List](https://openchallengelist.com/).** Open Challenge List is a peer list: it compiles GitHub-hosted competitions and their record holders automatically and asks readers to verify before citing.
This list is smaller and curated by hand. It covers sources beyond GitHub, such as journal surveys, lab competitions and wet-lab challenges, and it classifies each source by how solutions are verified.

## How to read an entry

- **Verified by** says how a solution is checked: `formal` (a proof assistant such as Lean), `score` (an automatic scoring function), `bound` (a numeric record with a checker), `review` (a human referee or editor), `blind` (held-out data, future weather or a wet lab), or `self-reported` (no independent check).
- **Verifier access** says whether you can run that check yourself: `public-code`, `public-service`, `gated-free` (free after registration), `paid`, or `none` (a person decides).
- **Lifecycle** is `active`, `slow` (little change for 6 to 24 months), `stale` (more than 24 months), `archived` or `superseded`.
- **AI records** use an evidence ladder. `claimed` means only the claimant says so. `machine-checked` means a Lean proof or public verifier passes. `source-accepted` means the source's own maintainer checked it and recorded it. `peer-reviewed` means it was published after review. New claims start at `claimed`.
- **Autonomy** says who did the work: `autonomous`, `human+ai` (AI was instrumental but people directed it, as in Epoch AI's label), `human-led-ai-tools`, or `unknown`.
- A claim marked `disputed` links to the dispute. A claim marked `secondhand` is known only through someone else's report.

Sources are never ranked by how many problems AI has solved.
