# PsychoPyGeneric

A small, configuration-driven toolbox for **visual behavioral experiments** with PsychoPy. You describe an
experiment in one Python dictionary (screen, stimuli, trial events, design, keys); the toolbox runs it,
times it in screen frames, records RTs and saves the data safely. No GUI, no need to rewrite code.

## What is included
| Part | Where |
|---|---|
| Generic experiment template | `template/generic_experiment.py` |
| Stimulus library (Gabor, bullseye, ring/gap cues, shapes, lines, arrows, text, visual-search arrays) | `toolbox/stimuli.py` |
| Engine: window, timing, responses, practice/blocks/feedback | `toolbox/experiment.py` |
| Config defaults, loading, validation | `toolbox/config.py` |
| Trial generation and randomization (seeded) | `toolbox/trials.py` |
| Safe data saving + summary | `toolbox/data.py` |
| Display/timing/keyboard/stimulus checks | `toolbox/testing.py` |
| 3 examples: visual search, Gabor detection/discrimination, arrow-cue spatial attention | `experiments/` |
| Tutorials | `tutorials/` (from scratch; from a published paper) |
| Example output files | `example_output/` |

## What each file does

The project has three layers: **recipes** (`experiments/*/config.py`) describe an experiment, the **toolbox**
(`toolbox/*.py`) does the work, and a few **helpers** make it easy to start and learn. Normally you only edit recipes.

### Top level
| File | Role |
|---|---|
| `run_experiment.py` | The launcher. Give it an experiment name (`arrow_cue`) and it loads that experiment's config and starts it. Handles `--test`, `--participant`, `--seed`, `--config` and `--check`. |
| `README.md` | This manual. |
| `requirements.txt` | Python packages needed (PsychoPy, numpy). Not needed if you use the PsychoPy app. |

### `toolbox/` (the engine; you do not edit these)
| File | Role |
|---|---|
| `config.py` | Default settings (screen, keys, timing...), loading of your config (.py or .json), and checking for mistakes (typos, colours out of range, unknown stimuli). Produces the `CONFIG ERROR` messages. |
| `stimuli.py` | The stimulus library. Each stimulus (`gabor`, `bullseye`, `gap_circle`, `circle`, `square`, `arrow`, `text`, `search_array`...) is a small function registered under a name; a config creates it with `"type": "<name>"`. New stimuli are added by registering a new function. |
| `trials.py` | Builds the list of trials: crosses the factors (or uses an explicit condition list), repeats, shuffles with the seed, splits into blocks, applies `max_run`. Does not use PsychoPy. |
| `experiment.py` | The main engine. Opens the window, asks for the participant ID, shows instructions, runs each trial's events frame by frame, measures reaction times, scores answers, shows practice feedback and handles the Esc key. Read this to understand how an experiment actually runs. |
| `data.py` | Saves data: creates the CSV, writes one row per trial, never overwrites files, keeps test and real data apart, writes the `.json` metadata, writes the **`_README.txt` that explains every column**, and prints the end-of-run summary. |
| `testing.py` | The `--check` tools: display, timing, keyboard and stimulus preview. |
| `__init__.py` | Marks `toolbox` as a Python package so it can be imported. Leave it alone. |

### `experiments/` (the recipes)
Each experiment folder (`visual_search/`, `gabor_detection/`, `arrow_cue/`, `posner_1980_tutorial/`) holds the same two files:

| File | Role |
|---|---|
| `config.py` | The description of the experiment: screen, stimuli, events, design, keys. **This is the file you edit.** It does nothing when run by itself. |
| `run.py` | A tiny start button. It calls the launcher with its folder's name, so you can start the experiment from the Run button of the PsychoPy Coder (or `python experiments/<name>/run.py`). You never edit it. |

Optional extra files in an experiment folder: `custom_stimuli.py` (your own stimuli, loaded automatically) and
`task.py` (a `Task` class for custom trial logic).

### Other folders
| File | Role |
|---|---|
| `template/generic_experiment.py` | The empty starting point for a new experiment: a minimal working experiment with its config and start code in one file. Copy it and modify it. |
| `tutorials/01_build_from_scratch.md` | Step-by-step guide to building a new experiment, including a custom stimulus. |
| `tutorials/02_from_paper_to_code.md` | How to turn a published paper's Methods into a config (Posner, 1980). |
| `example_output/` | Sample CSV/JSON files showing the data format. Values are dummy (made by a fake participant). |
| `tools/make_example_output.py` | The script that generated those samples. Not needed for normal use. |

### Created when you run
| Item | Role |
|---|---|
| `data/` | Your CSV, column-guide (`_README.txt`) and JSON files (`data/<experiment>/`; test runs in `data/test/`). |
| `__pycache__/` | Created automatically by Python to start faster. Ignore or delete. |

### What to touch and what not to touch

