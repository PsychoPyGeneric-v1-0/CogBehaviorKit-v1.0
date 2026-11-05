"""
Tutorial experiment: a Posner-style spatial-cueing detection task with a PERIPHERAL cue and catch trials,
following the logic of Posner (1980), Quarterly Journal of Experimental Psychology, 32, 3-25.

The design logic (valid / invalid / neutral cues, ~80% validity, catch trials, simple key-press detection)
comes from the paper. The NUMERIC values below (durations, sizes, trial counts) are ILLUSTRATIVE
PLACEHOLDERS: check them against the Methods section of the paper (see tutorials/02_*.md).
"""
ECC = 7.0
SIDES = ["left", "right"]
SOA = 0.15            # cue-target onset asynchrony in s (illustrative)
CONDITIONS = (
    [{"trial_type": "valid", "target_side": s, "n": 8} for s in SIDES] +
    [{"trial_type": "invalid", "target_side": s, "n": 2} for s in SIDES] +
    [{"trial_type": "neutral", "target_side": s, "n": 2} for s in SIDES] +
    [{"trial_type": "catch", "target_side": s, "n": 1} for s in SIDES]      # no target: do NOT respond
)


def derive(trial, rng):
    t, side = trial["trial_type"], trial["target_side"]
    cue_side = {"valid": side, "invalid": "right" if side == "left" else "left", "neutral": "both", "catch": side}[t]
    return {"cue_left.visible": cue_side in ("left", "both"),
            "cue_right.visible": cue_side in ("right", "both"),
            "target.visible": t != "catch",
            "target.pos": [-ECC if side == "left" else ECC, 0],
            "answer": "none" if t == "catch" else "detected"}


CONFIG = {
    "experiment": {"name": "posner_1980_tutorial",
                   "description": "Posner-style cueing, detection task with catch trials: press SPACE when a star "
                                  "appears in a box; do nothing on catch trials. NUMERIC SETTINGS ARE PLACEHOLDERS.",
                   "column_descriptions": {
                       "trial_type": "valid = cue on the target side; invalid = cue on the other side; "
                                     "neutral = both boxes cued; catch = no target (do not respond).",
                       "target_side": "Side where the target appeared (or would have appeared on catch trials).",
                       "cue_left.visible": "True = the left box was highlighted by the cue.",
                       "cue_right.visible": "True = the right box was highlighted by the cue.",
                       "target.visible": "False on catch trials (no target shown).",
                       "target.pos": "[x, y] position of the target in degrees.",
                       "answer": "'detected' when a target appeared, 'none' on catch trials.",
                   },
                   "instructions": ["Fixate the central cross.\nPress SPACE as soon as a star appears in a box.\n"
                                    "If nothing appears, do nothing.\n\nPress SPACE to begin."]},
    "screen": {"size": [1280, 720], "bg_color": [128, 128, 128], "color_space": "rgb255", "units": "deg"},
    "keys": {"responses": {"space": "detected"}},
    "design": {"conditions": CONDITIONS, "n_repeats": 2, "n_blocks": 2, "derive": derive,
               "summary_by": ["trial_type"]},
    "practice": {"n_trials": 6, "feedback": True},
    "scoring": {"answer_variable": "answer", "no_response_label": "none"},
    "stimuli": {
        "fixation": {"type": "text", "text": "+", "height": 1.0},
        "box_left": {"type": "square", "pos": [-ECC, 0], "size": 2.5, "fill_color": None, "line_color": "white", "line_width": 2},
        "box_right": {"type": "square", "pos": [ECC, 0], "size": 2.5, "fill_color": None, "line_color": "white", "line_width": 2},
        "cue_left": {"type": "square", "pos": [-ECC, 0], "size": 2.5, "fill_color": None, "line_color": "white", "line_width": 8},
        "cue_right": {"type": "square", "pos": [ECC, 0], "size": 2.5, "fill_color": None, "line_color": "white", "line_width": 8},
        "target": {"type": "text", "text": "*", "height": 1.5, "pos": [ECC, 0]},
    },
    "events": [
        {"name": "fixation", "stimuli": ["fixation", "box_left", "box_right"], "duration": [0.8, 1.5]},
        {"name": "cue", "stimuli": ["fixation", "box_left", "box_right", "cue_left", "cue_right"], "duration": 0.05},
        {"name": "gap", "stimuli": ["fixation", "box_left", "box_right"], "duration": SOA - 0.05},
        {"name": "target", "stimuli": ["fixation", "box_left", "box_right", "target"], "duration": 1.0,
         "response": True, "end_on_response": True},
        {"name": "iti", "stimuli": [], "duration": 0.5},
    ],
}
