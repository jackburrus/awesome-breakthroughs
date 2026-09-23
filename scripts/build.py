#!/usr/bin/env python3
"""Validate every entry, then generate README.md, dist/problems.json and llms.txt.

Usage:
    python scripts/build.py           validate and write the generated files
    python scripts/build.py --check   validate and fail if a generated file is out of date

Entries live in sources/<field>/<id>.yaml, ai-records/<id>.yaml and pending/<id>.yaml.
The hand-written parts of the README live in templates/.
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
REPO = "jackburrus/awesome-breakthroughs"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"
SCHEMA_VERSION = "1"

# Display order and headings. Keys must match the field enum in schema/source.schema.json.
FIELDS = {
    "mathematics": "Mathematics",
    "computer-science": "Computer science",
    "physics-astronomy": "Physics and astronomy",
    "biology-medicine": "Biology and medicine",
    "chemistry-materials": "Chemistry and materials",
    "earth-climate-energy": "Earth, climate and energy",
    "ai-ml": "AI and machine learning",
    "meta": "Other lists",
}


class BuildError(Exception):
    pass


def to_json_types(value):
    """YAML parses bare dates into date objects; the schema and JSON output want ISO strings."""
    if isinstance(value, dict):
        return {key: to_json_types(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_json_types(item) for item in value]
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def load_yaml(path):
    with path.open(encoding="utf-8") as handle:
        return to_json_types(yaml.safe_load(handle))


def make_validators(root):
    schemas = {}
    for name in ("source", "ai-record", "pending"):
        schemas[name] = json.loads(
            (root / "schema" / f"{name}.schema.json").read_text(encoding="utf-8")
        )
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    field_enum = schemas["source"]["$defs"]["field"]["enum"]
    if list(FIELDS) != field_enum:
        raise BuildError(
            f"FIELDS in build.py {list(FIELDS)} does not match the schema field enum {field_enum}"
        )
    return {
        name: Draft202012Validator(
            schema, registry=registry, format_checker=FormatChecker()
        )
        for name, schema in schemas.items()
    }


def normalize_url(url):
    url = url.strip().lower()
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            url = url[len(prefix) :]
    if url.startswith("www."):
        url = url[4:]
    return url.rstrip("/")


VALUE_LINE = re.compile(r"^\s*(?:-\s+)?(?:[\w-]+:\s+)?(?P<value>.*)$")


def unquoted_hash_lines(text):
    """Line numbers where ' #' in an unquoted value would silently truncate it, as in 'Erdős #728'."""
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        value = VALUE_LINE.match(line).group("value")
        if not value.startswith(("'", '"')) and " #" in value:
            yield number


def load_entries(root):
    """Load and validate every entry. Returns (data, errors)."""
    validators = make_validators(root)
    errors = []
    data = {"sources": [], "ai_records": [], "pending": []}
    groups = [
        ("sources", "source", sorted((root / "sources").glob("*/*.yaml"))),
        ("ai_records", "ai-record", sorted((root / "ai-records").glob("*.yaml"))),
        ("pending", "pending", sorted((root / "pending").glob("*.yaml"))),
    ]
    for key, schema_name, paths in groups:
        for path in paths:
            rel = path.relative_to(root).as_posix()
            for line_number in unquoted_hash_lines(path.read_text(encoding="utf-8")):
                errors.append(
                    f"{rel}:{line_number}: ' #' starts a YAML comment and cuts the value short; quote the value"
                )
            try:
                entry = load_yaml(path)
            except yaml.YAMLError as exc:
                errors.append(f"{rel}: invalid YAML: {exc}")
                continue
            if not isinstance(entry, dict):
                errors.append(f"{rel}: expected a mapping at the top level")
                continue
            schema_errors = sorted(
                validators[schema_name].iter_errors(entry),
                key=lambda e: list(e.absolute_path),
            )
            for err in schema_errors:
                location = (
                    "/".join(str(part) for part in err.absolute_path) or "(top level)"
                )
                errors.append(f"{rel}: {location}: {err.message}")
            if schema_errors:
                continue
            if entry["id"] != path.stem:
                errors.append(
                    f"{rel}: id '{entry['id']}' must match the file name '{path.stem}'"
                )
            if key == "sources" and entry["field"] != path.parent.name:
                errors.append(
                    f"{rel}: field '{entry['field']}' must match the directory '{path.parent.name}'"
                )
            data[key].append((rel, entry))
    errors.extend(cross_checks(data))
    return data, errors


def cross_checks(data):
    errors = []
    seen_ids = {}
    for key in ("sources", "pending"):
        for rel, entry in data[key]:
            if entry["id"] in seen_ids:
                errors.append(
                    f"{rel}: id '{entry['id']}' is already used by {seen_ids[entry['id']]}"
                )
            seen_ids[entry["id"]] = rel
    seen_record_ids = {}
    for rel, entry in data["ai_records"]:
        if entry["id"] in seen_record_ids:
            errors.append(
                f"{rel}: id '{entry['id']}' is already used by {seen_record_ids[entry['id']]}"
            )
        seen_record_ids[entry["id"]] = rel

    seen_urls = {}
    for key in ("sources", "pending"):
        for rel, entry in data[key]:
            if "url" not in entry:
                continue
            url = normalize_url(entry["url"])
            if url in seen_urls:
                errors.append(f"{rel}: url {entry['url']} duplicates {seen_urls[url]}")
            seen_urls[url] = rel

    source_ids = {entry["id"] for _, entry in data["sources"]}
    for rel, entry in data["sources"]:
        checked = entry["last_checked"]
        if entry["size"]["as_of"] > checked:
            errors.append(
                f"{rel}: size.as_of {entry['size']['as_of']} is after last_checked {checked}"
            )
        for index, record in enumerate(entry.get("ai_records", [])):
            if record["date"] > checked:
                errors.append(
                    f"{rel}: ai_records/{index}: date {record['date']} is after last_checked {checked}"
                )
    for rel, entry in data["ai_records"]:
        for source_id in entry["related_sources"]:
            if source_id not in source_ids:
                errors.append(
                    f"{rel}: related source '{source_id}' is not a listed source"
                )
        if entry["date"] > entry["last_checked"]:
            errors.append(
                f"{rel}: date {entry['date']} is after last_checked {entry['last_checked']}"
            )
    return errors


def sort_sources(sources):
    order = list(FIELDS)
    return sorted(
        sources,
        key=lambda item: (order.index(item[1]["field"]), item[1]["name"].casefold()),
    )


def build_json(data):
    sources = sort_sources(data["sources"])
    as_of = max(entry["last_checked"] for _, entry in sources)
    document = {
        "schema_version": SCHEMA_VERSION,
        "data_as_of": as_of,
        "license": "CC0-1.0",
        "homepage": f"https://github.com/{REPO}",
        "sources": [dict(entry, file=rel) for rel, entry in sources],
        "ai_records": [
            dict(entry, file=rel)
            for rel, entry in sorted(data["ai_records"], key=lambda i: i[1]["id"])
        ],
        "pending": [
            dict(entry, file=rel)
            for rel, entry in sorted(data["pending"], key=lambda i: i[1]["id"])
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def anchor(heading):
    kept = "".join(ch for ch in heading.lower() if ch.isalnum() or ch in " -")
    return kept.replace(" ", "-")


def record_links(record):
    links = [f"[{n}]({url})" for n, url in enumerate(record["evidence"], start=1)]
    return " ".join(links)


def record_flags(record):
    flags = []
    if record.get("disputed"):
        disputes = " ".join(f"[dispute]({url})" for url in record["dispute_evidence"])
        flags.append(f"disputed {disputes}")
    if record.get("secondhand"):
        flags.append("secondhand")
    return ", ".join(flags)


def build_readme(data, root):
    intro = (root / "templates" / "README.intro.md").read_text(
        encoding="utf-8"
    ).rstrip() + "\n"
    footer = (root / "templates" / "README.footer.md").read_text(
        encoding="utf-8"
    ).rstrip() + "\n"
    sources = sort_sources(data["sources"])
    by_field = {
        field: [entry for _, entry in sources if entry["field"] == field]
        for field in FIELDS
    }
    names = {entry["id"]: entry["name"] for _, entry in sources}

    out = [
        intro,
        "<!-- Everything from here to the Contributing section is generated by scripts/build.py from the YAML files. Edit those files or templates/, not this README. -->\n",
    ]
    out.append("## Contents\n")
    for field, heading in FIELDS.items():
        if by_field[field]:
            out.append(f"- [{heading}](#{anchor(heading)}) ({len(by_field[field])})")
    out.append("- [AI records](#ai-records)")
    out.append("- [Pending](#pending)")
    out.append("- [Contributing](#contributing)")
    out.append("- [License](#license)\n")
    empty = [heading for field, heading in FIELDS.items() if not by_field[field]]
    if empty:
        out.append(
            f"No source in {', '.join(empty)} has passed the checks yet. Suggestions are welcome.\n"
        )

    for field, heading in FIELDS.items():
        entries = by_field[field]
        if not entries:
            continue
        out.append(f"## {heading}\n")
        out.append(
            "| Source | What it is | Verified by | Verifier access | Submit via | Lifecycle | Checked |"
        )
        out.append("|---|---|---|---|---|---|---|")
        for entry in entries:
            out.append(
                "| "
                + " | ".join(
                    [
                        f"[{cell(entry['name'])}]({entry['url']})",
                        cell(entry["description"]),
                        cell(", ".join(entry["verification"])),
                        cell(entry["verifier_access"]),
                        cell(", ".join(entry["submission"])),
                        cell(entry["lifecycle"]),
                        entry["last_checked"],
                    ]
                )
                + " |"
            )
        out.append("")

    out.append("## AI records\n")
    out.append(
        "Claims that an AI system made progress, grouped by source and listed by date. "
        "This is a record of evidence, not a scoreboard, so sources are not ranked by it. "
        "`Evidence` is the evidence ladder and `Autonomy` says who did the work; see the legend above.\n"
    )
    out.append(
        "| Source | Date | Claim | System | Evidence | Autonomy | Flags | Links |"
    )
    out.append("|---|---|---|---|---|---|---|---|")
    for _, entry in sorted(sources, key=lambda item: item[1]["name"].casefold()):
        for record in sorted(entry.get("ai_records", []), key=lambda r: r["date"]):
            out.append(
                "| "
                + " | ".join(
                    [
                        cell(entry["name"]),
                        record["date"],
                        cell(record["summary"]),
                        cell(record.get("system", "")),
                        record["level"],
                        record["autonomy"],
                        record_flags(record),
                        record_links(record),
                    ]
                )
                + " |"
            )
    out.append("")
    if data["ai_records"]:
        out.append("### Claims not tied to one source\n")
        out.append(
            "| Claim | Date | System | Related sources | Evidence | Autonomy | Flags | Links |"
        )
        out.append("|---|---|---|---|---|---|---|---|")
        for _, record in sorted(data["ai_records"], key=lambda item: item[1]["date"]):
            related = ", ".join(
                names[source_id] for source_id in record["related_sources"]
            )
            out.append(
                "| "
                + " | ".join(
                    [
                        cell(record["title"]),
                        record["date"],
                        cell(record.get("system", "")),
                        cell(related),
                        record["level"],
                        record["autonomy"],
                        record_flags(record),
                        record_links(record),
                    ]
                )
                + " |"
            )
        out.append("")

    out.append("## Pending\n")
    out.append(
        f"{len(data['pending'])} candidates are waiting in [`pending/`](pending/) until someone confirms their URL and key facts. "
        "Each file lists what to check.\n"
    )
    for _, entry in sorted(
        data["pending"], key=lambda item: item[1]["name"].casefold()
    ):
        out.append(
            f"- **{entry['name']}** ({FIELDS[entry['field']]}): {entry['reason']}"
        )
    out.append("")
    out.append(footer)
    return "\n".join(out)


def build_llms(data):
    sources = sort_sources(data["sources"])
    as_of = max(entry["last_checked"] for _, entry in sources)
    fields_used = sorted(
        {entry["field"] for _, entry in sources}, key=list(FIELDS).index
    )
    out = [
        "# awesome-breakthroughs",
        "",
        f"> Curated, verification-first index of open-problem sources where AI agents can make checkable progress. "
        f"{len(sources)} sources across {len(fields_used)} fields, each checked by hand; latest check {as_of}. Data is CC0-1.0.",
        "",
        "Every source records how solutions are verified (formal, score, bound, review, blind or self-reported), "
        "whether you can run the verifier yourself (verifier_access), and how to submit. "
        "AI claims carry an evidence level (claimed, machine-checked, source-accepted, peer-reviewed) and an autonomy label "
        "(autonomous, human+ai, human-led-ai-tools, unknown). Treat anything below source-accepted as unconfirmed.",
        "",
        "## Data",
        "",
        f"- [problems.json]({RAW_BASE}/dist/problems.json): every source, AI record and pending candidate as JSON",
        f"- [source schema]({RAW_BASE}/schema/source.schema.json): field definitions, including the evidence ladder",
        f"- [README](https://github.com/{REPO}#readme): the same list as tables",
        f"- [CONTRIBUTING](https://github.com/{REPO}/blob/main/CONTRIBUTING.md): how to add or update a source",
        "",
    ]
    for field in fields_used:
        out.append(f"## {FIELDS[field]}")
        out.append("")
        for _, entry in sources:
            if entry["field"] != field:
                continue
            out.append(
                f"- [{entry['name']}]({entry['url']}): {entry['description']} "
                f"Verification: {', '.join(entry['verification'])}. Verifier access: {entry['verifier_access']}. "
                f"Submit via: {', '.join(entry['submission'])}. Lifecycle: {entry['lifecycle']}."
            )
        out.append("")
    return "\n".join(out)


def outputs(root):
    data, errors = load_entries(root)
    if errors:
        raise BuildError("\n".join(errors))
    if not data["sources"]:
        raise BuildError("no sources found under sources/")
    return {
        root / "README.md": build_readme(data, root),
        root / "dist" / "problems.json": build_json(data),
        root / "llms.txt": build_llms(data),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check", action="store_true", help="fail if a generated file is out of date"
    )
    args = parser.parse_args(argv)
    try:
        generated = outputs(ROOT)
    except BuildError as exc:
        print(f"Validation failed:\n{exc}", file=sys.stderr)
        return 1

    stale = []
    for path, content in generated.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if args.check:
            stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT).as_posix()}")
    if stale:
        print(
            "Generated files are out of date: "
            + ", ".join(stale)
            + "\nRun `python scripts/build.py` and commit the result.",
            file=sys.stderr,
        )
        return 1
    if args.check:
        print("All entries are valid and generated files are up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
