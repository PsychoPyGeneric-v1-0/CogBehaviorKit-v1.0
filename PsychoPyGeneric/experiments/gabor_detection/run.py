"""Run this experiment:  python experiments/<name>/run.py [--test] [--participant ID]"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from run_experiment import main  # noqa: E402

if __name__ == "__main__":
    main([Path(__file__).resolve().parent.name] + sys.argv[1:])
