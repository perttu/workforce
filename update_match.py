from pathlib import Path
import re

file_path = Path("/Users/perttu/projects/kuitit/tools/match_pipeline.py")
content = file_path.read_text()

# Add logic to detect scan dir at the beginning of main
new_main_start = """def main():
    # Auto-detect scan directory if it exists in standard locations
    additional_pdf_dirs = []
    for p in [Path('/Volumes/nfs/scan'), Path('/mnt/scan')]:
        if p.exists():
            additional_pdf_dirs.append(str(p))
            break

    parser = argparse.ArgumentParser"""

content = re.sub(r'def main\(\):\s+parser = argparse\.ArgumentParser', new_main_start, content)

# Update the default for pdf-dirs to include detected scan dir
# Current default is ["work/pdfout", "work/scanned"]
# We want to keep those but also add the new one if found.

# This is harder to do purely by string replacement because it's a list.
# I'll just inject the logic after parse_args.

logic_injection = """    args = parser.parse_args()
    
    # Add auto-detected scan dirs to pdf_dirs if not explicitly provided
    # Note: argparse defaults to ["work/pdfout", "work/scanned"]
    # We check if it's the default and then append.
    if args.pdf_dirs == ["work/pdfout", "work/scanned"]:
        for d in additional_pdf_dirs:
            if d not in args.pdf_dirs:
                args.pdf_dirs.append(d)
"""

if "args = parser.parse_args()" in content:
    content = content.replace("args = parser.parse_args()", logic_injection)

file_path.write_text(content)
print("Updated match_pipeline.py")
