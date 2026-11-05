#!/usr/bin/env python
"""
Launcher.   Examples
    python run_experiment.py --list
    python run_experiment.py visual_search --test                 # 6 trials, data go to data/test/
    python run_experiment.py visual_search --participant 01 --seed 42
    python run_experiment.py gabor_detection --check timing       # display | timing | keyboard | preview | all
    python run_experiment.py my_task --config path/to/config.json
"""
import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a PsychoPyGeneric experiment")
    ap.add_argument("experiment", nargs="?", help="folder name inside experiments/")
    ap.add_argument("--list", action="store_true", help="list available experiments")
    ap.add_argument("--test", action="store_true", help="test mode: few trials, windowed, data in <output_dir>/test")
    ap.add_argument("--participant", help="participant ID (skips the dialog)")
    ap.add_argument("--seed", type=int, help="random seed for reproducible trial order")
    ap.add_argument("--config", help="use this .py/.json config instead of experiments/<name>/config.py")
    ap.add_argument("--check", choices=["display", "timing", "keyboard", "preview", "all"])
    a = ap.parse_args(argv)

    if a.list or not a.experiment:
        names = sorted(p.parent.name for p in (ROOT / "experiments").glob("*/config.py"))
        print("Available experiments:", ", ".join(names))
        return

    folder = ROOT / "experiments" / a.experiment
    config = a.config or folder / "config.py"
    if (folder / "custom_stimuli.py").exists():                   # user-defined stimuli are auto-loaded
        importlib.import_module(f"experiments.{a.experiment}.custom_stimuli")
    from toolbox import testing
    from toolbox.config import ConfigError
    from toolbox.experiment import Experiment
    Task = Experiment
    if (folder / "task.py").exists():                             # optional custom subclass called Task
        Task = importlib.import_module(f"experiments.{a.experiment}.task").Task
    try:
        if a.check:
            {"display": testing.check_display, "timing": testing.check_timing, "keyboard": testing.check_keyboard,
             "preview": testing.preview_stimuli, "all": testing.run_all}[a.check](config)
        else:
            Task(config, test_mode=a.test, seed=a.seed).run(participant_id=a.participant)
    except ConfigError as err:
        sys.exit(f"CONFIG ERROR: {err}")


if __name__ == "__main__":
    main()
