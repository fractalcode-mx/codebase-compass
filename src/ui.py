import sys
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

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Draws a progress bar in the terminal."""
    if total == 0: total = 1
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total: sys.stdout.write('\n')