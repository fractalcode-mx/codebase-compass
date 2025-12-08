import os
import argparse
import datetime
import re
from pathlib import Path

from ui import Colors
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
    target_name_slug = re.sub(r'[^a-zA-Z0-9_-]', '', target_path.name).lower()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"comparison_{base_name_slug}_{target_name_slug}_{timestamp}.txt")

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.write(f"{FILE_HEADER_LINE}\n")
        outfile.write(f"{FILE_HEADER_LINE}\n")
        outfile.write("Fractalcode - Codebase Compass\n")
        outfile.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
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

            outfile.write(f"  Total items compared: {total_items}\n\n")

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