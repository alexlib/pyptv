import re
import os
from pathlib import Path

# Define the current version
CURRENT_VERSION = "0.2.9"

def bump_version(version):
    """Increment the last integer of the version string by 1."""
    parts = version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)

def update_version_in_file(file_path, old_version, new_version):
    """Update the version number in the given file."""
    with open(file_path, 'r') as file:
        content = file.read()

    updated_content = re.sub(re.escape(old_version), new_version, content)

    with open(file_path, 'w') as file:
        file.write(updated_content)

    return updated_content != content

def search_and_update_versions(directory, old_version, new_version):
    """Search for all files in the directory and update the version number."""
    changed_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.yaml'):
                file_path = Path(root) / file
                if update_version_in_file(file_path, old_version, new_version):
                    changed_files.append(file_path)
    return changed_files

if __name__ == '__main__':
    # Define the directory to search for version updates
    directory_to_search = Path('.')

    # Calculate the new version
    new_version = bump_version(CURRENT_VERSION)

    # Search and update versions in files
    changed_files = search_and_update_versions(directory_to_search, CURRENT_VERSION, new_version)

    # Print the changed files
    if changed_files:
        print("Updated version in the following files:")
        for file_path in changed_files:
            print(file_path)
    else:
        print("No files were updated.")