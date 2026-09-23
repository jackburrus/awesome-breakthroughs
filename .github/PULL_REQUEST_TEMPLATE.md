## What this changes

<!-- Which sources, AI records or pending candidates this adds or updates. -->

## Checklist

- [ ] Each new source has a precise problem statement and a stated way to check solutions (see CONTRIBUTING.md).
- [ ] I opened every URL I added or changed, and `last_checked` is the date I did so.
- [ ] Every size has a `size.as_of` date.
- [ ] New AI claims start at `level: claimed` unless the evidence shows more, with evidence links; secondhand claims have `secondhand: true`; disputed claims have `disputed: true` and a `dispute_evidence` link.
- [ ] Anything I could not confirm is in `pending/`, not `sources/`.
- [ ] I ran `python scripts/build.py` and committed the regenerated README.md, dist/problems.json and llms.txt.
- [ ] If an AI agent did some of this work, the commits carry a `Co-authored-by:` or `Agent:` trailer naming it.
