import os
import re
from collections import defaultdict

# Directory where your static files are located
static_dirs = [
    '/usr/src/geonode/geonode/static',
    # Add more directories as needed
]

# Dictionary to keep track of file occurrences
file_occurrences = defaultdict(list)

# Function to scan directories and detect duplicates
def scan_directories(directories):
    for static_dir in directories:
        for root, _, files in os.walk(static_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, static_dir)
                file_occurrences[relative_path].append(file_path)

# Function to rename duplicate files and update references
def rename_duplicates_and_update_references():
    for relative_path, file_paths in file_occurrences.items():
        if len(file_paths) > 1:
            for index, file_path in enumerate(file_paths):
                if index == 0:
                    continue  # Keep the first file as is
                new_file_path = f"{file_path.rsplit('.', 1)[0]}_{index}.{file_path.rsplit('.', 1)[1]}"
                os.rename(file_path, new_file_path)
                print(f"Renamed {file_path} to {new_file_path}")
                update_references(relative_path, new_file_path)

# Function to update file references in HTML, CSS, and JavaScript files
def update_references(old_path, new_path):
    search_path = '/usr/src/geonode/'  # Root directory to search for references
    old_file_name = os.path.basename(old_path)
    new_file_name = os.path.basename(new_path)
    
    for root, _, files in os.walk(search_path):
        for file in files:
            if file.endswith(('.html', '.css', '.js')):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                new_content = re.sub(rf'\b{old_file_name}\b', new_file_name, content)
                if content != new_content:
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    print(f"Updated references in {file_path}")

# Scan directories for duplicates
scan_directories(static_dirs)

# Rename duplicate files and update references
rename_duplicates_and_update_references()
