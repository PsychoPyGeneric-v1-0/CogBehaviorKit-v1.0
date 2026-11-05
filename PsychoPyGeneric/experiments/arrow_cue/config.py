"""
ARROW CUE / SPATIAL ATTENTION  (Posner-style)
=============================================
Fixation + two placeholder boxes -> arrow cue -> short gap -> target in one of the boxes.
  valid   : the arrow points to the side where the target appears
  invalid : the arrow points to the OPPOSITE side
  neutral : double-headed arrow (no information)
Task: which shape is the target?   F = circle, J = square.
The summary printed at the end compares RT for valid / invalid / neutral cues.

HOW TO READ THIS FILE
  1. constants and the list of conditions   2. derive(): per-trial values   3. CONFIG
"""

# ---------------------------------------------------------------- 1. constants and conditions
ECC = 6.0                                               # target distance from the centre (degrees)
CUE_COUNTS = {"valid": 3, "invalid": 1, "neutral": 1}   # how often each cue type -> 60% / 20% / 20%
SIDES, SHAPES = ["left", "right"], ["circle", "square"]

# The list of conditions: every cue type x target side x target shape. "n" = how many times it appears
# (taken from CUE_COUNTS), which is how valid trials become more frequent than invalid ones.
CONDITIONS = [{"cue_type": cue, "target_side": side, "target_shape": shape, "n": n}
              for cue, n in CUE_COUNTS.items() for side in SIDES for shape in SHAPES]


# ---------------------------------------------------------------- 2. derive
def derive(trial, rng):
    """Called once per trial: decides where the arrow points and where the target appears."""
    side, cue = trial["target_side"], trial["cue_type"]
    other_side = "right" if side == "left" else "left"
    direction = {"valid": side,              # points at the target
                 "invalid": other_side,      # points the wrong way
                 "neutral": "both"}[cue]     # double-headed arrow
    return {"cue.direction": direction,
            "target.pos": [-ECC if side == "left" else ECC, 0],
            "target.type": trial["target_shape"],       # the target becomes a circle or a square
            "answer": trial["target_shape"]}            # the correct response = the shape shown


# ---------------------------------------------------------------- 3. the settings
CONFIG = {
    "experiment": {
        "name": "arrow_cue",
        "description": "Spatial attention: a central arrow predicts (valid), misleads (invalid) or says nothing "
                       "(neutral) about the side of the target. The participant names the target's shape. "
                       "RT is counted from the target onset, 0.3 s after the cue starts (0.2 s cue + 0.1 s gap).",
        "instructions": ["ATTENTION TASK\n\nKeep your eyes on the centre.\n"
                         "An arrow will appear, then a shape in one of the boxes.\n\n"
                         "F = circle     J = square\n\nThe arrow is usually right, but not always.\n"
                         "Be fast and accurate.\n\nPress SPACE."],
        "column_descriptions": {
            "cue_type": "valid = the arrow pointed at the target side; invalid = it pointed to the other side; "
                        "neutral = double-headed arrow.",
            "target_side": "Side of the screen where the target appeared.",
            "target_shape": "Shape of the target: circle or square.",
            "cue.direction": "Direction the arrow really pointed: left, right, or both (neutral).",
            "target.pos": "[x, y] position of the target in degrees from the centre (negative x = left).",
            "target.type": "Shape type used for the target (same as target_shape).",
            "answer": "The correct response of this trial (= the target shape).",
        },
    },
    "screen": {"size": [1280, 720], "fullscreen": True, "bg_color": [128, 128, 128], "color_space": "rgb255",
               "units": "deg", "width_cm": 53.0, "distance_cm": 57.0},
    "keys": {"responses": {"f": "circle", "j": "square"}},
    "design": {"conditions": CONDITIONS, "n_repeats": 4, "n_blocks": 2, "derive": derive,
               "max_run": {"variable": "cue_type", "n": 4},    # never more than 4 identical cue types in a row
               "summary_by": ["cue_type"]},                    # end-of-run table: accuracy and RT per cue type
    "practice": {"n_trials": 10, "feedback": True},
    "scoring": {"answer_variable": "answer"},
    "stimuli": {
        "fixation": {"type": "bullseye", "radius": 0.3, "n_rings": 3, "colors": [[0, 0, 0], [255, 255, 255]]},
        # Two empty boxes (fill_color None = no fill) marking where the target can appear
        "box_left":  {"type": "square", "pos": [-ECC, 0], "size": 2.5, "fill_color": None,
                      "line_color": "white", "line_width": 3},
        "box_right": {"type": "square", "pos": [ECC, 0], "size": 2.5, "fill_color": None,
                      "line_color": "white", "line_width": 3},
        # direction and pos below are only defaults: derive() replaces them on every trial
        "cue":    {"type": "arrow", "pos": [0, 1.2], "size": 1.6, "direction": "right", "fill_color": "white"},
        "target": {"type": "circle", "pos": [ECC, 0], "size": 1.0, "fill_color": [255, 255, 255]},
    },
    # The fixation and boxes are listed in every event so they stay on screen without flickering.
    "events": [
        {"name": "fixation", "stimuli": ["fixation", "box_left", "box_right"], "duration": [0.6, 1.0]},
        {"name": "cue",      "stimuli": ["fixation", "box_left", "box_right", "cue"], "duration": 0.2},
        {"name": "gap",      "stimuli": ["fixation", "box_left", "box_right"], "duration": 0.1},   # cue-to-target gap
        {"name": "target",   "stimuli": ["fixation", "box_left", "box_right", "target"],
         "duration": 1.5, "response": True},       # waits for a key (max 1.5 s); RT is measured here
        {"name": "iti",      "stimuli": [], "duration": 0.5},
    ],
}
