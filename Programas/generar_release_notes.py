#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import PurePosixPath


def run_git(args):
    return subprocess.check_output(["git"] + args, text=True, encoding="utf-8", errors="replace").strip()


def get_last_tag():
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return ""


def get_root_commit():
    return run_git(["rev-list", "--max-parents=0", "HEAD"]).splitlines()[0]


def parse_changes(base_ref):
    diff_range = f"{base_ref}..HEAD"
    output = run_git(["diff", "--name-status", diff_range])
    return [line for line in output.splitlines() if line.strip()]


def extract_mod_name(path):
    path = path.replace("\\", "/")
    if not path.startswith("Archivo Traducciones/"):
        return ""
    parts = PurePosixPath(path).parts
    if len(parts) < 2:
        return ""
    return parts[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base_ref = get_last_tag() or get_root_commit()

    added = set()
    modified = set()
    deleted = set()

    for line in parse_changes(base_ref):
        fields = line.split("\t")
        status = fields[0]
        path = fields[-1]

        mod_name = extract_mod_name(path)
        if not mod_name:
            continue

        if status.startswith("A"):
            added.add(mod_name)
        elif status.startswith("D"):
            deleted.add(mod_name)
        elif status.startswith("M") or status.startswith("R") or status.startswith("C"):
            modified.add(mod_name)

    lines = []
    if modified:
        lines.append("Correcciones:")
        lines.extend([f"- {name}" for name in sorted(modified)])
    if added:
        lines.append("Añadidos:")
        lines.extend([f"- {name}" for name in sorted(added)])
    if deleted:
        lines.append("Ajustes:")
        lines.extend([f"- {name}" for name in sorted(deleted)])

    if not lines:
        lines = ["Sin cambios registrados"]

    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
