"""
experiment.py - THE ENGINE: runs any experiment described by a config.
=========================================================================
You do not need to edit this file to make a new experiment (edit config.py instead).
Read it if you want to understand what happens when an experiment runs.

THE IDEA
    An experiment = blocks of TRIALS.  A trial = a list of EVENTS (set in config["events"]).
    An event = "draw these stimuli for this long" (and, for ONE event per trial, "wait for a key").

WHAT HAPPENS WHEN YOU CALL  Experiment(config).run()
    1. ask for the participant ID                     -> get_participant_info()
    2. create the data file                           -> DataWriter (data.py)
    3. open the window                                -> setup_window()
    4. build the list of trials                       -> make_trials()  (uses trials.py)
    5. instructions -> practice -> blocks -> goodbye  -> run()
    6. for every trial:
         a. build the stimuli of this trial           -> build_trial_stimuli()
         b. run each event, frame by frame            -> run_event()
         c. score the answer and save one CSV row     -> run_trial()
    7. close everything, print a summary              -> _finish()

TIMING: durations are converted to whole screen frames (60 Hz -> 1 frame = 16.7 ms) because a screen
can only change at a refresh. The reaction time starts at the refresh that first shows the response event.

CUSTOM LOGIC (advanced): make a subclass and override prepare_trial() or score_trial().
"""
import platform
import sys
import time

import numpy as np
import psychopy
from psychopy import core, gui, monitors, visual
from psychopy.hardware import keyboard

from .config import ConfigError, load_config, pixels_per_degree, validate_config
from .data import DataWriter, summarize
from .stimuli import available_stimuli, build_stimulus
from .trials import flatten, make_blocks, make_practice

# Default text size for instruction screens, depending on the screen units.
TEXT_HEIGHT = {"deg": 1.0, "cm": 1.0, "pix": 28, "norm": 0.08, "height": 0.05}


class AbortExperiment(Exception):
    """Raised when the escape key is pressed. It stops the experiment cleanly (data are kept)."""


def _is_simple(value):
    """True for values that fit in one CSV cell. Stimulus specs (dictionaries) are not saved."""
    if isinstance(value, dict):
        return False
    if isinstance(value, (list, tuple)) and any(isinstance(v, dict) for v in value):
        return False
    return True


