import sys
from pathlib import Path

# make this checkout's src/ win over any other editable install of `ic`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
