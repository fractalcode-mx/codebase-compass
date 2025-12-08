import os
import argparse
import datetime
import re
from pathlib import Path

from ui import Colors, write_report_file, TERMINAL_HEADER_LINE
from analyzer import load_config, generate_tree_comparison

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

    # --- 1. Load configuration and validate paths ---
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

    # --- 2. Initial terminal feedback ---
    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")
    print(f"{Colors.CYAN}  INITIALIZING CODEBASE COMPASS")
    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")
    print(f"{Colors.YELLOW}Base Project:   {base_path}")
    print(f"{Colors.YELLOW}Target Project: {target_path}")
    print(f"{Colors.CYAN}Mode:           {'Quick Scan (Existence Only)' if args.quick_scan else 'Deep Content Comparison'}\n")

    # --- 3. Core analysis logic ---
    print(f"{Colors.CYAN}Phase 1: Analyzing directory structure and content...")
    ignored_patterns = config.get("ignored_patterns", [])
    ignored_extensions = config.get("ignored_file_extensions", [])

    comparison_tree, status_counts = generate_tree_comparison(str(base_path), str(target_path), ignored_patterns, ignored_extensions, quick_scan=args.quick_scan)

    total_items = sum(status_counts.values())
    print(f"{Colors.GREEN}Analysis complete. Found {total_items} items compared.\n")

    # --- 4. Report generation ---
    print(f"{Colors.CYAN}Phase 2: Writing comparison file...")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    base_name_slug = re.sub(r'[^a-zA-Z0-9_-]', '', base_path.name).lower()
    target_name_slug = re.sub(r'[^a-zA-Z0-9_-]', '', target_path.name).lower()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"comparison_{base_name_slug}_{target_name_slug}_{timestamp}.txt")

    write_report_file(
        output_filename,
        base_path,
        target_path,
        comparison_tree,
        status_counts
    )

    print(f"{Colors.GREEN}File writing complete.\n")

    # --- 5. Final terminal feedback ---
    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")
    print(f"{Colors.CYAN}  COMPARISON FINISHED")
    print(f"{Colors.GREEN}  Comparison result saved to:")
    print(f"{Colors.YELLOW}  {output_filename}")
    print(f"{Colors.BLUE}{TERMINAL_HEADER_LINE}")

if __name__ == '__main__':
    main()