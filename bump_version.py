import re
from pathlib import Path

def get_version_from_file(version_file):
    """Read the version string from the specified file."""
    with open(version_file, 'r') as file:
        content = file.read()
        match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
        if match:
            return match.group(1)
        raise RuntimeError("Unable to find version string.")

def update_pyproject_version(pyproject_file, new_version):
    """Update the version string in pyproject.toml."""
    with open(pyproject_file, 'r') as file:
        content = file.read()

    updated_content = re.sub(r'version\s*=\s*".*"', f'version = "{new_version}"', content)

    with open(pyproject_file, 'w') as file:
        file.write(updated_content)

if __name__ == '__main__':
    version_file = Path('pyptv/__version__.py')
    pyproject_file = Path('pyproject.toml')

    # Get the current version from __version__.py
    current_version = get_version_from_file(version_file)

    # Update the version in pyproject.toml
    update_pyproject_version(pyproject_file, current_version)

    print(f"Updated pyproject.toml to version {current_version}")