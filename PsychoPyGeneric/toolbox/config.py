"""
config.py - SETTINGS: the default values, loading your config, and checking it for mistakes.
==========================================================================================
An experiment is described by ONE dictionary (called CONFIG) in experiments/<name>/config.py.
You only write what you want to CHANGE; everything else comes from DEFAULTS below.
DEFAULTS is also the complete list of every setting you can use, with its meaning.

    load_config(...)      reads your config and merges it with DEFAULTS
    validate_config(...)  stops with a clear message if something is wrong (typo, bad colour, ...)

This file does not need PsychoPy.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path


class ConfigError(ValueError):
    """Raised when the configuration is wrong. The message says what to fix."""


COLOR_SPACES = ("rgb", "rgb1", "rgb255", "hex", "named")
UNITS = ("deg", "pix", "cm", "norm", "height")

DEFAULTS = {
    "experiment": {
        "name": "experiment",
        "instructions": ["Welcome!\n\nPress SPACE to start."],
        "break_message": "Break.\n\nPress SPACE to continue.",
        "end_message": "Thank you!\n\nThe experiment is over.",
        "output_dir": "data",
        "seed": None,                 # integer -> reproducible trial order; None -> random
        "description": "",            # one or two sentences about the task, copied into the data README
        "column_descriptions": {},    # {"cue_type": "valid = arrow points at target, ..."} explains YOUR columns
    },
    "screen": {
        "size": [1280, 720],          # pixels (use your real resolution when fullscreen)
        "fullscreen": False,
        "screen_index": 0,
        "bg_color": [128, 128, 128],  # interpreted in `color_space`
        "color_space": "rgb255",      # "rgb255" (0..255), "rgb" (-1..1), "rgb1" (0..1), "hex", "named"
        "units": "deg",               # "deg" needs width_cm and distance_cm below
        "width_cm": 53.0,             # physical screen width
        "distance_cm": 57.0,          # eye-to-screen distance
        "frame_rate": 60.0,           # used only if the frame rate cannot be measured
        "measure_frame_rate": True,
        "hide_mouse": True,
        "text_color": "white",
        "text_height": None,          # None -> sensible default for the chosen units
    },
    "participant": {
        "ask": True,
        "use_dialog": True,           # False -> ask in the terminal instead
        "fields": {"participant": "", "session": "1", "age": "", "gender": ""},
    },
    "keys": {
        "responses": {},              # {"f": "left", "j": "right"}: key name -> response label
        "escape": "escape",           # abort key (data collected so far are kept)
    },
    "design": {
        "factors": {},                # {"cue": ["valid", "invalid"], "side": ["left", "right"]}
        "conditions": None,           # OR an explicit list: [{"cue": "valid", "n": 3}, ...]
        "n_repeats": 1,               # repetitions of every condition PER BLOCK
        "n_blocks": 1,
        "randomization": "shuffle",   # "shuffle" or "sequential"
        "max_run": None,              # {"variable": "cue", "n": 3} -> no more than 3 identical in a row
        "derive": None,               # function(trial, rng) -> dict of extra trial variables
        "summary_by": [],             # variables used for the summary printed at the end
    },
    "practice": {
        "n_trials": 0,
        "feedback": True,
        "feedback_duration": 0.5,
        "message": "Practice.\n\nPress SPACE to start.",
        "main_message": "Practice finished.\n\nThe real experiment starts now.\n\nPress SPACE.",
    },
    "scoring": {
        "answer_variable": None,      # trial variable holding the correct response label
        "no_response_label": None,    # label assigned when the participant does not respond
    },
    "test_mode": {"n_trials": 6, "n_practice": 0, "windowed": True},
    "stimuli": {},                    # {"name": {"type": "gabor", ...}}
    "events": [],                     # ordered list of what happens in each trial
}

_FIXED_SECTIONS = ("experiment", "screen", "participant", "keys", "design",
                   "practice", "scoring", "test_mode")
_EVENT_KEYS = {"name", "stimuli", "duration", "response", "end_on_response"}


def merge(base, override):
    """Return a deep copy of `base` updated with `override` (dicts merge, everything else replaces)."""
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(source):
    """`source` may be a dict, a path to a .json file, or a path to a .py file defining CONFIG."""
    if isinstance(source, dict):
        user = source
    else:
        path = Path(source)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        if path.suffix == ".json":
            with open(path, encoding="utf-8") as fh:
                user = json.load(fh)
        elif path.suffix == ".py":
            spec = importlib.util.spec_from_file_location("user_config", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "CONFIG"):
                raise ConfigError(f"{path} must define a dictionary called CONFIG")
            user = module.CONFIG
        else:
            raise ConfigError("Config files must be .json or .py")
    unknown = set(user) - set(DEFAULTS)
    if unknown:
        raise ConfigError(f"Unknown config section(s): {sorted(unknown)}. Valid: {sorted(DEFAULTS)}")
    for section in _FIXED_SECTIONS:
        bad = set(user.get(section, {})) - set(DEFAULTS[section])
        if bad:
            raise ConfigError(f"Unknown key(s) in '{section}': {sorted(bad)}. Valid: {sorted(DEFAULTS[section])}")
    return merge(DEFAULTS, user)


def _check(condition, message):
    if not condition:
        raise ConfigError(message)


def check_color(value, space, where):
    """Check a colour against the colour space (a common source of silent mistakes)."""
    if value is None or isinstance(value, str):
        return
    ranges = {"rgb255": (0, 255), "rgb": (-1, 1), "rgb1": (0, 1)}
    _check(isinstance(value, (list, tuple)) and len(value) == 3,
           f"{where}: colour must be a name, hex string or 3 numbers, got {value!r}")
    if space in ranges:
        lo, hi = ranges[space]
        _check(all(isinstance(v, (int, float)) and lo <= v <= hi for v in value),
               f"{where}: {value} is outside the {space} range [{lo}, {hi}]")


def pixels_per_degree(cfg):
    """Pixels per degree of visual angle at screen centre (small-angle geometry)."""
    s = cfg["screen"]
    px_per_cm = s["size"][0] / s["width_cm"]
    return px_per_cm * 2 * s["distance_cm"] * math.tan(math.radians(0.5))


def _check_screen(cfg):
    s = cfg["screen"]
    _check(s["color_space"] in COLOR_SPACES, f"screen.color_space must be one of {COLOR_SPACES}")
    _check(s["units"] in UNITS, f"screen.units must be one of {UNITS}")
    _check(len(s["size"]) == 2 and all(v > 0 for v in s["size"]), "screen.size must be [width, height] in pixels")
    _check(s["width_cm"] > 0 and s["distance_cm"] > 0, "screen.width_cm and screen.distance_cm must be > 0")
    check_color(s["bg_color"], s["color_space"], "screen.bg_color")


def _check_design(cfg):
    d = cfg["design"]
    _check(d["randomization"] in ("shuffle", "sequential"), "design.randomization must be 'shuffle' or 'sequential'")
    _check(int(d["n_repeats"]) >= 1 and int(d["n_blocks"]) >= 1, "design.n_repeats and design.n_blocks must be >= 1")
    for name, levels in d["factors"].items():
        _check(isinstance(levels, (list, tuple)) and len(levels) > 0,
               f"design.factors['{name}'] must be a non-empty list, e.g. [\"left\", \"right\"]")
    _check(d["derive"] is None or callable(d["derive"]), "design.derive must be a function (or None)")
    if d["max_run"]:
        _check({"variable", "n"} <= set(d["max_run"]), "design.max_run needs 'variable' and 'n'")


def _check_stimuli(cfg, known_types):
    for name, spec in cfg["stimuli"].items():
        _check("." not in name, f"Stimulus name '{name}' must not contain a dot")
        _check(isinstance(spec, dict) and "type" in spec, f"stimuli['{name}'] needs a 'type'")
        if known_types is not None:
            _check(spec["type"] in known_types,
                   f"stimuli['{name}']: unknown type '{spec['type']}'. Available: {sorted(known_types)}")
        for key in ("color", "fill_color", "line_color"):
            check_color(spec.get(key), cfg["screen"]["color_space"], f"stimuli['{name}'].{key}")


def _check_events(cfg):
    _check(cfg["events"], "'events' is empty: define at least one event")
    names_seen, n_response_events = set(), 0
    for i, event in enumerate(cfg["events"]):
        where = f"events[{i}]"
        _check(isinstance(event, dict) and "name" in event, f"{where} needs a 'name'")
        _check(set(event) <= _EVENT_KEYS,
               f"{where}: unknown key(s) {sorted(set(event) - _EVENT_KEYS)}. Valid: {sorted(_EVENT_KEYS)}")
        _check(event["name"] not in names_seen, f"{where}: duplicate event name '{event['name']}'")
        names_seen.add(event["name"])
        for stim in event.get("stimuli", []):
            _check(stim in cfg["stimuli"], f"{where}: stimulus '{stim}' is not defined in 'stimuli'")

        duration = event.get("duration")
        if isinstance(duration, (list, tuple)):
            _check(len(duration) == 2 and 0 <= duration[0] <= duration[1],
                   f"{where}: a duration range must be [min, max] with min <= max")
        else:
            _check(duration is None or duration >= 0, f"{where}: duration must be >= 0 (or None)")
        _check(duration is not None or event.get("response"),
               f"{where}: duration None (wait forever) is only allowed for a response event")
        n_response_events += bool(event.get("response"))

    _check(n_response_events <= 1, "Only ONE event per trial can collect a response")
    _check(n_response_events == 0 or cfg["keys"]["responses"],
           "An event collects a response but keys.responses is empty")


def validate_config(cfg, known_types=None):
    """Check a merged config. Raises ConfigError with a readable message if something is wrong."""
    _check_screen(cfg)
    _check_design(cfg)
    _check_stimuli(cfg, known_types)
    _check_events(cfg)
    return cfg
