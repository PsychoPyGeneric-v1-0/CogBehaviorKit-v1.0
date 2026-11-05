"""
data.py - saving the data, and explaining it.
=============================================
For every run, THREE files are created in the same folder (same name, different ending):

    arrow_cue_sub-01_ses-1_20261103-101500.csv         the data: one row per trial   <- open this in Excel
    arrow_cue_sub-01_ses-1_20261103-101500_README.txt  explains EVERY column of that CSV in plain words
    arrow_cue_sub-01_ses-1_20261103-101500.json        settings, seed, versions, run status (for the record)

Safety rules:
  * the CSV is written after every trial, so an aborted run keeps its data
  * a file is NEVER overwritten (a new name with the date and time is used each run)
  * test runs go to  <output_dir>/test/   and real runs to  <output_dir>/<experiment>/
This module does not need PsychoPy.
"""
import csv
import json
import re
import statistics
import textwrap
import time
from collections import defaultdict
from pathlib import Path

# Relative output folders (like "data") are created inside the project folder, wherever you start from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# =====================================================================================
#  EXPLANATIONS OF THE COLUMNS  (used to write the _README.txt)
# =====================================================================================
GENERAL_COLUMNS = {
    "experiment": "Name of the experiment.",
    "participant": "Participant ID you typed at the start.",
    "session": "Session number you typed at the start.",
    "test_mode": "1 = test run (started with --test), 0 = real run.",
    "block": "Block number (1, 2, ...). Practice trials have block 0.",
    "trial": "Trial counter over the whole run, starting at 1. Practice trials are counted too.",
    "practice": "1 = practice trial, 0 = real trial. REMOVE the practice trials (practice = 1) before analysing.",
    "seed": "Random seed of the run. Running again with the same seed gives the same trial order.",
}
RESPONSE_COLUMNS = {
    "response_key": "The keyboard key the participant pressed first. Empty = no key pressed.",
    "response": "What that key MEANS in this experiment (see the key list above). If no key was pressed, "
                "this is the 'no response' label if one is defined, otherwise empty.",
    "rt": "Reaction time in SECONDS (0.45 = 450 ms), measured from the first screen refresh of the "
          "response event. Empty = no key pressed.",
    "correct": "1 = correct, 0 = wrong. Empty = the experiment has no correct answer to compare with.",
    "timed_out": "1 = no key was pressed before the response time ran out, 0 = a key was pressed.",
}
OTHER_COLUMNS = {
    "dropped_frames": "Number of screen refreshes that came late during this trial. A value around 1 per trial "
                      "is common (probably a late first frame while the trial's stimuli are prepared). What "
                      "matters is that the 'measured_' durations of your important events match the 'planned_' "
                      "ones. Many dropped frames in the middle of trials would mean a timing problem.",
    "onset_time": "Time (seconds since the experiment started) when the first screen of this trial appeared.",
}
# Extra information some stimuli save (column name = <stimulus name>_<key>)
STIMULUS_INFO = {
    "n_items": "number of items shown in the search array",
    "target_present": "True = the search array contained the target",
    "target_pos": "[x, y] position of the target in the search array (empty if no target)",
}
KNOWN_COLUMNS = set(GENERAL_COLUMNS) | set(RESPONSE_COLUMNS) | set(OTHER_COLUMNS)


def _wrap(name, text, name_width=26, total_width=100):
    """Format one 'column name   explanation' entry with the explanation wrapped and aligned."""
    lines = textwrap.wrap(text, width=total_width - name_width) or [""]
    out = [f"  {name:<{name_width - 2}}{lines[0]}"]
    out += [" " * name_width + line for line in lines[1:]]
    return "\n".join(out)


def _explain_variable(column, info):
    """Explain a column that comes from the experiment itself (conditions, overrides, stimulus info)."""
    user_text = info["descriptions"].get(column)
    if user_text:
        return user_text
    stimuli = info["stimuli"]
    if "." in column and column.split(".", 1)[0] in stimuli:
        stim, param = column.split(".", 1)
        if param == "visible":
            return f"True = stimulus '{stim}' was shown on this trial, False = it was hidden."
        return (f"Value of the parameter '{param}' of the stimulus '{stim}' on this trial "
                f"(it replaces the value written in the config).")
    for stim in stimuli:
        if column.startswith(stim + "_"):
            key = column[len(stim) + 1:]
            return f"Extra information saved by stimulus '{stim}': {STIMULUS_INFO.get(key, key)}."
    if column == info["answer_variable"]:
        return "The CORRECT response of this trial. 'correct' is 1 when 'response' equals this."
    return ("Experiment variable (no description given). You can add one in the config: "
            "experiment -> column_descriptions.")


