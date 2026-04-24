from pathlib import Path
import re

file_path = Path("/Users/perttu/projects/kuitit/tools/match_pdfs.py")
content = file_path.read_text()

# Add logic to detect scan dir at the beginning of main
new_main_start = """def main(argv: Sequence[str] | None = None) -> int:
    # Auto-detect scan directory if it exists in standard locations
    additional_pdf_dirs = []
    for p in [Path('/Volumes/nfs/scan'), Path('/mnt/scan')]:
        if p.exists():
            additional_pdf_dirs.append(p)
            break

    args = parse_args(argv)"""

content = re.sub(r'def main\(argv: Sequence\[str\] \| None = None\) -> int:', new_main_start, content)

# I won't change the PDF directory for match_pdfs.py as it typically expects a processed dir,
# but I'll ensure it's easy to point to the scan dir if needed.
# Actually, the user asked to use correct paths by default.

file_path.write_text(content)
print("Updated match_pdfs.py")