| Safe to edit (this is what you are meant to change) | Leave alone (unless you know what you are doing) |
|---|---|
| `experiments/<name>/config.py`: stimuli, colours, keys, timing, conditions, number of trials, screen settings | `toolbox/` (all files): the engine. A small edit can break every experiment at once |
| A **copy** of `template/generic_experiment.py` for a new experiment | `run_experiment.py`, the launcher |
| `experiments/<name>/custom_stimuli.py`: your own new stimuli (you create this file) | `experiments/<name>/run.py`: the start button, nothing to change in it |
| `experiments/<name>/task.py`: custom trial logic (advanced, optional, you create it) | `__init__.py` files and `__pycache__/` folders |
| Your data in `data/`: copy files elsewhere to analyse them | `example_output/` and `tools/`: samples only |

Rules of thumb:
- **Keep a backup copy** of a working `config.py` before experimenting (for example `config_backup.py`).
- **Do not edit the original template.** Copy it first, and edit the copy.
- **Do not edit data files while an experiment is running.** Excel can lock a CSV and block saving.
- **Do not rename or move the `toolbox` folder.** Experiments look for it by that name and location.
- Keep the **quotes, commas, brackets and colons** in a config exactly as they are. Only change the values. If you get a `SyntaxError`, a comma or bracket is usually missing.
- Change **one thing at a time**, then run with `--test` to check.
- If something breaks, restore your backup, or re-extract the original zip into a fresh folder.

### What happens when you press Run on `experiments/arrow_cue/run.py`
1. `run.py` calls `run_experiment.py` with the name `arrow_cue`.
2. The launcher loads `experiments/arrow_cue/config.py`.
3. `toolbox/config.py` merges it with the defaults and checks it.
4. `toolbox/trials.py` builds the list of trials.
5. `toolbox/experiment.py` opens the window and runs each trial, using `toolbox/stimuli.py` to create the shapes.
6. `toolbox/data.py` saves each trial to the CSV as it goes.

To change an experiment you only touch step 2, its `config.py`.

