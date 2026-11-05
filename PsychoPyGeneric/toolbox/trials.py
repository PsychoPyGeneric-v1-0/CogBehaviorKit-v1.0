"""
trials.py - BUILDING THE LIST OF TRIALS
=======================================
A TRIAL is a plain dictionary of variables, for example
        {"cue_type": "valid", "target_side": "left"}

Where do trials come from?  From config["design"], in one of two ways:

  A) FACTORS: every combination of the levels is created.
        "factors": {"cue_type": ["valid", "invalid"], "side": ["left", "right"]}
        -> 2 x 2 = 4 conditions: (valid,left) (valid,right) (invalid,left) (invalid,right)

  B) CONDITIONS: you write the list yourself; "n" says how many times each one appears.
        "conditions": [{"cue_type": "valid", "n": 3}, {"cue_type": "invalid", "n": 1}]
        -> valid appears 3 times as often as invalid (75% / 25%)

Then:  repeated n_repeats times -> derive() adds computed variables -> shuffled (with the seed) -> blocks.
Note: n_repeats is PER BLOCK, so total trials = conditions x n_repeats x n_blocks.

This file does not need PsychoPy.
"""
import itertools

from .config import ConfigError


def base_conditions(design):
    """The list of distinct conditions, before any repetition (see A and B above)."""
    if design["conditions"]:                                   # way B: explicit list
        conditions = []
        for entry in design["conditions"]:
            entry = dict(entry)
            how_many = int(entry.pop("n", 1))                  # "n" is a count, not a variable
            conditions += [dict(entry) for _ in range(how_many)]
        return conditions

    factors = design["factors"]                                # way A: all combinations
    if not factors:
        return [{}]
    names = list(factors)
    return [dict(zip(names, levels)) for levels in itertools.product(*factors.values())]


def _longest_run(trials, variable):
    """Longest streak of identical values of `variable` (used for the max_run rule)."""
    longest = current = 0
    previous = object()                                        # something equal to nothing
    for trial in trials:
        current = current + 1 if trial.get(variable) == previous else 1
        previous = trial.get(variable)
        longest = max(longest, current)
    return longest


def _order(trials, design, rng):
    """Shuffle the trials (unless 'sequential'). With max_run, shuffle again until the rule is respected."""
    if design["randomization"] == "sequential":
        return trials
    rule = design["max_run"]
    for _ in range(2000):
        shuffled = [trials[i] for i in rng.permutation(len(trials))]
        if not rule or _longest_run(shuffled, rule["variable"]) <= rule["n"]:
            return shuffled
    raise ConfigError("Could not satisfy design.max_run. Relax the rule (larger n).")


def _add_derived_variables(trials, design, rng):
    """Call your derive(trial, rng) function for every trial and add the variables it returns."""
    function = design["derive"]
    if function:
        for trial in trials:
            trial.update(function(trial, rng) or {})
    return trials


def make_blocks(design, rng):
    """Returns a list of blocks; each block is a list of trials (all conditions x n_repeats, shuffled)."""
    conditions = base_conditions(design)
    blocks = []
    for _ in range(int(design["n_blocks"])):
        trials = [dict(c) for _ in range(int(design["n_repeats"])) for c in conditions]
        trials = _add_derived_variables(trials, design, rng)
        blocks.append(_order(trials, design, rng))
    return blocks


def make_practice(design, n, rng):
    """`n` practice trials, picked at random from the conditions."""
    if n <= 0:
        return []
    conditions = base_conditions(design)
    picks = rng.choice(len(conditions), size=n, replace=n > len(conditions))
    return _add_derived_variables([dict(conditions[i]) for i in picks], design, rng)


def flatten(blocks):
    """[[a, b], [c]] -> [a, b, c]"""
    return [trial for block in blocks for trial in block]
