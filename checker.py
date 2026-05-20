"""
Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
Copyright (c) 2024 Joshua R <https://p.utty.dev/>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import argparse
from collections import defaultdict
import fnmatch

MAP_RELATED_FILES = ["*.ytd", "*.ymt", "*.ydr", "*.ydd", "*.ytyp", "*.ybn", "*.ycd", "*.ymap", "*.ynv", "*.ypt"]

def scan_directory(directory, ignored_files=None):
    """Walk *directory* and group map-related files by lowercased filename.

    Returns a dict mapping ``filename -> [paths]``. This is the exact data the
    CLI has always built internally; both the CLI and the GUI consume it.
    """
    file_dict = defaultdict(list)

    for foldername, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.normpath(os.path.join(foldername, filename))

            if not any(fnmatch.fnmatch(filename.lower(), pattern.lower()) for pattern in MAP_RELATED_FILES):
                continue

            if ignored_files and any(fnmatch.fnmatch(filename.lower(), pattern.lower()) for pattern in ignored_files):
                continue

            file_key = filename.lower()
            file_dict[file_key].append(file_path)

    return file_dict

def find_collisions(directory, ignored_files=None, output_file=None):
    file_dict = scan_directory(directory, ignored_files)
    collisions = 0

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for filename, paths in file_dict.items():
                if len(paths) > 1:
                    f.write(f'Possible collisions: {filename}\n')
                    for path in paths:
                        f.write(f'   - {path}\n')
                    f.write('\n')
                    collisions += 1

            f.write(f"Total collisions found: {collisions}\n")

        print(f"All collisions written to '{output_file}'.")
    else:
        for filename, paths in file_dict.items():
            if len(paths) > 1:
                print(f'Possible collisions: {filename}')
                for path in paths:
                    print(f'   - {path}')
                print()
                collisions += 1

        print(f"Total collisions found: {collisions}")

    return collisions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find map collisions in a directory.")
    parser.add_argument("directory", help="The directory to scan for map collisions.")
    parser.add_argument("--ignore", nargs="+", default=[], help="List of file patterns to ignore.")
    parser.add_argument("--output", help="Output file to write the list of collisions to.")
    args = parser.parse_args()

    collisions = find_collisions(args.directory, ignored_files=args.ignore, output_file=args.output)
    sys.exit(1 if collisions else 0)