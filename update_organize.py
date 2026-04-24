from pathlib import Path
import re

file_path = Path("/Users/perttu/projects/kuitit/tools/organize_receipts.py")
content = file_path.read_text()

# Add logic to detect scan dir at the beginning of main
new_main_start = """def main():
    # Auto-detect scan directory if it exists in standard locations
    default_scan_dir = Path('scan')
    for p in [Path('/Volumes/nfs/scan'), Path('/mnt/scan')]:
        if p.exists():
            default_scan_dir = p
            break

    parser = argparse.ArgumentParser"""

if "def main():\n    parser = argparse.ArgumentParser" in content:
    content = content.replace("def main():\n    parser = argparse.ArgumentParser", new_main_start)
elif "def main():\n    # Auto-detect" not in content:
    # Handle different spacing if any
    content = re.sub(r'def main\(\):\s+parser = argparse\.ArgumentParser', new_main_start, content)

# Update the default for input-dir to None to allow dynamic assignment
content = content.replace("default=Path('in/pdf')", "default=None")

# Inject logic after parse_args
logic_injection = """    args = parser.parse_args()

    # Dynamic defaults based on mode
    if args.input_dir is None:
        if args.prefer_ocr:
            # Re-check scan dir in case it was modified above
            args.input_dir = default_scan_dir
        else:
            args.input_dir = Path('in/pdf')
"""

if "args = parser.parse_args()" in content:
    content = content.replace("args = parser.parse_args()", logic_injection)

file_path.write_text(content)
print("Updated organize_receipts.py")
