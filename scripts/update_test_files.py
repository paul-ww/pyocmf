#!/usr/bin/env python3
"""
Script to download XML test files from the transparency software repository.
Run this script when you want to update your test files with the latest versions.
Uses git sparse-checkout to download the entire XML test directory structure.
"""

import subprocess
import pathlib
import os
import shutil
import tempfile

# Repository URL and target directory path
REPO_URL = "https://github.com/SAFE-eV/transparenzsoftware.git"
SOURCE_PATH = "src/test/resources/xml"

def download_test_files() -> None:
    """Download entire XML test directory from the transparency software repository."""
    
    # Create the target directory
    test_dir = pathlib.Path(__file__).parent.parent / "test" / "resources" / "transparency_xml"
    test_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading XML test files to {test_dir}")

    # Create a temporary directory for the git clone
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        repo_path = temp_path / "transparenzsoftware"
        original_cwd = os.getcwd()

        try:
            print("Cloning repository with sparse checkout...")

            # Initialize git repository
            subprocess.run(
                ["git", "clone", "--no-checkout", REPO_URL, str(repo_path)],
                check=True,
                capture_output=True,
            )

            # Change to repo directory
            os.chdir(repo_path)

            # Configure sparse checkout
            subprocess.run(
                ["git", "sparse-checkout", "init", "--cone"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "sparse-checkout", "set", SOURCE_PATH],
                check=True,
                capture_output=True,
            )

            # Checkout the files
            subprocess.run(["git", "checkout"], check=True, capture_output=True)

            # Copy the XML directory to our target location
            source_xml_dir = repo_path / SOURCE_PATH
            if source_xml_dir.exists():
                # Remove existing files and directories
                for item in test_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()

                # Copy all files and directories from source
                for item in source_xml_dir.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, test_dir / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, test_dir / item.name)

                print(f"Successfully downloaded XML test directory to {test_dir}")

                # Count downloaded files
                file_count = sum(1 for item in test_dir.rglob("*") if item.is_file())
                print(f"Downloaded {file_count} files from XML test directory")

            else:
                print(f"Error: Source directory {SOURCE_PATH} not found in repository")
                return

        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            print(
                f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}"
            )
            return
        except Exception as e:
            print(f"Error during download: {e}")
            return
        finally:
            # Restore original working directory
            os.chdir(original_cwd)


if __name__ == "__main__":
    download_test_files()
