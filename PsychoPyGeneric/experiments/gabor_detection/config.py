"""
GABOR DETECTION / DISCRIMINATION
================================
Change TASK below to switch between the two tasks:
  "discrimination": is the Gabor tilted LEFT or RIGHT of vertical?      (left / right arrow keys)
  "detection"     : was a Gabor shown at all?                           (Y = yes, N = no)

Trial: bullseye fixation -> (optional) ring cue -> Gabor (very brief) -> response screen -> blank.

HOW TO READ THIS FILE
  1. the settings you will most often change (top)   2. derive(): per-trial values   3. CONFIG
"""

# ---------------------------------------------------------------- 1. settings you will often change
TASK = "discrimination"       # "discrimination" or "detection"
USE_CUE = True                # True/False: show a ring around the place where the Gabor will appear
CONTRASTS = [0.02, 0.04, 0.08, 0.16, 0.32]    # contrast levels (0 = invisible, 1 = maximum)
TILT_DEG = 4.0                # discrimination: how far from vertical the Gabor is tilted (degrees)
ECCENTRICITY = 5.0            # distance of the Gabor left/right of the centre (degrees)
GABOR_DURATION = 0.10         # seconds the Gabor stays on screen (rounded to whole screen frames)

# The task decides which conditions exist, which keys are used and what the instructions say.
if TASK == "discrimination":
    FACTORS = {"gabor.contrast": CONTRASTS, "tilt": [-1, 1], "side": ["left", "right"]}
    KEYS = {"left": "left", "right": "right"}                     # the arrow keys
    INSTRUCTIONS = "Is the patch tilted LEFT or RIGHT of vertical?\n\nLEFT arrow / RIGHT arrow\n\nPress SPACE."
else:
    FACTORS = {"gabor.contrast": CONTRASTS, "gabor.visible": [True, False], "side": ["left", "right"]}
    KEYS = {"y": "yes", "n": "no"}
    INSTRUCTIONS = "Was a patch presented?\n\nY = yes     N = no\n\nPress SPACE."


# ---------------------------------------------------------------- 2. derive
def derive(trial, rng):
    """Called once per trial: computes positions, orientation and the correct answer."""
    x = -ECCENTRICITY if trial["side"] == "left" else ECCENTRICITY    # negative x = left of the centre
    out = {"gabor.pos": [x, 0], "cue.pos": [x, 0]}                    # Gabor and cue at the same place
    if TASK == "discrimination":
        out["gabor.ori"] = trial["tilt"] * TILT_DEG        # degrees; positive = clockwise = tilted RIGHT
        out["answer"] = "right" if trial["tilt"] > 0 else "left"
    else:
        out["gabor.ori"] = float(rng.choice([-45, 45]))    # random orientation (irrelevant for detection)
        out["answer"] = "yes" if trial["gabor.visible"] else "no"
    return out


# What happens in each trial. Built as a list: the cue events are added only if USE_CUE is True.
EVENTS = [{"name": "fixation", "stimuli": ["fixation"], "duration": [0.5, 1.0]}]
if USE_CUE:
    EVENTS += [{"name": "cue", "stimuli": ["fixation", "cue"], "duration": 0.10},
               {"name": "gap", "stimuli": ["fixation"], "duration": 0.05}]   # short blank between cue and Gabor
EVENTS += [
    {"name": "target", "stimuli": ["fixation", "gabor"], "duration": GABOR_DURATION},    # the brief flash
    {"name": "respond", "stimuli": ["fixation"], "duration": 2.0, "response": True},     # RT measured here
    {"name": "iti", "stimuli": [], "duration": 0.5},                                      # blank between trials
]

# ---------------------------------------------------------------- 3. the settings
CONFIG = {
    "experiment": {
        "name": f"gabor_{TASK}",
        "description": f"Gabor {TASK} at several contrast levels. The Gabor is shown briefly, then the "
                       "participant answers on a response screen (RT is counted from that screen).",
        "instructions": ["GABOR TASK\n\n" + INSTRUCTIONS],
        "output_dir": "data",
        "column_descriptions": {
            "gabor.contrast": "Contrast of the Gabor (0 = invisible, 1 = maximum).",
            "tilt": "Discrimination: -1 = tilted left, +1 = tilted right.",
            "side": "Side of the screen where the Gabor (and cue) appeared.",
            "gabor.pos": "[x, y] position of the Gabor in degrees from the centre (negative x = left).",
            "cue.pos": "[x, y] position of the ring cue (same as the Gabor).",
            "gabor.ori": "Orientation of the Gabor in degrees, clockwise from vertical.",
            "answer": "The correct response of this trial.",
        },
    },
    "screen": {"size": [1280, 720], "fullscreen": False, "bg_color": [128, 128, 128], "color_space": "rgb255",
               "units": "deg", "width_cm": 53.0, "distance_cm": 57.0},
    "keys": {"responses": KEYS},
    "design": {"factors": FACTORS, "n_repeats": 4, "n_blocks": 2, "derive": derive,
               "summary_by": ["gabor.contrast"]},
    "practice": {"n_trials": 8, "feedback": True},
    "scoring": {"answer_variable": "answer"},
    "stimuli": {
        # Bullseye fixation: 3 concentric rings alternating black / white
        "fixation": {"type": "bullseye", "radius": 0.3, "n_rings": 3, "colors": [[0, 0, 0], [255, 255, 255]]},
        # Ring cue. gap_side None = a closed circle (no gap). Try "left" or "right" for a ring with a gap.
        "cue": {"type": "gap_circle", "radius": 2.5, "gap_side": None, "line_width": 0, "color": "white"},
        # Gabor: sf = cycles per degree, size in degrees, "gauss" = soft circular edge.
        # contrast/pos/ori below are only defaults: every trial replaces them (see derive and FACTORS).
        "gabor": {"type": "gabor", "size": 10.0, "sf": 1.0, "phase": 0.0, "contrast": 0.2, "mask": "gauss"},
    },
    "events": EVENTS,
}