def build_readme(columns, info, header):
    """Return the text of the _README.txt for a CSV that has these columns."""
    lines = []
    add = lines.append
    add("=" * 100)
    add("WHAT IS IN THE DATA FILE?")
    add("=" * 100)
    add(f"Experiment : {header['experiment']}")
    add(f"Participant: {header['participant']}   Session: {header['session']}   "
        f"Run type: {'TEST' if header['test_mode'] else 'real'}")
    add(f"Data file  : {header['csv_name']}")
    add(f"Written    : {time.strftime('%Y-%m-%d %H:%M:%S')}  (updated while the experiment runs)")
    if info["experiment_description"]:
        add("")
        add(textwrap.fill(info["experiment_description"], 100))

    add("")
    add("HOW TO OPEN THE CSV")
    add("  * One ROW = one TRIAL. One COLUMN = one measure (explained below). Empty cell = not applicable.")
    add("  * Excel: use Data > From Text/CSV and choose 'comma' as delimiter. Double-clicking can put everything")
    add("    in one column on computers set to French or other European settings (they expect ';').")
    add("  * If you open and re-save the CSV in Excel it may be rewritten with ';' separators and decimal commas.")
    add("    Keep the original file untouched and save your own copy as .xlsx.")
    add("  * 'rt' and 'onset_time' are in SECONDS; the planned_/measured_ timing columns are in MILLISECONDS. "
        "Positions/sizes are in the screen units of the experiment "
        f"('{info['units']}').")

    if info["responses"]:
        add("")
        add("RESPONSE KEYS  (key pressed -> meaning saved in the 'response' column)")
        for key, label in info["responses"].items():
            add(f"  key '{key}'  ->  '{label}'")
        if info["no_response_label"] is not None:
            add(f"  no key pressed  ->  '{info['no_response_label']}'")

    def section(title, names, explain):
        names = [c for c in columns if c in names]
        if names:
            add("")
            add(title)
            for c in names:
                add(_wrap(c, explain(c)))

    section("GENERAL COLUMNS", GENERAL_COLUMNS, GENERAL_COLUMNS.get)

    variables = [c for c in columns if c not in KNOWN_COLUMNS
                 and not c.startswith(("planned_", "measured_"))]
    section("EXPERIMENT VARIABLES  (the conditions of each trial, and what was shown)",
            variables, lambda c: _explain_variable(c, info))

    section("RESPONSE COLUMNS", RESPONSE_COLUMNS, RESPONSE_COLUMNS.get)

    timing = [c for c in columns if c.startswith(("planned_", "measured_"))]
    if timing:
        add("")
        add("TIMING COLUMNS  (one pair per event of the trial; times in whole MILLISECONDS)")
        add("  planned_<event>_ms  = the duration the program planned, rounded to whole screen frames.")
        add("  measured_<event>_ms = the duration it really lasted. It should match 'planned_' within about one frame")
        add("                        (16.7 ms at 60 Hz). A big difference = timing problem.")
        add("  (Milliseconds, not seconds, so that Excel can never turn 1.5 into a date such as '1 May'.)")
        add("  Events of a trial, in order:")
        for number, event in enumerate(info["events"], start=1):
            shows = ", ".join(event.get("stimuli", [])) or "blank screen"
            extra = ""
            if event.get("response"):
                extra = "  [response event: waits for a key; RT starts here; its measured time = until the key press]"
            add(f"    {number}. {event['name']:<12} shows: {shows}{extra}")
        for c in timing:
            kind, event_name = c.split("_", 1)
            event_name = event_name[:-3] if event_name.endswith("_ms") else event_name
            what = "planned duration" if kind == "planned" else "measured duration"
            add(_wrap(c, f"{what} of the event '{event_name}', in milliseconds."))

    section("OTHER COLUMNS", OTHER_COLUMNS, OTHER_COLUMNS.get)

    add("")
    add("QUICK ANALYSIS RECIPE")
    add("  1. Keep only real trials:                  practice = 0")
    add("  2. For reaction times keep only:           correct = 1  and  timed_out = 0")
    add("  3. Average 'rt' (seconds) for each level of your condition columns; compare accuracy ('correct')")
    add("     separately, to check that faster responses are not simply less accurate.")
    add("  4. Check 'planned_' vs 'measured_' timing and 'dropped_frames' to make sure the timing was good.")
    add("")
    return "\n".join(lines)


