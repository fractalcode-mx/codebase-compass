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

def is_ignored(relative_path, simple_ignore_set, wildcard_ignore_list, ignored_extensions):
    """
    Checks if a file or directory should be ignored.
    This version performs two fast checks against the simple_ignore_set
    before falling back to the slower wildcard matching.
    """
    path_to_check = relative_path.replace(os.sep, '/')

    # 1. Fast check: full relative path (for patterns like 'app/panel/file.php')
    if path_to_check in simple_ignore_set:
        return True

    # 2. Fast check: basename only (for patterns like '.git', 'node_modules')
    basename = os.path.basename(path_to_check)
    if basename in simple_ignore_set:
        return True

    # 3. Fast check: file extension
    _, extension = os.path.splitext(basename)
    if extension and extension in ignored_extensions:
        return True

    # 4. Slow fallback: wildcard matching for complex patterns
    for pattern in wildcard_ignore_list:
        if fnmatch.fnmatch(path_to_check, pattern):
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
    Generates a data structure representing the directory tree and its comparison status.
    Returns a tuple: (list of raw tree data, dictionary of status counts).
    """
    tree_dict = {}
    status_counts = {'identical': 0, 'modified': 0, 'missing': 0}

    # Pre-process ignore patterns for optimization.
    simple_ignore_set = {p for p in ignored_patterns if '*' not in p and '?' not in p and '[' not in p}
    wildcard_ignore_list = [p for p in ignored_patterns if p not in simple_ignore_set]

    for root, dirs, files in os.walk(base_root, topdown=True):
        current_relative_dir = os.path.relpath(root, base_root)
        if current_relative_dir == ".": current_relative_dir = ""

        original_dirs = list(dirs)
        dirs[:] = [
            d for d in original_dirs
            if not is_ignored(os.path.join(current_relative_dir, d), simple_ignore_set, wildcard_ignore_list, ignored_extensions)
        ]
        files[:] = [
            f for f in files
            if not is_ignored(os.path.join(current_relative_dir, f), simple_ignore_set, wildcard_ignore_list, ignored_extensions)
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

    def build_data_with_comparison(d, prefix='', current_path=''):
        data_list = []
        items = sorted(d.keys(), key=lambda x: (d[x] is None, x.lower()))
        for i, name in enumerate(items):
            connector = '└── ' if i == len(items) - 1 else '├── '
            base_path_item = os.path.join(base_root, current_path, name)
            target_path_item = os.path.join(target_root, current_path, name)

            status_key = ''
            if not os.path.exists(target_path_item):
                status_key = "missing"
            else:
                is_dir = d[name] is not None
                if is_dir:
                    status_key = "identical"
                else:
                    if quick_scan:
                        status_key = "identical"
                    else:
                        if are_files_identical(base_path_item, target_path_item):
                            status_key = "identical"
                        else:
                            status_key = "modified"

            status_counts[status_key] += 1
            data_list.append((prefix, connector, name, status_key))

            if d[name] is not None:
                extension = '    ' if i == len(items) - 1 else '│   '
                data_list.extend(build_data_with_comparison(d[name], prefix + extension, os.path.join(current_path, name)))
        return data_list

    tree_data = build_data_with_comparison(tree_dict)
    return tree_data, status_counts