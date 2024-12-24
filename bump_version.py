def update_version_in_file(file_path, old_version, new_version):
    """Update the version number in the given file."""
    with open(file_path, 'r') as file:
        content = file.read()

    updated_content = re.sub(re.escape(old_version), new_version, content)

    with open(file_path, 'w') as file:
        file.write(updated_content)

    return updated_content != content

if __name__ == '__main__':
    # Define the directory to search for version updates
    directory_to_search = Path('.')
    current_version_file = Path('pyptv/__version__.py')
    
    # Read the current version
    current_version = read_current_version(current_version_file)
    
    # Calculate the new version
    new_version = bump_version(current_version, args.bump_type)
    
    # Update the version in __version__.py
    update_version_in_file(current_version_file, current_version, new_version, args.dry_run)
    
    # Search and update versions in other files
    changed_files = search_and_update_versions(directory_to_search, current_version, new_version, args.dry_run)
    
    # Print the changed files
    if changed_files:
        logging.info("Updated version in the following files:")
        for file_path in changed_files:
            logging.info(file_path)
    else:
        logging.info("No files were updated.")
