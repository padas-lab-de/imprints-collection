import os
import sys
from pathlib import Path

# ic.config reads topics/categories.jsonl relative to the working directory at
# import time, so tests must run from the repository root.
os.chdir(Path(__file__).resolve().parents[1])

# make this checkout's src/ win over any other editable install of `ic`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
