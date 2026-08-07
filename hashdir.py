#!/usr/bin/env python3
import hashlib
import os
from shlex import quote
from sys import argv


def rename_to_hash(directory_path):
    # Store the original > hash mapping as a shell script to revert
    mapping_file = "mapping.txt"

    try:
        os.chdir(directory_path)
    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' was not found.")
        return

    with open(mapping_file, "a") as log:
        for filename in os.listdir("."):
            # Skip the mapping file itself and directories
            if filename == mapping_file or os.path.isdir(filename):
                continue

            file_hash = hashlib.sha1(filename.encode('utf-8')).hexdigest()

            # Preserve the file extension
            extension = os.path.splitext(filename)[1]
            new_name = f"{file_hash}{extension}"

            try:
                os.rename(filename, new_name)
                log.write(f"mv -n {quote(new_name)} {quote(filename)}\n")
                print(f"Renamed: {filename} -> {new_name}")
            except Exception as e:
                print(f"Failed to rename {filename}: {e}")


if __name__ == "__main__":
    target_dir = argv[1] if len(argv) > 1 else "."
    rename_to_hash(target_dir)
