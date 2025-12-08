import os
import json
import hashlib
import fnmatch
from ui import Colors

def load_config(config_path='config.json'):
    """Loads the configuration file."""
    try:
        with open(config_path, 'r') as f: return json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Configuration file not found at '{config_path}'.")
        print(f"{Colors.YELLOW}Please copy 'config.template.json' to 'config.json' and set the project paths.")
        return None
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Could not decode JSON from '{config_path}'. Please check its format.")
        return None

def is_ignored(relative_path, ignored_patterns, ignored_extensions):
    """
    Checks if a file or directory should be ignored based on its full relative path.
    Uses fnmatch for wildcard support.
    """
    path_to_check = relative_path.replace(os.sep, '/')
    for pattern in ignored_patterns:
        if fnmatch.fnmatch(path_to_check, pattern):
            return True
    _, extension = os.path.splitext(path_to_check)
    if extension and extension in ignored_extensions:
        return True
    return False

def are_files_identical(path1, path2):
    """Efficiently compares two files. First by size, then by SHA-256 hash."""
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
    """
    Generates a visual directory tree of the base_root, comparing each item
    against the target_root.
    Returns a tuple: (list of tree lines, dictionary of status counts).
    """
    tree_dict = {}
    status_counts = {'✅': 0, '⚠️': 0, '❌': 0}

    for root, dirs, files in os.walk(base_root, topdown=True):
        current_relative_dir = os.path.relpath(root, base_root)
        if current_relative_dir == ".": current_relative_dir = ""

        original_dirs = list(dirs)
        dirs[:] = [
            d for d in original_dirs
            if not is_ignored(os.path.join(current_relative_dir, d), ignored_patterns, ignored_extensions)
        ]
        files[:] = [
            f for f in files
            if not is_ignored(os.path.join(current_relative_dir, f), ignored_patterns, ignored_extensions)
        ]

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