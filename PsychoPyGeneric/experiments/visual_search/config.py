"""
VISUAL SEARCH
=============
Is a RED CIRCLE present among other shapes?   F = present, J = absent.

  feature search     : red circle among GREEN circles                 (colour alone finds the target)
  conjunction search : red circle among RED squares + GREEN circles   (colour AND shape are needed)

HOW TO READ THIS FILE
  1. constants (colours, targets)    2. derive(): computes values for each trial    3. CONFIG: the settings
Everything is configuration: change numbers, colours, keys, set sizes... no other code to touch.
"""

# ---------------------------------------------------------------- 1. constants
# Colours are [red, green, blue], each 0-255, because screen.color_space is "rgb255" below.
RED, GREEN = [230, 40, 40], [40, 170, 60]

TARGET = {"type": "circle", "fill_color": RED}
DISTRACTORS = {
    "feature":     [{"type": "circle", "fill_color": GREEN}],
    "conjunction": [{"type": "square", "fill_color": RED},
                    {"type": "circle", "fill_color": GREEN}],
}


# ---------------------------------------------------------------- 2. derive
def derive(trial, rng):
    """Called once per trial. `trial` holds that trial's conditions, e.g.
    {"search_type": "feature", "search.n_items": 8, "search.target_present": True}.
    We return extra values. A name like "search.target" means:
    'set the parameter "target" of the stimulus called "search"' (see CONFIG -> stimuli)."""
    return {
        "search.target": TARGET,
        "search.distractors": DISTRACTORS[trial["search_type"]],
        "answer": "present" if trial["search.target_present"] else "absent",   # the correct response
    }


# ---------------------------------------------------------------- 3. the settings
CONFIG = {
    "experiment": {
        "name": "visual_search",
        "description": "Visual search: report whether a red circle is present among distractors "
                       "(feature vs conjunction search, 4/8/16 items).",
        "instructions": [
            "VISUAL SEARCH\n\nA set of coloured shapes will appear.\n\n"
            "Is there a RED CIRCLE?\n  F = present     J = absent\n\n"
            "Respond as fast and as accurately as you can.\n\nPress SPACE.",
        ],
        "output_dir": "data",
        "seed": None,                      # e.g. 42 -> same trial order every run
        # Explanations of the columns that are specific to this experiment (written in the data README):
        "column_descriptions": {
            "search_type": "feature = red circle among green circles; conjunction = red circle among "
                           "red squares and green circles.",
            "search.n_items": "Number of shapes on the screen (set size).",
            "search.target_present": "True = the red circle was on the screen, False = it was not.",
            "answer": "The correct response: 'present' (key F) or 'absent' (key J).",
            "search_n_items": "Same as search.n_items (written by the stimulus itself, a duplicate).",
            "search_target_present": "Same as search.target_present (a duplicate).",
            "search_target_pos": "[x, y] position of the red circle in degrees from the screen centre "
                                 "(empty when absent).",
        },
    },

    "screen": {"size": [1280, 720], "fullscreen": False, "bg_color": [128, 128, 128], "color_space": "rgb255",
               "units": "deg", "width_cm": 53.0, "distance_cm": 57.0},

    # Pressing key "f" gives the response label "present"; "j" gives "absent".
    "keys": {"responses": {"f": "present", "j": "absent"}},

    "design": {
        # Every combination of these levels: 2 x 3 x 2 = 12 conditions.
        "factors": {"search_type": ["feature", "conjunction"],
                    "search.n_items": [4, 8, 16],
                    "search.target_present": [True, False]},
        "n_repeats": 5,            # each condition 5 times PER BLOCK -> 60 trials per block
        "n_blocks": 2,             # 2 blocks -> 120 trials in total
        "randomization": "shuffle",
        "derive": derive,          # run the function above for every trial
        "summary_by": ["search_type", "search.n_items", "search.target_present"],   # table printed at the end
    },

    "practice": {"n_trials": 8, "feedback": True},      # 8 practice trials with "Correct!/Wrong"
    "scoring": {"answer_variable": "answer"},           # correct = the key's label equals trial["answer"]

    # What CAN appear on screen (each has a name and a type). Which ones appear when: see "events".
    "stimuli": {
        "fixation": {"type": "text", "text": "+", "height": 1.0, "color": "white"},
        "search":   {"type": "search_array", "layout": "grid", "grid_shape": [4, 4],
                     "spacing": 2.5, "item_size": 1.2, "jitter": 0.25},
    },

    # What happens in EVERY trial, in order. Durations are in seconds.
    "events": [
        {"name": "fixation", "stimuli": ["fixation"], "duration": [0.5, 0.8]},   # random time between 0.5 and 0.8 s
        {"name": "search", "stimuli": ["search"], "duration": 5.0,
         "response": True},         # waits for a key press; 5.0 s = time limit. RT is measured here
        {"name": "iti", "stimuli": [], "duration": 0.5},                         # blank screen between trials
    ],
}