## Install
1. Install **PsychoPy** (https://www.psychopy.org/download.html). Either the standalone app, or in a fresh
   virtual environment: `pip install psychopy`. Use the Python version your PsychoPy release supports
   (see the PsychoPy docs; PsychoPy is picky about Python versions).
2. Download this folder. No other dependencies (`numpy` comes with PsychoPy).
3. Run from the project folder with the same Python that has PsychoPy (in the standalone app use its Coder).

## Run
```
python run_experiment.py --list
python run_experiment.py visual_search --test                    # a few trials, windowed, data in data/test/
python run_experiment.py visual_search --participant 01 --seed 42
python experiments/arrow_cue/run.py --participant 02             # equivalent shortcut
```
Esc aborts (data so far are kept). Options: `--test`, `--participant`, `--seed`, `--config file.json|.py`, `--check`.

## Before real data collection (testing and calibration)
```
python run_experiment.py <exp> --check display     # real window size, measured frame rate, pixels/degree, reference square
python run_experiment.py <exp> --check timing      # requested vs measured durations (flip timestamps), dropped frames
python run_experiment.py <exp> --check keyboard    # key names and RTs of your response keys
python run_experiment.py <exp> --check preview     # each stimulus on screen
python run_experiment.py <exp> --check all
```
Test runs (`--test`) save to `data/test/`, real runs to `data/<experiment>/`: they never mix.
Always do `display` and `timing` on the actual lab computer, in fullscreen (set `screen.fullscreen: True` and
`screen.size` to the true resolution).

## How an experiment is described
```python
CONFIG = {
  "experiment": {"name": ..., "output_dir": "data", "seed": 42, "instructions": [...],
                 "description": "...", "column_descriptions": {"cue_type": "valid = ..."}},   # both go into the data README
  "screen":     {"size": [1280, 720], "bg_color": [128,128,128], "color_space": "rgb255", "units": "deg",
                 "width_cm": 53, "distance_cm": 57, "fullscreen": False},
  "keys":       {"responses": {"f": "left", "j": "right"}},
  "design":     {"factors": {...} | "conditions": [...], "n_repeats": 5, "n_blocks": 2, "derive": fn},
  "practice":   {"n_trials": 8, "feedback": True},
  "scoring":    {"answer_variable": "answer"},
  "stimuli":    {"gabor": {"type": "gabor", "sf": 3, "size": 4}, ...},
  "events":     [{"name": "target", "stimuli": ["fixation", "gabor"], "duration": 0.1}, ...],
}
```
Only list what you change; everything else uses `DEFAULTS` in `toolbox/config.py` (also the list of all options).
JSON files work too (`--config my.json`), except `derive` which is a Python function.
Typos in section or key names, out-of-range colours, unknown stimulus types and undefined stimulus names
are reported with a clear `CONFIG ERROR`.

**Key ideas**
- **Events** run in order each trial. `duration` is seconds (or `[min, max]` for jitter), converted to whole frames.
  The single event with `"response": True` measures RT from its first flip; it ends on keypress unless
  `"end_on_response": False`; its `duration` is the timeout (`None` = wait forever).
- **Trial variables** come from `design.factors` (full crossing) or `design.conditions` (explicit list with `n` counts,
  e.g. 80% valid cues), then `derive(trial, rng)` can add computed variables.
- **`"<stimulus>.<param>"` variables** override that stimulus parameter on that trial (e.g. `"gabor.contrast": 0.1`,
  `"target.pos": [5, 0]`, `"target.type": "square"`); `"<stimulus>.visible": False` hides it. This is how conditions
  reach the screen without code. Combine any number of stimuli in an event by listing them.
- **Colours** are interpreted in `screen.color_space` (`rgb255`: 0-255, `rgb`: -1..1, `rgb1`: 0-1) and passed
  consistently to every stimulus. Names (`"red"`) and hex strings also work.
- **Randomization**: `seed` makes trial order, jitter and random layouts reproducible. `n_repeats` is *per block*.
  `max_run` limits consecutive repeats of a variable.
- **Scoring**: correct if the response label equals `trial[answer_variable]`; `no_response_label` supports catch trials.

## Stimulus library
`gabor`, `bullseye`, `gap_circle` (ring cue, gap `left/right/up/down` or closed), `circle`, `square`, `rectangle`,
`polygon`, `triangle`, `diamond`, `line`, `arrow` (`left/right/up/down/both`), `text`, `search_array`
(target + distractors on a `grid`, `ring` or `random` layout). Parameters are the arguments of each function in
`toolbox/stimuli.py`. Gabor `sf` is in cycles per degree when `units` is `"deg"`; `ori` is clockwise degrees.

### Add a new stimulus (no change to existing code)
```python
from psychopy import visual
from toolbox.stimuli import register_stimulus

@register_stimulus("my_square")
def my_square(win, cs, rng, pos=(0, 0), size=1.0, color="white"):
    return visual.Rect(win, width=size, height=size, pos=pos, fillColor=color, colorSpace=cs)
```
Put it in `experiments/<name>/custom_stimuli.py` (auto-loaded by the launcher) or import it before running.
To combine several PsychoPy objects use `StimGroup([...])`.

## Create a new experiment
1. Make `experiments/my_task/config.py` (copy `template/generic_experiment.py`'s `CONFIG`, or another example) and
   copy a `run.py` from an example. 2. Edit the config. 3. `--check` and `--test`. 4. Run.
Step-by-step: `tutorials/01_build_from_scratch.md`. A paper-to-code walk-through: `tutorials/02_from_paper_to_code.md`.
Need custom trial logic? Add `experiments/my_task/task.py` with `class Task(Experiment)` overriding `prepare_trial` / `score_trial`.

## Data
Every run creates **three files** in the same folder (`data/<experiment>/`, or `data/test/` for `--test` runs):

| File | Content |
|---|---|
| `<experiment>_sub-<ID>_ses-<n>_<date-time>.csv` | The data: one row per trial. Written after every trial, never overwritten. |
| `..._README.txt` | **Explains every column of that CSV in plain words**, lists the response keys and the events of a trial, and gives a quick analysis recipe. Generated automatically. |
| `..._<date-time>.json` | Settings used, seed, participant info, PsychoPy/Python versions, measured frame rate and run status (`completed`/`aborted`/`crashed`). |

Read the `_README.txt` first. It lists the columns that really exist in your file. For columns that come from
your own experiment (conditions such as `cue_type`), the explanation is the one you wrote in the config under
`experiment -> column_descriptions` (and `experiment -> description` for the task). Columns without a description
get a generic explanation (for example `gabor.contrast` = "value of the parameter 'contrast' of the stimulus 'gabor'").

Main columns: `participant, session, test_mode, block, trial, practice, seed`, your conditions, `response_key, response,
rt` (seconds, from the onset of the response event), `correct, timed_out`, `planned_<event>_ms` / `measured_<event>_ms`
(whole milliseconds, so Excel can never turn a duration such as 1.5 into a date), `dropped_frames, onset_time`. Practice trials have `practice = 1`.
Careful with Excel: on French/European settings, double-clicking a CSV can show one big column, and re-saving
from Excel rewrites it with `;` separators. Use Data > From Text/CSV (delimiter: comma) and keep the original file untouched. Once a cell has been turned into a date by Excel
the original value is lost: always reopen the original CSV.

## Timing and reliability notes
- Stimuli are drawn frame by frame; durations are whole frames (50 ms at 60 Hz = 3 frames). The actual refresh rate is measured at start.
- RT clock is reset on the flip that shows the response event, via PsychoPy's keyboard module (`psychopy.hardware.keyboard`).
- Stimuli are built *before* each trial, not during it. Very heavy trial-wise builds could still slow the gap between events, not the events.
- Verify with `--check timing` and the `measured_*_ms`/`dropped_frames` columns. Disable power saving, close other programs, use fullscreen.
- RT accuracy is bounded by the keyboard and the monitor (typically a few ms to ~20 ms); use response boxes if you need more.
