#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core analysis engine for Codebase Compass.

This script contains the main logic for comparing two codebases,
identifying structural and content differences.
"""

import os
import json
import argparse
import sys
import datetime
import re
import hashlib
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class Colors:
    """A simple class to hold color constants for terminal output."""
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    RESET = Style.RESET_ALL

# --- (Las funciones de soporte no cambian) ---
def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    if total == 0: total = 1
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total: sys.stdout.write('\n')

def load_config(config_path='config.json'):
    try:
        with open(config_path, 'r') as f: return json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Configuration file not found at '{config_path}'.")
        print(f"{Colors.YELLOW}Please copy 'config.template.json' to 'config.json' and set the project paths.")
        return None
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Could not decode JSON from '{config_path}'. Please check its format.")
        return None

def is_ignored(path_segment, ignored_patterns, ignored_extensions):
    if path_segment in ignored_patterns: return True
    _, extension = os.path.splitext(path_segment)
    if extension and extension in ignored_extensions: return True
    return False

def are_files_identical(path1, path2):
    try:
        if os.path.getsize(path1) != os.path.getsize(path2):
            return False
        hasher1 = hashlib.sha256()
        hasher2 = hashlib.sha256()
        with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
            while chunk := f1.read(8192):
                hasher1.update(chunk)
            while chunk := f2.read(8192):
                hasher2.update(chunk)
        return hasher1.hexdigest() == hasher2.hexdigest()
    except (FileNotFoundError, OSError):
        return False

def generate_tree_comparison(base_root, target_root, ignored_patterns, ignored_extensions, quick_scan=False):
    tree_dict = {}
    status_counts = {'✅': 0, '⚠️': 0, '❌': 0}
    for root, dirs, files in os.walk(base_root, topdown=True):
        dirs[:] = [d for d in dirs if not is_ignored(d, ignored_patterns, ignored_extensions)]
        files[:] = [f for f in files if not is_ignored(f, ignored_patterns, ignored_extensions)]
        relative_path = os.path.relpath(root, base_root)
        path_parts = [] if relative_path == "." else relative_path.split(os.sep)
        current_level = tree_dict
        for part in path_parts:
            current_level = current_level.setdefault(part, {})
        for d in dirs:
            current_level.setdefault(d, {})
        for f in files:
            current_level.setdefault(f, None)

    def build_string_with_comparison(d, prefix='', current_path=''):
        lines = []
        items = sorted(d.keys(), key=lambda x: (d[x] is None, x.lower()))
        for i, name in enumerate(items):
            connector = '└── ' if i == len(items) - 1 else '├── '
            base_path_item = os.path.join(base_root, current_path, name)
            target_path_item = os.path.join(target_root, current_path, name)
            if not os.path.exists(target_path_item):
                status_icon = "❌"
            else:
                is_dir = d[name] is not None
                if is_dir:
                    status_icon = "✅"
                else:
                    if quick_scan:
                        status_icon = "✅"
                    else:
                        if are_files_identical(base_path_item, target_path_item):
                            status_icon = "✅"
                        else:
                            status_icon = "⚠️"
            status_counts[status_icon] += 1
            lines.append(f"{prefix}{connector}{name} {status_icon}")
            if d[name] is not None:
                extension = '    ' if i == len(items) - 1 else '│   '
                lines.extend(build_string_with_comparison(d[name], prefix + extension, os.path.join(current_path, name)))
        return lines

    tree_lines = build_string_with_comparison(tree_dict)
    return tree_lines, status_counts
def main():
    """Main entry point for the analyzer."""
    parser = argparse.ArgumentParser(
        description="Compare a target project against a base codebase to detect drift."
    )
    parser.add_argument(
        '--quick-scan',
        action='store_true',
        help="Perform a quick scan (existence check only), skipping deep content comparison. Default is deep comparison."
    )
    args = parser.parse_args()

    config = load_config()
    if not config: return

    base_path = Path(config.get("base_project_path"))
    target_path = Path(config.get("target_project_path"))

    if not base_path or not base_path.is_dir():
        print(f"{Colors.RED}Error: The 'base_project_path' is not a valid directory: {base_path}")
        return
    if not target_path or not target_path.is_dir():
        print(f"{Colors.RED}Error: The 'target_project_path' is not a valid directory: {target_path}")
        return

    TERMINAL_WIDTH = 80
    FILE_LINE_WIDTH = 120
    TERMINAL_HEADER_LINE = "=" * TERMINAL_WIDTH
    FILE_HEADER_LINE = "=" * FILE_LINE_WIDTH
    FILE_SEPARATOR_LINE = "-" * FILE_LINE_WIDTH

    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")
    print(f"{Colors.CYAN}  INITIALIZING CODEBASE COMPASS")
    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")
    print(f"{Colors.YELLOW}Base Project:   {base_path}")
    print(f"{Colors.YELLOW}Target Project: {target_path}")
    print(f"{Colors.CYAN}Mode:           {'Quick Scan (Existence Only)' if args.quick_scan else 'Deep Content Comparison'}\n")

    print(f"{Colors.CYAN}Phase 1: Analyzing directory structure and content...")
    ignored_patterns = config.get("ignored_patterns", [])
    ignored_extensions = config.get("ignored_file_extensions", [])

    comparison_tree, status_counts = generate_tree_comparison(str(base_path), str(target_path), ignored_patterns, ignored_extensions, quick_scan=args.quick_scan)

    total_items = sum(status_counts.values())
    print(f"{Colors.GREEN}Analysis complete. Found {total_items} items compared.\n")

    print(f"{Colors.CYAN}Phase 2: Writing comparison file...")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    base_name_slug = re.sub(r'[^a-zA-Z0-9_-]', '', base_path.name).lower()
    # --- CORRECCIÓN DEL TYPO ---
    target_name_slug = re.sub(r'[^a-zA-Z0-9_-]', '', target_path.name).lower()
    # --- FIN DE LA CORRECCIÓN ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"comparison_{base_name_slug}_{target_name_slug}_{timestamp}.txt")

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.write(f"{FILE_HEADER_LINE}\n")
        outfile.write(f"{FILE_HEADER_LINE}\n")
        outfile.write("Fractalcode - Codebase Compass\n")
        outfile.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H%M%S')}\n")
        outfile.write(f"Base Project: {base_path}\n")
        outfile.write(f"Target Project: {target_path}\n")
        outfile.write(f"{FILE_HEADER_LINE}\n\n")

        outfile.write(f"{FILE_SEPARATOR_LINE}\n")
        summary_header = "--- COMPARISON SUMMARY "
        outfile.write(f"{summary_header}{'-' * (FILE_LINE_WIDTH - len(summary_header))}\n")
        if total_items == 0:
            outfile.write("No items found to compare with the current filters.\n")
        else:
            total_identical = status_counts.get('✅', 0)
            total_modified = status_counts.get('⚠️', 0)
            total_missing = status_counts.get('❌', 0)

            percent_identical = (total_identical / total_items) * 100
            percent_modified = (total_modified / total_items) * 100
            percent_missing = (total_missing / total_items) * 100

            outfile.write(f"  Total items compared: {total_items}\n")
            label_padding = 45
            outfile.write(f"  ✅ { 'Identical (or directory exists):':<{label_padding}} {total_identical:>5} ({percent_identical:5.1f}% )\n")
            outfile.write(f"  ⚠️ { 'Exists but content is different:':<{label_padding}} {total_modified:>5} ({percent_modified:5.1f}% )\n")
            outfile.write(f"  ❌ { 'Does not exist in the target project:':<{label_padding}} {total_missing:>5} ({percent_missing:5.1f}% )\n")

            bar_length = 40
            chars_identical = round((percent_identical / 100) * bar_length)
            chars_modified = round((percent_modified / 100) * bar_length)
            chars_missing = round((percent_missing / 100) * bar_length)

            current_total_chars = chars_identical + chars_modified + chars_missing
            if current_total_chars != bar_length:
                diff = bar_length - current_total_chars
                max_val = max(percent_identical, percent_modified, percent_missing)
                if max_val == percent_identical: chars_identical += diff
                elif max_val == percent_modified: chars_modified += diff
                else: chars_missing += diff

            bar_chart_line = ("  " + "🟩" * chars_identical + "🟨" * chars_modified + "🟥" * chars_missing)
            outfile.write(f"\n{bar_chart_line}")
        outfile.write(f"\n{FILE_SEPARATOR_LINE}\n\n")

        outfile.write(f"{FILE_SEPARATOR_LINE}\n")
        detailed_header = "--- DETAILED COMPARISON "
        outfile.write(f"{detailed_header}{'-' * (FILE_LINE_WIDTH - len(detailed_header))}\n")

        outfile.write(f"{base_path.name}/\n")
        outfile.write("\n".join(comparison_tree))
        outfile.write(f"\n{FILE_SEPARATOR_LINE}\n")

    print(f"{Colors.GREEN}File writing complete.\n")

    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")
    print(f"{Colors.CYAN}  COMPARISON FINISHED")
    print(f"{Colors.GREEN}  Comparison result saved to:")
    print(f"{Colors.YELLOW}  {output_filename}")
    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")

if __name__ == '__main__':
    main()