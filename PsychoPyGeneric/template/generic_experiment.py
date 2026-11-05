"""
GENERIC EXPERIMENT TEMPLATE
===========================
1. Copy this file (or the whole folder) and rename it.
2. Edit CONFIG below, from top to bottom.
3. Test:  python my_experiment.py --test      Run:  python my_experiment.py

This template is a minimal, working skeleton: fixation -> target square left/right -> key press.
It contains NO experiment-specific logic; every section is documented in README.md.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # lets Python find the 'toolbox' folder
from toolbox.experiment import Experiment                          # noqa: E402

# ---------------------------------------------------------------- 1. TRIAL VARIABLES
def derive(trial, rng):
    """Compute extra trial variables from the design (optional). Return a dict.
    'name.param' keys change a stimulus parameter for this trial only (here: target position)."""
    x = -5 if trial["side"] == "left" else 5
    return {"target.pos": [x, 0], "answer": trial["side"]}


CONFIG = {
    # ------------------------------------------------------------ 2. EXPERIMENT
    "experiment": {"name": "my_experiment", "output_dir": "data", "seed": None,
                   "description": "Describe your task here in one or two sentences (copied into the data README).",
                   # Explain your OWN columns here: they appear in the _README.txt saved next to every CSV
                   "column_descriptions": {"side": "Side of the screen where the target appeared.",
                                           "answer": "The correct response of this trial.",
                                           "target.pos": "[x, y] position of the target in degrees."},
                   "instructions": ["Press F if the square is on the left, J if it is on the right.\n\nPress SPACE."]},
    # ------------------------------------------------------------ 3. SCREEN (colours follow color_space)
    "screen": {"size": [1280, 720], "fullscreen": False, "bg_color": [128, 128, 128], "color_space": "rgb255",
               "units": "deg", "width_cm": 53.0, "distance_cm": 57.0},
    # ------------------------------------------------------------ 4. KEYS: key -> response label
    "keys": {"responses": {"f": "left", "j": "right"}},
    # ------------------------------------------------------------ 5. DESIGN
    "design": {"factors": {"side": ["left", "right"]}, "n_repeats": 10, "n_blocks": 1,
               "randomization": "shuffle", "derive": derive, "summary_by": ["side"]},
    "practice": {"n_trials": 4, "feedback": True},
    "scoring": {"answer_variable": "answer"},
    # ------------------------------------------------------------ 6. STIMULI (see toolbox/stimuli.py)
    "stimuli": {
        "fixation": {"type": "text", "text": "+", "height": 1.0},
        "target": {"type": "square", "size": 1.5, "fill_color": [255, 255, 255]},
    },
    # ------------------------------------------------------------ 7. EVENTS: what happens in each trial
    "events": [
        {"name": "fixation", "stimuli": ["fixation"], "duration": [0.5, 1.0]},        # [min, max] = jittered
        {"name": "target", "stimuli": ["fixation", "target"], "duration": 2.0, "response": True},
        {"name": "iti", "stimuli": [], "duration": 0.5},
    ],
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--participant")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    Experiment(CONFIG, test_mode=a.test, seed=a.seed).run(participant_id=a.participant)
