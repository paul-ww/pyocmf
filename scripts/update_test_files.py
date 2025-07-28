#!/usr/bin/env python3
"""
Script to download OCMF XML test files from the transparency software repository.
Run this script when you want to update your test files with the latest versions.
"""

import urllib.request
import pathlib
import os

# Base URL for the transparency software test files
BASE_URL = "https://raw.githubusercontent.com/SAFE-eV/transparenzsoftware/main/src/test/resources/xml"

# List of OCMF-related test files we want to include
OCMF_TEST_FILES = [
    "OCMF_Test_Data_00.xml",
    "Ocmf_Example_OBIS_98.8.0_2.8.0.xml",
    "VW_OCMF_load.xml",
    "brainpoolP256r1.xml",
    "chargepoint_3.xml",
    "ocmf_sec.xml",
    "ocmf_tariff_1.xml",
    "second_key_fail_ocmf.xml",
    "test_ocmf_ebee_01.xml",
    "test_ocmf_ebee_02.xml",
    "test_ocmf_keba_kcp30.xml",
    "test_ocmf_keba_kcp30_fail.xml",
    "test_ocmf_rsa_01.xml",
    "test_ocmf_transaction_two_values.xml",
    "test_input_xml_two_values.xml",
    "20211007-device-with-evt-ocmf-sss-ses.xml",
    "nistP384_0Wh.xml",
]

def download_test_files() -> None:
    """Download OCMF test files from the transparency software repository."""
    
    # Create the target directory
    test_dir = pathlib.Path(__file__).parent.parent / "test" / "resources" / "transparency_xml"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading OCMF test files to {test_dir}")
    
    downloaded = []
    failed = []
    
    for filename in OCMF_TEST_FILES:
        url = f"{BASE_URL}/{filename}"
        target_path = test_dir / filename
        
        try:
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, target_path)
            downloaded.append(filename)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
            failed.append(filename)
    
    print("\nDownload complete!")
    print(f"Successfully downloaded: {len(downloaded)} files")
    if failed:
        print(f"Failed to download: {failed}")
    
    # Create a README explaining the source of these files
    readme_content = f"""# Transparency Software Test Files

These XML test files were downloaded from the SAFE-eV transparency software repository:
https://github.com/SAFE-eV/transparenzsoftware/tree/main/src/test/resources/xml

## Files included:
{chr(10).join(f"- {f}" for f in sorted(downloaded))}

## Updating files:
To update these files with the latest versions from upstream, run:
```bash
python scripts/update_test_files.py
```

Last updated: {os.popen('date').read().strip()}
"""
    
    (test_dir / "README.md").write_text(readme_content)
    print(f"Created README.md in {test_dir}")

if __name__ == "__main__":
    download_test_files()