# =====================================================================================
#  WRITING THE DATA
# =====================================================================================
def _safe(text):
    """Make a string safe to use in a file name (letters, digits, - and _ only)."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", str(text).strip())


class DataWriter:
    """Creates the CSV (+ README + metadata) of ONE run and adds one row per trial."""

    def __init__(self, output_dir, experiment, participant, session, test_mode=False, readme_info=None):
        base = Path(output_dir)
        if not base.is_absolute():
            base = PROJECT_ROOT / base
        folder = base / ("test" if test_mode else _safe(experiment))
        folder.mkdir(parents=True, exist_ok=True)

        name = f"{_safe(experiment)}_sub-{_safe(participant)}_ses-{_safe(session)}"
        if not test_mode and list(folder.glob(name + "_*.csv")):
            print(f"WARNING: data already exist for {name}. A NEW file is created; nothing is overwritten.")
        name += "_" + time.strftime("%Y%m%d-%H%M%S")

        path, counter = folder / (name + ".csv"), 0
        while path.exists():                          # same second twice? add a number
            counter += 1
            path = folder / f"{name}_{counter}.csv"
        path.touch(exist_ok=False)

        self.path = path
        self.meta_path = path.with_suffix(".json")
        self.readme_path = path.with_name(path.stem + "_README.txt")
        self.rows = []              # every row written so far (kept in memory too)
        self.columns = []           # column names, in order
        self.header = {"experiment": experiment, "participant": participant, "session": session,
                       "test_mode": test_mode, "csv_name": path.name}
        self.readme_info = readme_info or {"events": [], "stimuli": [], "responses": {}, "answer_variable": None,
                                           "no_response_label": None, "units": "", "descriptions": {},
                                           "experiment_description": ""}

    def write_row(self, row):
        """Add one trial. If a never-seen column appears, the file is rewritten once with the new header."""
        self.rows.append(row)
        new_columns = [c for c in row if c not in self.columns]
        if new_columns:
            self.columns += new_columns
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
                writer.writerows(self.rows)
            self.write_readme()                       # columns changed -> refresh the explanation file
        else:
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self.columns).writerow(row)

    def write_readme(self):
        with open(self.readme_path, "w", encoding="utf-8") as f:
            f.write(build_readme(self.columns, self.readme_info, self.header))

    def write_metadata(self, metadata):
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)


# =====================================================================================
#  QUICK SUMMARY PRINTED AT THE END OF A RUN
# =====================================================================================
def _format(x):
    return "" if x is None else f"{x:.3f}"


def summarize(csv_path, by, print_table=True):
    """Accuracy and mean RT (correct trials only) for each level of the columns in `by`. Practice excluded."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("practice") == "0"]
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r.get(k, "") for k in by)].append(r)

    results = []
    for key in sorted(groups):
        trials = groups[key]
        correct = [r for r in trials if r.get("correct") == "1"]
        rts = [float(r["rt"]) for r in correct if r.get("rt")]
        results.append({**dict(zip(by, key)), "n": len(trials),
                        "accuracy": len(correct) / len(trials),
                        "mean_rt": statistics.mean(rts) if rts else None,
                        "sd_rt": statistics.stdev(rts) if len(rts) > 1 else None})
    if print_table:
        print("\nSummary (practice excluded; RT = correct trials only, in seconds)")
        for r in results:
            label = ", ".join(f"{k}={r[k]}" for k in by) or "all trials"
            print(f"  {label:45s} n={r['n']:4d}  accuracy={r['accuracy']:.2f}  "
                  f"RT={_format(r['mean_rt'])} (sd {_format(r['sd_rt'])})")
    return results
