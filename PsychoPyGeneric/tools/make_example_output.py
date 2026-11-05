"""
Regenerates example_output/ WITHOUT a screen or a person: it runs the real toolbox pipeline against a
stand-in 'psychopy' whose keyboard answers randomly. Columns/format are authentic; the VALUES
(RTs, accuracy, measured durations) are meaningless. Usage:
    PYTHONPATH=<folder containing a fake 'psychopy' package> python tools/make_example_output.py
Real data come from:  python run_experiment.py <experiment>
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from toolbox.config import load_config            # noqa: E402
from toolbox.experiment import Experiment         # noqa: E402

for name in ["visual_search", "gabor_detection", "arrow_cue"]:
    cfg = load_config(ROOT / "experiments" / name / "config.py")
    cfg["experiment"]["output_dir"] = str(ROOT / "example_output")
    cfg["participant"]["ask"] = False
    Experiment(cfg, seed=123).run(participant_id="S01")
