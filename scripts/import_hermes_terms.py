#!/usr/bin/env python3
"""Import project-scoped terms from the pinned Hermes Agent review archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ARCHIVE_COMMIT = "f60889b413494b02c1bc9765d92bca524a7ce1ea"
DOC_PATH = "Hermes-Agent/20261114/TERMINOLOGY.md"
DOC_SHA256 = "0cc27102ea244eebe84787e0d922bc673225d47cf858ed8fe16f06a4eda2d59d"
SOURCE_REVISION = "abeeef4d491cba7ea6126a2f54d81c879da5059f"
OUTPUT = Path(__file__).resolve().parents[1] / "reviewed/data/hermes-agent-20261114.jsonl"
EXCLUDED = {"charge"}  # The archive combines two parts of speech in one row.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("translations_repo", type=Path, help="yeager/translations checkout")
    parser.add_argument("--write", action="store_true", help="write the generated JSONL")
    args = parser.parse_args()
    raw = subprocess.check_output([
        "git", "-C", str(args.translations_repo), "show", f"{ARCHIVE_COMMIT}:{DOC_PATH}"
    ])
    digest = hashlib.sha256(raw).hexdigest()
    if digest != DOC_SHA256:
        raise ValueError("Hermes terminology source checksum mismatch")

    rows = []
    for line in raw.decode("utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Engelska"):
            continue
        fields = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(fields) != 3:
            raise ValueError(f"unexpected terminology table row: {line}")
        source, canonical, context = fields
        if source in EXCLUDED:
            continue
        if len(source.split()) > 6 or len(source) > 65 or len(canonical) > 100:
            raise ValueError(f"term exceeds glossary selection limits: {source}")
        identifier = hashlib.sha256(f"Hermes Agent\0{source}\0{context}".encode()).hexdigest()[:24]
        rows.append({
            "id": identifier,
            "source": source,
            "canonical": canonical,
            "project": "Hermes Agent",
            "component": "Hermes Agent terminology",
            "context": context,
            "note": f"Projektterminologi från lokalt granskad Hermes-katalog. {context}",
            "scope": "project-context",
            "review_id": "hermes-agent-20261114-terminology",
            "publication_status": "local-reviewed-terminology",
            "evidence": {
                "artifact": f"https://github.com/yeager/translations/blob/{ARCHIVE_COMMIT}/{DOC_PATH}",
                "sha256": DOC_SHA256,
            },
            "source_evidence": {
                "format": "Markdown terminology table",
                "reviewed_archive_commit": ARCHIVE_COMMIT,
                "source_catalog": f"https://github.com/NousResearch/hermes-agent/blob/{SOURCE_REVISION}/locales/en.yaml",
                "source_revision": SOURCE_REVISION,
            },
        })
    if len(rows) != 22:
        raise ValueError(f"expected 22 unambiguous terms, got {len(rows)}")
    encoded = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    if args.write:
        OUTPUT.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(f"Validated {len(rows)} project-scoped terms; use --write to save {OUTPUT}")


if __name__ == "__main__":
    main()
