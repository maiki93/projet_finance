"""
Helper methods and template data for tests.

Keep separate from conftest.py, specifc for fixtures
"""

import json
from pathlib import Path


def create_file_with_content(tmp_path: Path, filename: str, content: str | dict | None = None) -> Path:

    tmp_file = tmp_path / filename
    with open(tmp_file, "w") as f:
        if content and isinstance(content, str):
            f.write(content)

        elif content and isinstance(content, dict):
            json.dump(content, f)

    return tmp_file
