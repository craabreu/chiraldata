import pathlib
import subprocess

DOWNLOAD_DIR = pathlib.Path.cwd().parent / "downloads"
doc_files = list(DOWNLOAD_DIR.glob("*/*.doc*"))

for doc_file in doc_files:
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(doc_file.parent),
            str(doc_file),
        ]
    )