class Experiment:
    # ================================================================== 1. CREATION
    def __init__(self, config, test_mode=False, seed=None):
        """config: a dictionary, or the path of a .py/.json config file.
        test_mode: few trials, windowed, data saved in data/test.
        seed: any integer -> the same trial order every time."""
        self.cfg = load_config(config)                      # defaults + your config, merged
        if seed is not None:
            self.cfg["experiment"]["seed"] = int(seed)
        self.test_mode = test_mode
        if test_mode:
            if self.cfg["test_mode"]["windowed"]:
                self.cfg["screen"]["fullscreen"] = False
            self.cfg["practice"]["n_trials"] = self.cfg["test_mode"]["n_practice"]
        validate_config(self.cfg, known_types=available_stimuli())   # stops here if the config is wrong

        # The random generator: ALL randomness (trial order, jitter, layouts) comes from it.
        seed = self.cfg["experiment"]["seed"]
        self.seed = int(seed) if seed is not None else int(time.time() * 1000) % (2 ** 31)
        self.rng = np.random.default_rng(self.seed)

        self.win = None            # the PsychoPy window (created in setup_window)
        self.kb = None             # the keyboard (created in setup_window)
        self.writer = None         # the data file (created in run)
        self.info = {}             # participant info
        self.clock = core.Clock()  # experiment clock, used for time stamps
        self.fps = float(self.cfg["screen"]["frame_rate"])   # replaced by the measured value later
        self.trial_count = 0       # counts all trials run so far, practice included

    # ================================================================== 2. SETUP
    def get_participant_info(self, participant_id=None):
        """Ask for participant ID, session, age... (dialog box, or the terminal if no dialog is possible)."""
        settings = self.cfg["participant"]
        fields = dict(settings["fields"])
        if participant_id:
            fields["participant"] = str(participant_id)
        if self.test_mode and not fields.get("participant"):
            fields["participant"] = "test"

        must_ask = settings["ask"] and not (participant_id or self.test_mode)
        if must_ask and settings["use_dialog"]:
            try:
                dialog = gui.DlgFromDict(fields, title=self.cfg["experiment"]["name"], order=list(fields))
                if not dialog.OK:
                    raise AbortExperiment("Cancelled in the participant dialog")
            except AbortExperiment:
                raise
            except Exception as err:                       # no dialog possible -> ask in the terminal
                print(f"(dialog unavailable: {err}); using the terminal")
                fields = self._ask_in_terminal(fields)
        elif must_ask:
            fields = self._ask_in_terminal(fields)

        if not str(fields.get("participant", "")).strip():
            raise ConfigError("Participant ID is empty")
        return fields

    @staticmethod
    def _ask_in_terminal(fields):
        for name, default in fields.items():
            answer = input(f"{name} [{default}]: ").strip()
            fields[name] = answer or default
        return fields

    def setup_window(self):
        """Open the window and the keyboard, and measure the real screen refresh rate."""
        s = self.cfg["screen"]
        # A 'monitor' tells PsychoPy the screen size and viewing distance: this is what makes 'deg' work.
        monitor = monitors.Monitor("psychopygeneric")
        monitor.setWidth(s["width_cm"])
        monitor.setDistance(s["distance_cm"])
        monitor.setSizePix(s["size"])

        self.win = visual.Window(size=s["size"], fullscr=s["fullscreen"], screen=s["screen_index"],
                                 color=s["bg_color"], colorSpace=s["color_space"], units=s["units"],
                                 monitor=monitor, allowGUI=not s["hide_mouse"])
        self.win.mouseVisible = not s["hide_mouse"]

        if s["measure_frame_rate"]:
            rate = self.win.getActualFrameRate(nIdentical=10, nMaxFrames=100, nWarmUpFrames=10, threshold=1)
            if rate:
                self.fps = float(rate)
            else:
                print(f"WARNING: could not measure the frame rate; using {self.fps} Hz from the config")

        self.win.recordFrameIntervals = True      # lets PsychoPy count dropped frames
        self.kb = keyboard.Keyboard()
        return self.win

    def _stamp(self, state, reset_keyboard_clock=False):
        """Called by PsychoPy at the exact moment the screen refreshes (see callOnFlip below).
        It saves the time, and optionally restarts the reaction-time clock: this is what makes
        RT start exactly when the stimulus appears."""
        state["time"] = self.clock.getTime()
        if reset_keyboard_clock:
            self.kb.clock.reset()

    # ================================================================== 3. TEXT SCREENS
    def _make_text(self, message):
        s = self.cfg["screen"]
        width_px = s["size"][0]
        # Maximum text width in the current units (80% of the screen)
        wrap = {"pix": 0.8 * width_px,
                "deg": 0.8 * width_px / pixels_per_degree(self.cfg),
                "cm": 0.8 * s["width_cm"],
                "norm": 1.6,
                "height": 0.8 * width_px / s["size"][1]}[s["units"]]
        height = s["text_height"] or TEXT_HEIGHT[s["units"]]
        return visual.TextStim(self.win, text=message, color=s["text_color"], height=height, wrapWidth=wrap)

    def show_text(self, message, wait_keys=("space",)):
        """Show a message and wait until one of `wait_keys` is pressed (escape aborts)."""
        text = self._make_text(message)
        escape = self.cfg["keys"]["escape"]
        text.draw()
        self.win.flip()
        self.kb.clearEvents()
        pressed = self.kb.waitKeys(keyList=list(wait_keys) + [escape], waitRelease=False)
        if pressed and pressed[0].name == escape:
            raise AbortExperiment("Escape pressed")

    def show_timed_text(self, message, seconds):
        """Show a message for a fixed time (used for the practice feedback)."""
        text = self._make_text(message)
        for _ in range(max(1, int(round(seconds * self.fps)))):
            text.draw()
            self.win.flip()

    # ================================================================== 4. TRIAL LIST
    def make_trials(self):
        """Returns (blocks, practice_trials). Each trial is a dictionary of variables."""
        design = self.cfg["design"]
        blocks = make_blocks(design, self.rng)
        practice = make_practice(design, int(self.cfg["practice"]["n_trials"]), self.rng)

        if self.test_mode:       # keep only a few randomly chosen trials
            all_trials = flatten(blocks)
            n = min(int(self.cfg["test_mode"]["n_trials"]), len(all_trials))
            chosen = self.rng.permutation(len(all_trials))[:n]
            blocks = [[all_trials[i] for i in chosen]]

        # Safety check: the variable holding the correct answer must exist.
        answer_var = self.cfg["scoring"]["answer_variable"]
        first = (flatten(blocks) or [{}])[0]
        if answer_var and answer_var not in first:
            raise ConfigError(f"scoring.answer_variable '{answer_var}' is not a trial variable "
                              f"(available: {sorted(first)}). Create it in design.derive.")
        return blocks, practice

    # ---- hooks: override these in a subclass for custom behaviour (advanced) ----
    def prepare_trial(self, trial):
        """Last chance to change the trial before it runs. Must return the trial."""
        return trial

    def score_trial(self, trial, response_label):
        """1 if correct, 0 if wrong, None if the experiment has no correct answer."""
        answer_var = self.cfg["scoring"]["answer_variable"]
        if not answer_var:
            return None
        return int(response_label == trial[answer_var])

    # ================================================================== 5. STIMULI OF ONE TRIAL
    def build_trial_stimuli(self, trial):
        """Create the stimuli this trial needs. Returns (stimuli, extra_info).

        Start from the stimulus definition in config["stimuli"], then apply the trial's overrides:
        a trial variable called "gabor.contrast" changes the 'contrast' parameter of stimulus "gabor".
        "gabor.visible" = False means: do not show it on this trial.
        (We go through config["stimuli"] in order so seeded runs are exactly reproducible.)"""
        used = {name for event in self.cfg["events"] for name in event.get("stimuli", [])}
        stimuli, extra_info = {}, {}
        for name, definition in self.cfg["stimuli"].items():
            if name not in used:
                continue
            spec = dict(definition)
            for variable, value in trial.items():
                if variable.startswith(name + "."):
                    spec[variable[len(name) + 1:]] = value     # "gabor.contrast" -> contrast
            if spec.pop("visible", True) is False:
                continue
            stimulus = build_stimulus(self.win, spec, self.cfg["screen"]["color_space"], self.rng)
            stimuli[name] = stimulus
            for key, value in getattr(stimulus, "info", {}).items():   # e.g. target position of a search array
                extra_info[f"{name}_{key}"] = value
        return stimuli, extra_info

    # ================================================================== 6. ONE EVENT
    def run_event(self, event, stimuli):
        """Show one event frame by frame. If the event collects a response, record the first key press.
        Returns {"time": screen time of first frame, "planned": planned duration (s), "response": (key, rt) or None}."""
        # --- how long? (a [min, max] pair means a random duration in that range)
        duration = event.get("duration")
        if isinstance(duration, (list, tuple)):
            duration = float(self.rng.uniform(duration[0], duration[1]))
        n_frames = None if duration is None else max(1, int(round(duration * self.fps)))

        collects_response = bool(event.get("response"))
        allowed_keys = list(self.cfg["keys"]["responses"]) if collects_response else []
        escape = self.cfg["keys"]["escape"]
        to_draw = [stimuli[name] for name in event.get("stimuli", []) if name in stimuli]

        stamp, response, frame = {}, None, 0
        self.kb.clearEvents()                                   # forget old key presses
        # "On the next screen refresh: save the time, and restart the RT clock."
        self.win.callOnFlip(self._stamp, stamp, collects_response)

        while True:
            for stimulus in to_draw:
                stimulus.draw()                                 # draw into the hidden buffer...
            self.win.flip()                                     # ...and show it at the next refresh
            frame += 1

            for key in self.kb.getKeys(keyList=allowed_keys + [escape], waitRelease=False, clear=True):
                if key.name == escape:
                    raise AbortExperiment("Escape pressed")
                if collects_response and response is None:      # only the FIRST key counts
                    response = (key.name, float(key.rt))

            if response and event.get("end_on_response", True):
                break                                           # key pressed -> event over
            if n_frames is not None and frame >= n_frames:
                break                                           # time is up

        planned = None if n_frames is None else n_frames / self.fps
        return {"time": stamp["time"], "planned": planned, "response": response}

    # ================================================================== 7. ONE TRIAL
    def run_trial(self, trial, block, is_practice):
        """Run all events of one trial, score it, save one row in the CSV. Returns the row."""
        trial = self.prepare_trial(dict(trial))
        stimuli, extra_info = self.build_trial_stimuli(trial)
        self.trial_count += 1
        dropped_before = getattr(self.win, "nDroppedFrames", 0)

        results = [(event["name"], self.run_event(event, stimuli)) for event in self.cfg["events"]]

        end = {}                                                # one more flip: marks the end of the last event
        self.win.callOnFlip(self._stamp, end)
        self.win.flip()

        row = self._make_row(trial, extra_info, results, end["time"], block, is_practice,
                             dropped=getattr(self.win, "nDroppedFrames", 0) - dropped_before)
        self.writer.write_row(row)

        if is_practice and self.cfg["practice"]["feedback"] and row["correct"] is not None:
            message = "Correct!" if row["correct"] else ("Too slow!" if row["timed_out"] else "Wrong")
            self.show_timed_text(message, self.cfg["practice"]["feedback_duration"])
        return row

    def _make_row(self, trial, extra_info, results, end_time, block, is_practice, dropped):
        """Collect everything we know about the trial into one dictionary = one CSV row."""
        row = {"experiment": self.cfg["experiment"]["name"],
               "participant": self.info["participant"],
               "session": self.info.get("session", ""),
               "test_mode": int(self.test_mode),
               "block": block,
               "trial": self.trial_count,
               "practice": int(is_practice),
               "seed": self.seed}
        row.update({k: v for k, v in trial.items() if _is_simple(v)})   # the trial's conditions
        row.update(extra_info)

        # --- the response
        response = next((r["response"] for _, r in results if r["response"]), None)   # (key, rt) or None
        if response:
            label = self.cfg["keys"]["responses"][response[0]]            # key -> meaning
        else:
            label = self.cfg["scoring"]["no_response_label"]
        has_response_event = any(e.get("response") for e in self.cfg["events"])
        row.update({"response_key": response[0] if response else None,
                    "response": label,
                    "rt": round(response[1], 5) if response else None,
                    "correct": self.score_trial(trial, label),
                    "timed_out": int(has_response_event and response is None)})

        # --- timing: measured duration of an event = start of the next event minus its own start
        starts = [r["time"] for _, r in results] + [end_time]
        for i, (name, r) in enumerate(results):
            # Whole milliseconds on purpose: a value such as 1.5 (seconds) is read by Excel with French/European
            # settings as the date "1 May". An integer like 1500 can never be mistaken for a date.
            row[f"planned_{name}_ms"] = None if r["planned"] is None else int(round(r["planned"] * 1000))
            row[f"measured_{name}_ms"] = int(round((starts[i + 1] - starts[i]) * 1000))
        row["dropped_frames"] = dropped
        row["onset_time"] = round(starts[0], 4)
        return row

    # ================================================================== 8. THE WHOLE EXPERIMENT
    def _readme_info(self):
        """What the data writer needs to explain the CSV columns (see data.py)."""
        e = self.cfg["experiment"]
        return {"events": self.cfg["events"],
                "stimuli": list(self.cfg["stimuli"]),
                "responses": self.cfg["keys"]["responses"],
                "answer_variable": self.cfg["scoring"]["answer_variable"],
                "no_response_label": self.cfg["scoring"]["no_response_label"],
                "units": self.cfg["screen"]["units"],
                "descriptions": e["column_descriptions"],
                "experiment_description": e["description"]}

    def run(self, participant_id=None):
        """Run the complete experiment. Returns the path of the CSV file."""
        self.info = self.get_participant_info(participant_id)
        e = self.cfg["experiment"]
        self.writer = DataWriter(e["output_dir"], e["name"], self.info["participant"],
                                 self.info.get("session", "1"), self.test_mode, self._readme_info())
        self.status = "completed"
        started = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.setup_window()
            blocks, practice = self.make_trials()

            for page in e["instructions"]:
                self.show_text(page)

            if practice:
                self.show_text(self.cfg["practice"]["message"])
                for trial in practice:
                    self.run_trial(trial, block=0, is_practice=True)
                self.show_text(self.cfg["practice"]["main_message"])

            for block_number, trials in enumerate(blocks, start=1):
                for trial in trials:
                    self.run_trial(trial, block_number, is_practice=False)
                if block_number < len(blocks):
                    self.show_text(e["break_message"])

            self.show_text(e["end_message"])
        except AbortExperiment as err:
            self.status = "aborted"
            print(f"Experiment aborted: {err}")
        except Exception:
            self.status = "crashed"
            raise                                           # show the error, but still save everything (finally)
        finally:
            self._finish(started)
        return self.writer.path

    def _finish(self, started):
        """Always runs at the end (even after Esc or an error): save metadata, close, print summary."""
        metadata = {"status": self.status, "started": started,
                    "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "participant": self.info, "test_mode": self.test_mode, "seed": self.seed,
                    "trials_run": self.trial_count, "measured_frame_rate_hz": self.fps,
                    "psychopy_version": psychopy.__version__, "python": sys.version.split()[0],
                    "platform": platform.platform(), "config": self.cfg}
        self.writer.write_metadata(metadata)
        if self.win is not None:
            self.win.close()
        print(f"\nData saved to: {self.writer.path}")
        print(f"Column explanations: {self.writer.readme_path}")
        if self.writer.rows:
            summarize(self.writer.path, self.cfg["design"]["summary_by"])
