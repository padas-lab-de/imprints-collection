import os
from pathlib import Path

# ic.config reads topics/categories.jsonl relative to the working directory at
# import time, so tests must run from the repository root.
os.chdir(Path(__file__).resolve().parents[1])
