# Contributing

Pull requests are the only way data changes. If you would rather not use Git, open an [add-source issue](https://github.com/jackburrus/awesome-breakthroughs/issues/new?template=add-source.yml) and a maintainer will turn it into a pull request.

## What belongs here

A source belongs in the list when all of these are true:

- It offers open problems, or a competition or benchmark whose answers are not yet known.
- Each problem has a precise statement.
- It says how a solution is checked: a proof assistant, a scoring function, a numeric record with a checker, a named editor or referee, or a blind test.
- Its URL works and its key facts can be confirmed from the source itself.

Benchmarks with public test sets are allowed, but they get `contamination_risk: high` and their descriptions say so.

## Add or update a source

1. Copy a similar file in `sources/<field>/` to `sources/<field>/<id>.yaml`. The `id` must match the file name, and the directory must match `field`.
2. Open the URL yourself and check every fact you write down. Set `last_checked` to the date you checked.
3. Give every size a date in `size.as_of`. Counts change often, so a size without a date is not accepted.
4. Keep `description` to one plain sentence of 200 characters or less.
5. If you cannot confirm the URL or the key facts, add the candidate to `pending/` instead, with a `reason` and a `to_check` list.

`schema/source.schema.json` defines every field and its allowed values. The legend at the top of the README explains the ones that matter most.

## Record an AI claim

AI claims go in the source's `ai_records` list. A claim that does not belong to one listed source goes in its own file under `ai-records/`.

- Start every new claim at `level: claimed`. Raise it to `machine-checked` only when a Lean proof or a public verifier passes, to `source-accepted` only when the source's own maintainer has recorded it (for example, Erdős Problems changing a status, or Epoch AI labelling a problem), and to `peer-reviewed` only on publication.
- Set `autonomy` from what the evidence says. Use `unknown` when it is not disclosed.
- Set `secondhand: true` when your evidence reports someone else's claim rather than making it.
- When a claim is disputed, set `disputed: true` and link the dispute in `dispute_evidence`. Do not delete disputed claims.
- Record `disclosure` when the claimant publishes the full attempted set (`denominator`), the cost (`cost`) or the prompts and scaffolding (`prompts`).
- Do not add fields that rank or score sources by AI success.

Changes to `ai_records` or `ai-records/` need a second reviewer before merging.

## Build and check

The README tables, `dist/problems.json` and `llms.txt` are generated. Do not edit them by hand; edit the YAML files or `templates/`, then run:

```sh
pip install -r requirements.txt
python scripts/build.py                  # validate and regenerate
python -m unittest discover -s scripts   # tests
```

Commit the regenerated files with your change. CI runs `python scripts/build.py --check`, which fails if an entry is invalid or a generated file is out of date.

In YAML, quote any value that contains ` #` (for example `"Erdős #728"`); otherwise everything after the `#` is dropped as a comment. The build rejects unquoted values like this.

## Agents as contributors

AI agents may open pull requests. Say so in the pull request, and add a `Co-authored-by:` or `Agent:` trailer to the commits naming the agent. A human maintainer approves every merge.

## License

By contributing you agree that your data contributions are released under [CC0-1.0](LICENSE) and your code contributions under the [MIT License](LICENSE-MIT).
