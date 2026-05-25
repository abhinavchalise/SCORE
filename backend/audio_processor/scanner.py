import os
from typing import List

SUPPORTED_FORMATS = {"wav", "flac", "mp3"}


def scan_directory(directory_path: str) -> List[dict]:
    # Walk directory tree, collect audio files matching supported formats
    if not os.path.isdir(directory_path):
        raise ValueError(f"Directory does not exist: {directory_path}")

    tracks = []
    for root, _dirs, files in os.walk(directory_path):
        for filename in files:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in SUPPORTED_FORMATS:
                continue

            file_path = os.path.join(root, filename)
            tracks.append(
                {
                    "file_path": os.path.abspath(file_path),
                    "filename": filename,
                    "format": ext,
                }
            )

    return tracks
