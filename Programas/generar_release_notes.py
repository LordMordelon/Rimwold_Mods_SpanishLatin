#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET


def run_git(args, text=True):
    return subprocess.check_output(
        ["git"] + args,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    ).strip()


def get_last_tag():
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return ""


def get_root_commit():
    return run_git(["rev-list", "--max-parents=0", "HEAD"]).splitlines()[0]


def get_repo_root():
    return Path(run_git(["rev-parse", "--show-toplevel"]))


def parse_changes(base_ref):
    diff_range = f"{base_ref}..HEAD"
    output = run_git(["diff", "--name-status", "-z", diff_range], text=False)
    if not output:
        return []

    parts = output.split(b"\x00")
    changes = []
    i = 0
    while i < len(parts) - 1:
        status = parts[i].decode("utf-8", errors="replace")
        i += 1
        if not status:
            continue

        code = status[0]
        if code in {"R", "C"}:
            # status, old path, new path
            if i + 1 >= len(parts):
                break
            old_path = parts[i].decode("utf-8", errors="replace")
            new_path = parts[i + 1].decode("utf-8", errors="replace")
            i += 2
            changes.append((status, old_path))
            changes.append((status, new_path))
        else:
            if i >= len(parts):
                break
            path = parts[i].decode("utf-8", errors="replace")
            i += 1
            changes.append((status, path))

    return changes


def extract_mod_name(path):
    path = path.replace("\\", "/")
    roots = ("Archivo Traducciones/", "Archivo Traducciones Vanilla/")
    if not any(path.startswith(root) for root in roots):
        return ""
    parts = PurePosixPath(path).parts
    if len(parts) < 2:
        return ""
    return parts[1]


def load_mod_display_name(mod_dir, repo_root, name_cache):
    if mod_dir in name_cache:
        return name_cache[mod_dir]

    mod_path = repo_root / "Archivo Traducciones" / mod_dir
    about_path = mod_path / "About"
    if about_path.is_dir():
        xml_paths = sorted(about_path.glob("About_*.xml")) + sorted(about_path.glob("About.xml"))
        for xml_path in xml_paths:
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                name_node = root.find("name")
                if name_node is not None and name_node.text:
                    display_name = name_node.text.strip()
                    if display_name:
                        name_cache[mod_dir] = display_name
                        return display_name
            except (ET.ParseError, OSError):
                continue

    name_cache[mod_dir] = mod_dir
    return mod_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo", required=False)
    parser.add_argument("--tag", required=False)
    args = parser.parse_args()

    base_ref = get_last_tag() or get_root_commit()
    repo_root = get_repo_root()
    name_cache = {}

    added = set()
    modified = set()
    deleted = set()

    for status, path in parse_changes(base_ref):

        mod_name = extract_mod_name(path)
        if not mod_name:
            continue

        if status.startswith("A"):
            added.add(mod_name)
        elif status.startswith("D"):
            deleted.add(mod_name)
        elif status.startswith("M") or status.startswith("R") or status.startswith("C"):
            modified.add(mod_name)

    sections = []

    def add_section(title_singular, title_plural, names):
        if not names:
            return
        title = title_singular if len(names) == 1 else title_plural
        items = [f"- {load_mod_display_name(name, repo_root, name_cache)}" for name in sorted(names)]
        sections.append("\n".join([title] + items))

    add_section("Añadido:", "Añadidos:", added)
    add_section("Actualizado:", "Actualizaciones:", modified)
    add_section("Correccion:", "Correcciones:", deleted)

    if not sections:
        lines = ["Sin cambios registrados"]
    else:
        lines = ["\n\n".join(sections)]

    if args.repo and args.tag and base_ref:
        lines.append("")
        lines.append(f"**Full Changelog**: https://github.com/{args.repo}/compare/{base_ref}...{args.tag}")

    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
