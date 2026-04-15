"""
Script to update the codemeta.json file used for software heritage.

With the option --update, this script will update codemeta.json with the content
from the last version found in CHANGELOG.md (release date, release notes, and version number).
This option is used manually to update the file.

With the option --check-up-to-date, this script will only check if codemeta.json is already
up to date or if it needs to be updated.
This option is used in the CI when a git tag is made to verify that the file is up-to-date.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parseLatestChangelog(changelog_text: str):
    """
    Extract the latest version block from a Keep-a-Changelog formatted file.

    Returns:
        (version: str, release_date: str, release_notes: str)
    """

    lines = changelog_text.splitlines()

    version = None
    collecting = False
    current_section = None
    release_date = None

    notes = []

    for line in lines:
        # Match version header: ## 2025.12.918-beta - 2025-12-18
        match_version = re.match(r"^##\s+(.+?)\s+-\s+(\d{4}-\d{2}-\d{2})", line)
        if match_version:
            if version is None:
                version = match_version.group(1).strip()
                release_date = match_version.group(2).strip()
                collecting = True
                continue
            # next version encountered → stop parsing
            break

        if not collecting:
            continue

        # Detect section headers
        match_section = re.match(r"^###\s+(.+)", line)
        if match_section:
            current_section = match_section.group(1).strip()
            if len(notes) > 0:
                notes.append("")
            notes.append("## " + current_section)
            continue

        # Collect bullet points
        match_bullet = re.match(r"^\s*-\s+(.*)", line)
        if match_bullet:
            notes.append(f"- {match_bullet.group(1).strip()}")

    release_notes = "\n".join(notes).strip()
    return version, release_date, release_notes


def main():
    """Main script"""

    parser = argparse.ArgumentParser(description="Sync codemeta.json with CHANGELOG.md")

    parser.add_argument("--codemeta", default="codemeta.json")
    parser.add_argument("--changelog", default="CHANGELOG.md")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check-up-to-date", action="store_true", help="Check if codemeta.json matches changelog-derived values"
    )
    group.add_argument("--update", action="store_true", help="Update codemeta.json if needed")

    args = parser.parse_args()

    changelog_path = Path(args.changelog)
    codemeta_path = Path(args.codemeta)

    with codemeta_path.open("r", encoding="utf-8") as f:
        current = json.load(f)

    changelog_text = changelog_path.read_text(encoding="utf-8")
    version, release_date, release_notes = parseLatestChangelog(changelog_text)

    if args.check_up_to_date:
        if (
            version == current["version"]
            and release_notes == current["schema:releaseNotes"]
            and release_date == current["dateModified"]
        ):
            print("OK: codemeta.json is up to date with CHANGELOG.")
            sys.exit(0)
        print("NOT OK: codemeta.json is NOT up to date with CHANGELOG.")
        print(f"Expected: {version=} but current is {current['version']}")
        print("Run this script with the --update option to create an up-to-date codemeta.json file")
        sys.exit(1)

    if args.update:
        if (
            version == current["version"]
            and release_notes == current["schema:releaseNotes"]
            and release_date == current["dateModified"]
        ):
            print("No update needed: codemeta.json already up to date.")
            sys.exit(0)

        expected = current.copy()
        expected["version"] = version
        expected["schema:releaseNotes"] = release_notes
        expected["dateModified"] = release_date
        with codemeta_path.open("w", encoding="utf-8") as f:
            json.dump(expected, f, indent=4, ensure_ascii=False)
            f.write("\n")

        print("codemeta.json updated successfully.")


if __name__ == "__main__":
    main()
