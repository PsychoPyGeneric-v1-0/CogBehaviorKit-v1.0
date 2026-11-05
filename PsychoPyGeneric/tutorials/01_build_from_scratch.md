# Tutorial 1: build an experiment from scratch

Goal: a **simple RT task**. A fixation cross appears, then a coloured circle on the left or right.
Press **F** for a red circle and **J** for a green circle.

## Step 1: copy the template
```
cp template/generic_experiment.py experiments/colour_rt.py     # or make a folder experiments/colour_rt/config.py
```
Easiest for the launcher: create the folder `experiments/colour_rt/` containing a `config.py` that defines
`CONFIG` (copy the `CONFIG = {...}` part of the template; `run.py` can be copied from another example).

## Step 2: screen and colours
```python
"screen": {"size": [1280, 720], "bg_color": [128, 128, 128], "color_space": "rgb255", "units": "deg",
           "width_cm": 53, "distance_cm": 57},
```
`rgb255` means every colour is 0-255 (grey = 128). With `"rgb"` it would be -1..1 (grey = 0). The toolbox
checks that your numbers fit the chosen space and stops with a clear message otherwise.
Measure your own screen width and viewing distance: they define what a "degree" is.

## Step 3: stimuli
```python
"stimuli": {
    "fixation": {"type": "text", "text": "+", "height": 1.0},
    "dot":      {"type": "circle", "size": 1.5},
},
```
Available types: `python -c "from toolbox.stimuli import available_stimuli; print(available_stimuli())"`
(needs PsychoPy installed). Parameters are the keyword arguments in `toolbox/stimuli.py`.

## Step 4: design (conditions)
```python
"design": {"factors": {"colour": ["red", "green"], "side": ["left", "right"]},
           "n_repeats": 10, "n_blocks": 2, "derive": derive, "summary_by": ["colour"]},
```
This crosses colour x side (4 conditions) x 10 repeats = 40 trials per block, shuffled.
Use `"seed": 42` in `experiment` to get the same order every time.

## Step 5: link conditions to stimulus parameters
A trial variable named `"<stimulus>.<parameter>"` changes that parameter for that trial. Compute them in `derive`:
```python
COLOURS = {"red": [230, 40, 40], "green": [40, 170, 60]}
def derive(trial, rng):
    return {"dot.fill_color": COLOURS[trial["colour"]],
            "dot.pos": [-5 if trial["side"] == "left" else 5, 0],
            "answer": trial["colour"]}
```
`"dot.visible": False` hides a stimulus on a trial (useful for catch trials).

## Step 6: keys, scoring, events
```python
"keys": {"responses": {"f": "red", "j": "green"}},      # key -> label
"scoring": {"answer_variable": "answer"},               # correct if label == trial["answer"]
"events": [
    {"name": "fixation", "stimuli": ["fixation"], "duration": [0.5, 1.0]},        # jittered
    {"name": "target",   "stimuli": ["fixation", "dot"], "duration": 2.0, "response": True},
    {"name": "iti",      "stimuli": [], "duration": 0.5},
],
```
Durations are in seconds and are rounded to whole screen frames. The event with `"response": True` measures RT
from its first screen refresh and ends at the keypress (or after `duration`, which then acts as a timeout).

## Step 7: check, test, run
```
python run_experiment.py colour_rt --check display      # resolution, frame rate, pixels/degree
python run_experiment.py colour_rt --check timing       # requested vs measured durations
python run_experiment.py colour_rt --check keyboard
python run_experiment.py colour_rt --check preview      # look at each stimulus
python run_experiment.py colour_rt --test               # 6 trials, data in data/test/
python run_experiment.py colour_rt --participant 01     # real run
```
Press **Esc** at any time to abort; data recorded so far are kept.

## Step 8: add a stimulus of your own
Create `experiments/colour_rt/custom_stimuli.py` (loaded automatically by the launcher):
```python
from psychopy import visual
from toolbox.stimuli import register_stimulus

@register_stimulus("cross")
def cross(win, cs, rng, pos=(0, 0), size=1.0, color="white", line_width=3):
    return visual.ShapeStim(win, vertices=[(-size/2, 0), (size/2, 0), (0, 0), (0, size/2), (0, -size/2)],
                            closeShape=False, pos=pos, lineColor=color, lineWidth=line_width, colorSpace=cs)
```
Then use `{"type": "cross", "size": 1.2}` in `stimuli`. Nothing else changes.

## Step 9: look at the data
Every run saves three files: the CSV, a `_README.txt` that explains every column of that CSV in plain words
(read it first!), and a `.json` with the settings. To get explanations of YOUR columns in that README, fill
`experiment -> column_descriptions` in your config.
Open the CSV (Excel, R, pandas). Key columns: `rt` (seconds), `response`, `correct`, `timed_out`, your trial variables,
`planned_<event>_ms` vs `measured_<event>_ms` durations (milliseconds), `dropped_frames`. A summary prints at the end of each run.

## Beyond the config: custom logic
Subclass `Experiment` in `experiments/colour_rt/task.py` (class name `Task`) and override `prepare_trial` or
`score_trial`. The launcher uses it automatically.
