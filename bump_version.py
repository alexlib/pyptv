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

def update_version(version_file, new_version):
    """Update the version string in pyproject.toml."""
    with open(version_file, 'r') as file:
        content = file.read()

    updated_content = re.sub(r'__version__\s*=\s*".*"', f'version = "{new_version}"', content)

    with open(version_file, 'w') as file:
        file.write(updated_content)

def increment_version(version, part='minor'):
    """Increment the version string. use major, minor, patch """
    major, minor, patch = map(int, version.split('.'))
    
    if part == 'major':
        major += 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor += 1
        patch = 0
    else:
        raise ValueError("Invalid part specified. Use 'major' or 'minor'.")
    
    return f"{major}.{minor}.{patch}"


if __name__ == '__main__':
    version_file = Path('pyptv/__version__.py')
    pyproject_file = Path('pyproject.toml')

    # Get the current version from __version__.py
    current_version = get_version_from_file(version_file)
    print(f"Current version is {current_version}")

    # Example usage
    new_version = increment_version(current_version, 'minor')
    print(f"New version is {new_version}")

    # Update the version in pyproject.toml
    update_pyproject_version(pyproject_file, new_version)
    update_version(version_file, new_version)

    print(f"Updated pyproject.toml to version {new_version}")