import sys
import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# ==============================================================================
# --- FORMATTING CONFIGURATION ---
# Centralized constants for easy customization of the output.
# ==============================================================================

# --- Terminal Output ---
TERMINAL_WIDTH = 80
TERMINAL_HEADER_LINE = "=" * TERMINAL_WIDTH

# --- Report File Output ---
FILE_LINE_WIDTH = 120
FILE_HEADER_LINE = "=" * FILE_LINE_WIDTH
FILE_SEPARATOR_LINE = "-" * FILE_LINE_WIDTH

# --- Status Icons ---
STATUS_ICONS = {
    'identical': '✅',
    'modified': '⚠️',
    'missing': '❌'
}

# --- Summary Section Formatting ---
SUMMARY_LABEL_PADDING = 45  # Space reserved for the description labels
SUMMARY_BAR_LENGTH = 40     # Total characters for the emoji bar chart
BAR_CHART_CHARS = {
    'identical': '🟩',
    'modified': '🟨',
    'missing': '🟥'
}
# ==============================================================================

class Colors:
    """A simple class to hold color constants for terminal output."""
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    RESET = Style.RESET_ALL

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Draws a progress bar in the terminal."""
    if total == 0: total = 1
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total: sys.stdout.write('\n')

def write_report_file(output_filename, base_path, target_path, comparison_data, status_counts):
    """
    Writes the complete comparison report to a text file.
    This function handles all file I/O and formatting for the final output.
    """
    total_items = sum(status_counts.values())

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        # --- 1. File Header ---
        outfile.write(f"{FILE_HEADER_LINE}\n")
        outfile.write(f"{FILE_HEADER_LINE}\n")
        outfile.write("Fractalcode - Codebase Compass\n")
        outfile.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write(f"Base Project: {base_path}\n")
        outfile.write(f"Target Project: {target_path}\n")
        outfile.write(f"{FILE_HEADER_LINE}\n\n")

        # --- 2. Comparison Summary ---
        outfile.write(f"{FILE_SEPARATOR_LINE}\n")
        summary_header = "--- COMPARISON SUMMARY "
        outfile.write(f"{summary_header}{'-' * (FILE_LINE_WIDTH - len(summary_header))}\n")
        if total_items == 0:
            outfile.write("No items found to compare with the current filters.\n")
        else:
            total_identical = status_counts.get('identical', 0)
            total_modified = status_counts.get('modified', 0)
            total_missing = status_counts.get('missing', 0)

            percent_identical = (total_identical / total_items) * 100
            percent_modified = (total_modified / total_items) * 100
            percent_missing = (total_missing / total_items) * 100

            outfile.write(f"  Total items compared: {total_items}\n\n")

            outfile.write(f"  {STATUS_ICONS['identical']} { 'Identical (or directory exists):':<{SUMMARY_LABEL_PADDING}} {total_identical:>5} ({percent_identical:5.1f}% )\n")
            outfile.write(f"  {STATUS_ICONS['modified']} { 'Exists but content is different:':<{SUMMARY_LABEL_PADDING}} {total_modified:>5} ({percent_modified:5.1f}% )\n")
            outfile.write(f"  {STATUS_ICONS['missing']} { 'Does not exist in the target project:':<{SUMMARY_LABEL_PADDING}} {total_missing:>5} ({percent_missing:5.1f}% )\n")

            chars_identical = round((percent_identical / 100) * SUMMARY_BAR_LENGTH)
            chars_modified = round((percent_modified / 100) * SUMMARY_BAR_LENGTH)
            chars_missing = round((percent_missing / 100) * SUMMARY_BAR_LENGTH)

            current_total_chars = chars_identical + chars_modified + chars_missing
            if current_total_chars != SUMMARY_BAR_LENGTH:
                diff = SUMMARY_BAR_LENGTH - current_total_chars
                max_val = max(percent_identical, percent_modified, percent_missing)
                if max_val == percent_identical: chars_identical += diff
                elif max_val == percent_modified: chars_modified += diff
                else: chars_missing += diff

            bar_chart_line = (
                "  " +
                BAR_CHART_CHARS['identical'] * chars_identical +
                BAR_CHART_CHARS['modified'] * chars_modified +
                BAR_CHART_CHARS['missing'] * chars_missing
            )
            outfile.write(f"\n{bar_chart_line}")

        outfile.write(f"\n{FILE_SEPARATOR_LINE}\n\n")

        # --- 3. Detailed Comparison Tree ---
        outfile.write(f"{FILE_SEPARATOR_LINE}\n")
        detailed_header = "--- DETAILED COMPARISON "
        outfile.write(f"{detailed_header}{'-' * (FILE_LINE_WIDTH - len(detailed_header))}\n")

        outfile.write(f"{base_path.name}/\n")

        # Render the tree from the raw data
        tree_lines = [
            f"{prefix}{connector}{name} {STATUS_ICONS[status_key]}"
            for prefix, connector, name, status_key in comparison_data
        ]
        outfile.write("\n".join(tree_lines))

        outfile.write(f"\n{FILE_SEPARATOR_LINE}\n")