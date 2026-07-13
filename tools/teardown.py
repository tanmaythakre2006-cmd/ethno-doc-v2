import os
import shutil
from pathlib import Path

def teardown():
    dirs_to_recreate = [
        "frontend",
        "backend",
        "tools",
        "tests",
        ".system",
        "docker",
        "corpus_vault"
    ]

    base_dir = Path(__file__).resolve().parent.parent

    for d in dirs_to_recreate:
        dir_path = base_dir / d
        if dir_path.exists():
            shutil.rmtree(dir_path)

        # Immediate recreation
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Recreated pristine directory: {d}")

if __name__ == "__main__":
    teardown()
